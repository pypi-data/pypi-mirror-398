import redis
import json
import time
import uuid
from urllib.parse import urlparse
from .state import atomic_bind, atomic_transition
from .policy import generate_space_name
from .account import select_account, mark_account_used
from .hf import create_space, deploy_worker, delete_space
class Scheduler:
    def __init__(self, redis_url):
        p = urlparse(redis_url)
        db = int(p.path.lstrip('/')) if p.path else 0
        self.redis = redis.Redis(
            host=p.hostname, port=p.port or 6379,
            password=p.password, db=db, decode_responses=True,
            socket_connect_timeout=10, socket_timeout=30
        )
        self.redis_url = redis_url
    def _get_system_config(self):
        data = self.redis.get('hfs:system:config')
        return json.loads(data) if data else {}
    def get_node(self, project_id, node_id):
        data = self.redis.get(f'hfs:node:{project_id}:{node_id}')
        return json.loads(data) if data else None
    def get_space(self, space_id):
        data = self.redis.get(f'hfs:space:{space_id}')
        return json.loads(data) if data else None
    def _get_node_last_account(self, project_id, node_id):
        node = self.get_node(project_id, node_id)
        if not node:
            return None
        space_id = node.get('space')
        if not space_id:
            return None
        return space_id.split('/')[0] if '/' in space_id else None
    def _log_account_status(self, project_id):
        print(f"[Scheduler] === Account Status for {project_id} ===", flush=True)
        space_counts = {}
        for skey in self.redis.scan_iter('hfs:space:*', count=500):
            sdata = self.redis.get(skey)
            if sdata:
                s = json.loads(sdata)
                space_id = s.get('id', '')
                if '/' in space_id:
                    username = space_id.split('/')[0]
                    space_counts[username] = space_counts.get(username, 0) + 1
        for key in self.redis.scan_iter('hfs:account:*', count=100):
            if ':stats' in key:
                continue
            data = self.redis.get(key)
            if data:
                acc = json.loads(data)
                username = acc.get('username', key.split(':')[-1])
                status = acc.get('status', 'unknown')
                max_spaces = acc.get('max_spaces', 5)
                space_count = space_counts.get(username, 0)
                reason = ""
                if status == 'banned':
                    reason = "BANNED"
                elif status == 'cooldown':
                    cooldown_until = acc.get('cooldown_until', 0)
                    if cooldown_until > time.time():
                        reason = f"COOLDOWN (until {time.strftime('%H:%M', time.localtime(cooldown_until))})"
                    else:
                        reason = "cooldown expired"
                elif space_count >= max_spaces:
                    reason = f"FULL ({space_count}/{max_spaces})"
                else:
                    reason = f"OK ({space_count}/{max_spaces})"
                print(f"[Scheduler]   {username}: {reason}", flush=True)
        print(f"[Scheduler] ================================", flush=True)
    def find_reusable_space(self, project_id, exclude_account=None, urgent=False):
        from .policy import get_project_config
        proj_data = self.redis.get(f'hfs:project:{project_id}')
        reuse_interval = 300
        if proj_data:
            proj = json.loads(proj_data)
            config = get_project_config(proj)
            reuse_interval = config.get('reuse_interval', config.get('run_timeout', 300))
        now = int(time.time())
        candidates = []
        for key in self.redis.scan_iter('hfs:space:*'):
            data = self.redis.get(key)
            if not data:
                continue
            space = json.loads(data)
            space_project = space.get('project_id')
            if space_project and space_project != project_id:
                continue
            status = space.get('status')
            if status not in ('exited', 'idle', 'failed'):
                continue
            updated_at = space.get('updated_at')
            if updated_at is None:
                updated_at = 0
            if not urgent and now - updated_at < reuse_interval:
                continue
            space_id = space.get('id')
            username = space_id.split('/')[0] if '/' in space_id else None
            if username:
                acc_data = self.redis.get(f'hfs:account:{username}')
                if acc_data:
                    acc = json.loads(acc_data)
                    if acc.get('status') == 'banned':
                        continue
            if exclude_account and username == exclude_account:
                continue
            priority = 0
            if status == 'idle':
                priority += 100
            elif status == 'exited':
                priority += 50
            elif status == 'failed':
                priority += 20
            if exclude_account and username != exclude_account:
                priority += 30
            priority += min(30, (now - updated_at) // 60)
            candidates.append({
                'space_id': space_id,
                'username': username,
                'priority': priority,
                'space': space
            })
        if not candidates:
            return None
        candidates.sort(key=lambda x: -x['priority'])
        from .hf import get_space_status
        for c in candidates:
            space_id = c['space_id']
            username = c['username']
            if username:
                acc_data = self.redis.get(f'hfs:account:{username}')
                if acc_data:
                    acc = json.loads(acc_data)
                    hf_status = get_space_status(space_id, acc.get('token'))
                    if hf_status:
                        return space_id
                    else:
                        c['space']['status'] = 'unusable'
                        self.redis.set(f'hfs:space:{space_id}', json.dumps(c['space']))
        return None
    def create_and_deploy_space(self, project_id, node_id, reuse=True, urgent=False):
        from .account import select_account, update_account_stats, mark_account_used
        from . import metrics
        space_id = None
        account = None
        from .policy import get_project_config
        proj_data = self.redis.get(f'hfs:project:{project_id}')
        config = get_project_config(json.loads(proj_data)) if proj_data else {}
        deploy_interval = config.get('deploy_interval', config.get('create_interval', 60))
        proj_stats_key = f'hfs:project:{project_id}:stats'
        proj_stats_data = self.redis.get(proj_stats_key)
        proj_stats = json.loads(proj_stats_data) if proj_stats_data else {}
        last_deployed = proj_stats.get('last_space_deployed', 0)
        if not urgent and time.time() - last_deployed < deploy_interval:
            wait = int(deploy_interval - (time.time() - last_deployed))
            print(f"[Scheduler] Deploy interval not reached, wait {wait}s", flush=True)
            return None, None
        last_account = None
        proj = json.loads(proj_data) if proj_data else {}
        if not proj.get('accounts'):
            last_account = self._get_node_last_account(project_id, node_id)
        if reuse:
            space_id = self.find_reusable_space(project_id, exclude_account=last_account, urgent=urgent)
            if space_id:
                print(f"[Scheduler] Reusing space: {space_id}", flush=True)
                from . import audit
                audit.log(self.redis, space_id, 'reuse_selected', 'scheduler',
                          project=project_id, node=node_id)
                metrics.inc(self.redis, 'space_reused', project=project_id)
                username = space_id.split('/')[0] if '/' in space_id else None
                if username:
                    acc_data = self.redis.get(f'hfs:account:{username}')
                    if acc_data:
                        account = json.loads(acc_data)
            else:
                print(f"[Scheduler] No reusable space for {project_id}", flush=True)
        if not space_id:
            from .policy import get_project_config
            proj_data = self.redis.get(f'hfs:project:{project_id}')
            config = get_project_config(json.loads(proj_data)) if proj_data else {}
            create_interval = config.get('create_interval', 300)
            proj_stats_key = f'hfs:project:{project_id}:stats'
            proj_stats_data = self.redis.get(proj_stats_key)
            proj_stats = json.loads(proj_stats_data) if proj_stats_data else {}
            last_created = proj_stats.get('last_space_created', 0)
            if not urgent and time.time() - last_created < create_interval:
                wait = int(create_interval - (time.time() - last_created))
                print(f"[Scheduler] Create interval not reached, wait {wait}s", flush=True)
                return None, None
            failed_accounts_data = proj_stats.get('failed_accounts', [])
            failed_accounts = set()
            if isinstance(failed_accounts_data, list):
                for item in failed_accounts_data:
                    if isinstance(item, str):
                        failed_accounts.add(item)
            elif isinstance(failed_accounts_data, dict):
                failed_account_ttl = config.get('failed_account_ttl', 86400)
                now = time.time()
                for account, timestamp in failed_accounts_data.items():
                    if isinstance(timestamp, (int, float)) and now - timestamp < failed_account_ttl:
                        failed_accounts.add(account)
                if len(failed_accounts) < len(failed_accounts_data):
                    proj_stats['failed_accounts'] = {k: v for k, v in failed_accounts_data.items() 
                                                     if isinstance(v, (int, float)) and now - v < failed_account_ttl}
                    self.redis.set(proj_stats_key, json.dumps(proj_stats))
            account = select_account(self.redis, project_id, exclude_accounts=failed_accounts)
            if not account:
                print(f"[Scheduler] ⚠️  NO AVAILABLE ACCOUNT for {project_id}", flush=True)
                self._log_account_status(project_id)
                return None, None
            username = account.get('username', account.get('id'))
            space_name = generate_space_name()
            result = create_space(space_name, account['token'])
            if result:
                space_id = result['id']
                print(f"[Scheduler] Created: {space_id}", flush=True)
                space_data = {
                    'id': space_id,
                    'project_id': project_id,
                    'node_id': node_id,
                    'status': 'starting',
                    'account': username,
                    'created_at': int(time.time()),
                    'updated_at': int(time.time()),
                    'started_at': int(time.time()),
                }
                self.redis.set(f'hfs:space:{space_id}', json.dumps(space_data))
                proj_stats['last_space_created'] = int(time.time())
                proj_stats['failed_accounts'] = {}
                self.redis.set(proj_stats_key, json.dumps(proj_stats))
                metrics.inc(self.redis, 'space_created', account=username, project=project_id)
                update_account_stats(self.redis, username, success=True)
            else:
                print(f"[Scheduler] Create failed for {username}", flush=True)
                metrics.inc(self.redis, 'space_failed', project=project_id, reason='create_failed')
                update_account_stats(self.redis, username, success=False)
                if isinstance(proj_stats.get('failed_accounts'), dict):
                    proj_stats['failed_accounts'][username] = int(time.time())
                else:
                    proj_stats['failed_accounts'] = {username: int(time.time())}
                proj_stats['last_space_created'] = int(time.time())
                self.redis.set(proj_stats_key, json.dumps(proj_stats))
                return None, None
        if space_id and node_id:
            from .state import atomic_bind
            import uuid
            instance_id = str(uuid.uuid4())[:8]
            ok, msg = atomic_bind(self.redis, project_id, node_id, space_id, instance_id)
            if ok:
                print(f"[Scheduler] Node {node_id} bound to {space_id}: {msg}", flush=True)
            else:
                print(f"[Scheduler] WARNING: Bind failed: {msg}", flush=True)
                return None, None
        from .hf import get_space_status, restart_space, wait_for_build, pause_space
        from . import audit
        proj_data = self.redis.get(f'hfs:project:{project_id}')
        project_config = json.loads(proj_data) if proj_data else {}
        force_deploy = project_config.get('force_deploy', True)
        need_deploy = True
        if reuse and space_id and not force_deploy:
            space_data = self.get_space(space_id)
            if space_data:
                old_project = space_data.get('project_id')
                old_node = space_data.get('node_id')
                if old_project == project_id and old_node == node_id:
                    print(f"[Scheduler] Space already has correct code (project={project_id}, node={node_id}), skip deploy", flush=True)
                    audit.log(self.redis, space_id, 'deploy_skipped', 'scheduler',
                              reason='same_project_node', project=project_id, node=node_id)
                    need_deploy = False
        if force_deploy and not need_deploy:
            print(f"[Scheduler] Force deploy enabled, deploying anyway", flush=True)
            need_deploy = True
        if need_deploy:
            if reuse:
                hf_status = get_space_status(space_id, account['token'])
                audit.log(self.redis, space_id, 'hf_status_check', 'scheduler', 
                          status=hf_status, reuse=True)
                if hf_status == 'RUNNING':
                    print(f"[Scheduler] Pausing space to stop old worker...", flush=True)
                    audit.log(self.redis, space_id, 'pause', 'scheduler', reason='stop_old_worker')
                    pause_space(space_id, account['token'])
                    time.sleep(3)
            audit.log(self.redis, space_id, 'deploy', 'scheduler', 
                      project=project_id, node=node_id, reuse=reuse)
            system_config = self._get_system_config()
            code_source = system_config.get('code_source')
            git_url = system_config.get('git_url')
            git_token = system_config.get('git_token')
            git_branch = system_config.get('git_branch')
            git_ref = system_config.get('git_ref')
            ok = deploy_worker(space_id, account['token'], self.redis_url, 
                              project_id=project_id, node_id=node_id,
                              code_source=code_source, git_url=git_url,
                              git_token=git_token, git_branch=git_branch, git_ref=git_ref)
            if not ok:
                print(f"[Scheduler] Deploy failed", flush=True)
                audit.log(self.redis, space_id, 'deploy_failed', 'scheduler')
                if reuse:
                    space = self.get_space(space_id)
                    if space:
                        space['status'] = 'failed'
                        self.redis.set(f'hfs:space:{space_id}', json.dumps(space))
                return None, None
            time.sleep(5)
            print(f"[Scheduler] Waiting for build...", flush=True)
            build_status = wait_for_build(space_id, account['token'], redis_client=self.redis)
            audit.log(self.redis, space_id, 'build_complete', 'scheduler', status=build_status)
            if not build_status:
                print(f"[Scheduler] Build failed", flush=True)
                return None, None
            need_factory_reboot = not reuse
            if build_status in ('PAUSED', 'SLEEPING', 'STOPPED'):
                need_factory_reboot = True
            elif build_status == 'RUNNING' and not reuse:
                need_factory_reboot = True
            if need_factory_reboot:
                print(f"[Scheduler] Space {build_status}, factory rebooting (new={not reuse})...", flush=True)
                audit.log(self.redis, space_id, 'restart', 'scheduler', 
                          reason=f'ensure_new_build', factory_reboot=True, reuse=reuse)
                ok = restart_space(space_id, account['token'], factory_reboot=True)
                print(f"[Scheduler] factory_reboot result: {ok}", flush=True)
        else:
            print(f"[Scheduler] Restarting space with existing code...", flush=True)
            audit.log(self.redis, space_id, 'restart', 'scheduler', 
                      reason='reuse_same_code', factory_reboot=False)
            restart_space(space_id, account['token'], factory_reboot=False)
        proj_stats['last_space_deployed'] = int(time.time())
        self.redis.set(proj_stats_key, json.dumps(proj_stats))
        mark_account_used(self.redis, account.get('username', account.get('id')))
        return space_id, account
    def wait_for_worker(self, space_id, timeout=120):
        print(f"[Scheduler] Waiting for worker heartbeat...")
        start = time.time()
        while time.time() - start < timeout:
            space = self.get_space(space_id)
            if space and space.get('status') == 'running':
                last_hb = space.get('last_heartbeat', 0)
                if time.time() - last_hb < 60:
                    print(f"[Scheduler] Worker running: {space.get('instance_id')}")
                    return True
            time.sleep(10)
        print(f"[Scheduler] Worker timeout after {timeout}s")
        return False
    def rotate_node(self, project_id, node_id):
        node = self.get_node(project_id, node_id)
        if not node:
            print(f"[Scheduler] Node not found: {node_id}")
            return None
        old_space_id = node.get('space')
        print(f"[Scheduler] Rotating {node_id}: {old_space_id} -> new")
        new_space_id, account = self.create_and_deploy_space(project_id, node_id)
        if not new_space_id:
            return None
        if not self.wait_for_worker(new_space_id):
            print(f"[Scheduler] New worker failed, cleaning up")
            if account:
                delete_space(new_space_id, account['token'])
            return None
        if old_space_id:
            print(f"[Scheduler] Draining old space: {old_space_id}")
            atomic_transition(self.redis, old_space_id, 'running', 'draining')
        node = self.get_node(project_id, node_id)
        if node and node.get('space') == new_space_id:
            print(f"[Scheduler] Rotation complete: {node_id} -> {new_space_id}")
            return new_space_id
        print(f"[Scheduler] Warning: Node not bound to new space")
        return new_space_id
    def allocate_node(self, project_id):
        for key in self.redis.scan_iter(f'hfs:node:{project_id}:*'):
            data = self.redis.get(key)
            if not data:
                continue
            node = json.loads(data)
            if node.get('status') == 'idle':
                node['status'] = 'pending'
                self.redis.set(key, json.dumps(node))
                return node['id']
        return None