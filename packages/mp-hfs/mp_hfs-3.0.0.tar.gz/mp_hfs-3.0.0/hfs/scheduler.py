"""Scheduler 核心逻辑（按 v2 设计文档）"""
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
        """获取系统级配置"""
        data = self.redis.get('hfs:system:config')
        return json.loads(data) if data else {}
    
    def get_node(self, project_id, node_id):
        """获取 Node 数据"""
        data = self.redis.get(f'hfs:node:{project_id}:{node_id}')
        return json.loads(data) if data else None
    
    def get_space(self, space_id):
        """获取 Space 数据"""
        data = self.redis.get(f'hfs:space:{space_id}')
        return json.loads(data) if data else None
    
    def _get_node_last_account(self, project_id, node_id):
        """获取 Node 上次使用的账号"""
        node = self.get_node(project_id, node_id)
        if not node:
            return None
        
        space_id = node.get('space')
        if not space_id:
            return None
        
        # 从 space_id 提取账号
        return space_id.split('/')[0] if '/' in space_id else None
    
    def _log_account_status(self, project_id):
        """输出账号状态告警"""
        print(f"[Scheduler] === Account Status for {project_id} ===", flush=True)
        
        # 先统计所有 Space（避免嵌套扫描）
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
                
                # 从预统计获取 Space 数量
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
        """查找可复用的 Space
        
        过滤条件：
        1. 必须是同项目的 Space
        2. 状态：exited/idle/failed
        3. 距离上次使用 > reuse_interval
        4. HF 端验证存在
        5. 排除指定账号的 Space（风控）
        
        优先级：
        1. exited > failed > idle
        2. 不同账号优先
        3. updated_at 越近越好
        """
        from .policy import get_project_config
        
        proj_data = self.redis.get(f'hfs:project:{project_id}')
        reuse_interval = 300
        if proj_data:
            proj = json.loads(proj_data)
            config = get_project_config(proj)
            # 默认用 run_timeout 作为休息期
            reuse_interval = config.get('reuse_interval', config.get('run_timeout', 300))
        
        now = int(time.time())
        candidates = []
        
        for key in self.redis.scan_iter('hfs:space:*'):
            data = self.redis.get(key)
            if not data:
                continue
            space = json.loads(data)
            
            # 允许复用：无 project_id 或同 project_id
            space_project = space.get('project_id')
            if space_project and space_project != project_id:
                continue
            
            status = space.get('status')
            if status not in ('exited', 'idle', 'failed'):
                continue
            
            # 检查 reuse_interval（urgent 模式跳过）
            updated_at = space.get('updated_at')
            if updated_at is None:
                updated_at = 0  # 没有时间戳，视为很久以前
            if not urgent and now - updated_at < reuse_interval:
                continue
            
            space_id = space.get('id')
            username = space_id.split('/')[0] if '/' in space_id else None
            
            # 跳过 banned 账号的 Space
            if username:
                acc_data = self.redis.get(f'hfs:account:{username}')
                if acc_data:
                    acc = json.loads(acc_data)
                    if acc.get('status') == 'banned':
                        continue
            
            # 排除指定账号（风控）
            if exclude_account and username == exclude_account:
                continue
            
            # 计算优先级分数: idle > exited > failed
            priority = 0
            if status == 'idle':
                priority += 100
            elif status == 'exited':
                priority += 50
            elif status == 'failed':
                priority += 20
            # 不同账号加分
            if exclude_account and username != exclude_account:
                priority += 30
            # 越近越好
            priority += min(30, (now - updated_at) // 60)  # 每分钟加1分，最多30
            
            candidates.append({
                'space_id': space_id,
                'username': username,
                'priority': priority,
                'space': space
            })
        
        if not candidates:
            return None
        
        # 按优先级排序
        candidates.sort(key=lambda x: -x['priority'])
        
        # 验证 HF 端存在
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
                        # HF 端不存在，标记 unusable
                        c['space']['status'] = 'unusable'
                        self.redis.set(f'hfs:space:{space_id}', json.dumps(c['space']))
        
        return None
    
    def create_and_deploy_space(self, project_id, node_id, reuse=True, urgent=False):
        """创建 Space 并部署 Worker
        
        Args:
            reuse: 是否尝试复用现有 Space
            urgent: 紧急模式（轮换），跳过 deploy_interval 检查
        
        Returns:
            (space_id, account) 或 (None, None)
        """
        from .account import select_account, update_account_stats, mark_account_used
        from . import metrics
        
        space_id = None
        account = None
        
        # 检查部署间隔（紧急模式跳过）
        from .policy import get_project_config
        proj_data = self.redis.get(f'hfs:project:{project_id}')
        config = get_project_config(json.loads(proj_data)) if proj_data else {}
        deploy_interval = config.get('deploy_interval', config.get('create_interval', 60))  # 默认 60 秒
        
        proj_stats_key = f'hfs:project:{project_id}:stats'
        proj_stats_data = self.redis.get(proj_stats_key)
        proj_stats = json.loads(proj_stats_data) if proj_stats_data else {}
        
        last_deployed = proj_stats.get('last_space_deployed', 0)
        if not urgent and time.time() - last_deployed < deploy_interval:
            wait = int(deploy_interval - (time.time() - last_deployed))
            print(f"[Scheduler] Deploy interval not reached, wait {wait}s", flush=True)
            return None, None
        
        # 获取 Node 上次使用的账号（用于风控排除）
        # 只有自动分配账号时才排除，项目指定账号不排除
        last_account = None
        proj = json.loads(proj_data) if proj_data else {}
        if not proj.get('accounts'):  # 自动分配账号
            last_account = self._get_node_last_account(project_id, node_id)
        
        # 1. 尝试复用
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
                # Space 状态和 Node 绑定由后面的 atomic_bind 统一处理
            else:
                print(f"[Scheduler] No reusable space for {project_id}", flush=True)
        
        # 2. 如果没有可复用的，创建新的
        if not space_id:
            # 检查创建间隔（可配置，默认 5 分钟）- 紧急模式跳过
            from .policy import get_project_config
            proj_data = self.redis.get(f'hfs:project:{project_id}')
            config = get_project_config(json.loads(proj_data)) if proj_data else {}
            create_interval = config.get('create_interval', 300)  # 默认 5 分钟
            
            proj_stats_key = f'hfs:project:{project_id}:stats'
            proj_stats_data = self.redis.get(proj_stats_key)
            proj_stats = json.loads(proj_stats_data) if proj_stats_data else {}
            
            last_created = proj_stats.get('last_space_created', 0)
            if not urgent and time.time() - last_created < create_interval:
                wait = int(create_interval - (time.time() - last_created))
                print(f"[Scheduler] Create interval not reached, wait {wait}s", flush=True)
                return None, None
            
            # 获取失败账号列表，支持过期机制
            failed_accounts_data = proj_stats.get('failed_accounts', [])
            
            # 兼容旧格式（list）和新格式（dict with timestamp）
            failed_accounts = set()
            if isinstance(failed_accounts_data, list):
                # 旧格式：直接使用
                for item in failed_accounts_data:
                    if isinstance(item, str):
                        failed_accounts.add(item)
            elif isinstance(failed_accounts_data, dict):
                # 新格式：检查过期时间（默认 24 小时）
                failed_account_ttl = config.get('failed_account_ttl', 86400)  # 24 小时
                now = time.time()
                for account, timestamp in failed_accounts_data.items():
                    if isinstance(timestamp, (int, float)) and now - timestamp < failed_account_ttl:
                        failed_accounts.add(account)
                
                # 如果有过期的，更新 Redis
                if len(failed_accounts) < len(failed_accounts_data):
                    proj_stats['failed_accounts'] = {k: v for k, v in failed_accounts_data.items() 
                                                     if isinstance(v, (int, float)) and now - v < failed_account_ttl}
                    self.redis.set(proj_stats_key, json.dumps(proj_stats))
            
            account = select_account(self.redis, project_id, exclude_accounts=failed_accounts)
            if not account:
                # 详细告警：账号资源不足
                print(f"[Scheduler] ⚠️  NO AVAILABLE ACCOUNT for {project_id}", flush=True)
                self._log_account_status(project_id)
                return None, None
            
            username = account.get('username', account.get('id'))
            space_name = generate_space_name()
            result = create_space(space_name, account['token'])
            
            if result:
                space_id = result['id']
                print(f"[Scheduler] Created: {space_id}", flush=True)
                
                # 立即写入 Redis
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
                
                # 更新项目统计
                proj_stats['last_space_created'] = int(time.time())
                proj_stats['failed_accounts'] = {}  # 清空失败账号（新格式）
                self.redis.set(proj_stats_key, json.dumps(proj_stats))
                
                metrics.inc(self.redis, 'space_created', account=username, project=project_id)
                update_account_stats(self.redis, username, success=True)
            else:
                print(f"[Scheduler] Create failed for {username}", flush=True)
                metrics.inc(self.redis, 'space_failed', project=project_id, reason='create_failed')
                update_account_stats(self.redis, username, success=False)
                
                # 记录失败账号（带时间戳），下次换账号
                if isinstance(proj_stats.get('failed_accounts'), dict):
                    # 新格式
                    proj_stats['failed_accounts'][username] = int(time.time())
                else:
                    # 转换为新格式
                    proj_stats['failed_accounts'] = {username: int(time.time())}
                
                proj_stats['last_space_created'] = int(time.time())  # 也更新时间，避免立即重试
                self.redis.set(proj_stats_key, json.dumps(proj_stats))
                return None, None
        
        # 3. 先绑定 Node（避免部署期间被重复创建）
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
        
        # 4. 检查是否需要重新部署代码
        from .hf import get_space_status, restart_space, wait_for_build, pause_space
        from . import audit
        
        # 获取项目配置，检查是否强制部署
        proj_data = self.redis.get(f'hfs:project:{project_id}')
        project_config = json.loads(proj_data) if proj_data else {}
        force_deploy = project_config.get('force_deploy', True)  # 默认强制部署
        
        need_deploy = True
        if reuse and space_id and not force_deploy:
            space_data = self.get_space(space_id)
            if space_data:
                old_project = space_data.get('project_id')
                old_node = space_data.get('node_id')
                
                # 如果 project_id 和 node_id 都匹配，不需要重新部署
                if old_project == project_id and old_node == node_id:
                    print(f"[Scheduler] Space already has correct code (project={project_id}, node={node_id}), skip deploy", flush=True)
                    audit.log(self.redis, space_id, 'deploy_skipped', 'scheduler',
                              reason='same_project_node', project=project_id, node=node_id)
                    need_deploy = False
        
        if force_deploy and not need_deploy:
            print(f"[Scheduler] Force deploy enabled, deploying anyway", flush=True)
            need_deploy = True
        
        if need_deploy:
            # 如果是复用，先暂停老 Space 确保老 Worker 停止
            if reuse:
                hf_status = get_space_status(space_id, account['token'])
                audit.log(self.redis, space_id, 'hf_status_check', 'scheduler', 
                          status=hf_status, reuse=True)
                if hf_status == 'RUNNING':
                    print(f"[Scheduler] Pausing space to stop old worker...", flush=True)
                    audit.log(self.redis, space_id, 'pause', 'scheduler', reason='stop_old_worker')
                    pause_space(space_id, account['token'])
                    time.sleep(3)  # 等待暂停生效
            
            audit.log(self.redis, space_id, 'deploy', 'scheduler', 
                      project=project_id, node=node_id, reuse=reuse)
            
            # 获取系统级代码来源配置
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
            
            # 5. 等待 HF 处理 git push，然后检查构建状态
            time.sleep(5)  # 等待 HF 同步 commit
            print(f"[Scheduler] Waiting for build...", flush=True)
            build_status = wait_for_build(space_id, account['token'], redis_client=self.redis)
            audit.log(self.redis, space_id, 'build_complete', 'scheduler', status=build_status)
            if not build_status:
                print(f"[Scheduler] Build failed", flush=True)
                return None, None
            
            # 构建完成后根据状态决定是否需要 factory_reboot
            # 新创建的 Space 必须 factory_reboot，因为 duplicate_space 可能用了缓存镜像
            need_factory_reboot = not reuse  # 新创建的 Space 强制 factory_reboot
            
            if build_status in ('PAUSED', 'SLEEPING', 'STOPPED'):
                need_factory_reboot = True
            elif build_status == 'RUNNING' and not reuse:
                # 新创建的 Space 即使 RUNNING 也要 factory_reboot
                # 因为 HF 可能用了模板的缓存镜像，没有真正 build 我们的代码
                need_factory_reboot = True
            
            if need_factory_reboot:
                print(f"[Scheduler] Space {build_status}, factory rebooting (new={not reuse})...", flush=True)
                audit.log(self.redis, space_id, 'restart', 'scheduler', 
                          reason=f'ensure_new_build', factory_reboot=True, reuse=reuse)
                ok = restart_space(space_id, account['token'], factory_reboot=True)
                print(f"[Scheduler] factory_reboot result: {ok}", flush=True)
        else:
            # 不需要重新部署，只需要重启（使用现有代码）
            print(f"[Scheduler] Restarting space with existing code...", flush=True)
            audit.log(self.redis, space_id, 'restart', 'scheduler', 
                      reason='reuse_same_code', factory_reboot=False)
            restart_space(space_id, account['token'], factory_reboot=False)
        
        # 6. 更新部署时间
        proj_stats['last_space_deployed'] = int(time.time())
        self.redis.set(proj_stats_key, json.dumps(proj_stats))
        
        # 7. 标记账号已使用
        mark_account_used(self.redis, account.get('username', account.get('id')))
        
        return space_id, account
    
    def wait_for_worker(self, space_id, timeout=120):
        """等待 Worker 发送心跳
        
        Returns:
            True if worker is running, False if timeout
        """
        print(f"[Scheduler] Waiting for worker heartbeat...")
        start = time.time()
        
        while time.time() - start < timeout:
            space = self.get_space(space_id)
            if space and space.get('status') == 'running':
                last_hb = space.get('last_heartbeat', 0)
                if time.time() - last_hb < 60:  # 心跳在 60s 内
                    print(f"[Scheduler] Worker running: {space.get('instance_id')}")
                    return True
            time.sleep(10)
        
        print(f"[Scheduler] Worker timeout after {timeout}s")
        return False
    
    def rotate_node(self, project_id, node_id):
        """轮换 Node
        
        流程：
        1. 创建新 Space 并部署 Worker
        2. 等待新 Worker 运行
        3. 旧 Space 设为 draining
        4. 更新 Node 指向新 Space
        
        Returns:
            new_space_id 或 None
        """
        node = self.get_node(project_id, node_id)
        if not node:
            print(f"[Scheduler] Node not found: {node_id}")
            return None
        
        old_space_id = node.get('space')
        print(f"[Scheduler] Rotating {node_id}: {old_space_id} -> new")
        
        # 1. 创建新 Space
        new_space_id, account = self.create_and_deploy_space(project_id, node_id)
        if not new_space_id:
            return None
        
        # 2. 等待新 Worker 运行
        if not self.wait_for_worker(new_space_id):
            print(f"[Scheduler] New worker failed, cleaning up")
            if account:
                delete_space(new_space_id, account['token'])
            return None
        
        # 3. 旧 Space 设为 draining
        if old_space_id:
            print(f"[Scheduler] Draining old space: {old_space_id}")
            atomic_transition(self.redis, old_space_id, 'running', 'draining')
        
        # 4. 更新 Node（通过 bind 完成）
        # Worker 启动时已经 bind 了，这里只需确认
        node = self.get_node(project_id, node_id)
        if node and node.get('space') == new_space_id:
            print(f"[Scheduler] Rotation complete: {node_id} -> {new_space_id}")
            return new_space_id
        
        print(f"[Scheduler] Warning: Node not bound to new space")
        return new_space_id
    
    def allocate_node(self, project_id):
        """分配空闲 Node"""
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
