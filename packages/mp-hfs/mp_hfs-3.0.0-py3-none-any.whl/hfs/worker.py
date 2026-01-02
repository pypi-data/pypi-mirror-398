"""Worker 核心逻辑（按 v2 设计文档）"""
import os
import signal
import subprocess
import time
import json
import uuid
import redis
import threading
import random
from urllib.parse import urlparse

from .state import atomic_bind, atomic_heartbeat, atomic_transition
from .policy import get_project_config, get_scene_config
from .diag import DiagLogger


class Worker:
    def __init__(self, redis_url, space_id, project_id=None, node_id=None, external=False, external_timeout=None):
        p = urlparse(redis_url)
        db = int(p.path.lstrip('/')) if p.path else 0
        self.redis = redis.Redis(
            host=p.hostname, port=p.port or 6379,
            password=p.password, db=db, decode_responses=True,
            socket_connect_timeout=10, socket_timeout=30
        )
        self.redis_url = redis_url
        self.space_id = space_id
        self.project_id = project_id
        self.node_id = node_id
        self.external = external
        self.instance_id = uuid.uuid4().hex[:8]
        
        # 诊断日志
        self.diag = DiagLogger(redis_url, 'worker', self.instance_id)
        
        # 读取配置
        self.config = self._load_config()
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        
        # 外部节点可自定义超时，不指定则永不超时
        if external:
            self.run_timeout = external_timeout  # None 表示永不超时
        else:
            from .policy import calc_run_timeout
            base_timeout = self.config.get('run_timeout', 3600)
            use_jitter = not self._is_project_specified_accounts()
            self.run_timeout = int(calc_run_timeout(base_timeout, use_jitter))
        
        self._process = None
        self._running = False
        self._should_exit = False
        self._heartbeat_count = 0
        self._started_at = None
        self._scheduler_thread = None
    
    def _is_project_specified_accounts(self):
        """检查项目是否指定了账号"""
        if not self.project_id:
            return False
        proj_data = self.redis.get(f'hfs:project:{self.project_id}')
        if proj_data:
            proj = json.loads(proj_data)
            return bool(proj.get('accounts'))
        return False
    
    def _find_available_node(self):
        """查找空闲节点（无 running Space 绑定）"""
        for key in self.redis.scan_iter(f'hfs:node:{self.project_id}:*'):
            node_data = self.redis.get(key)
            if not node_data:
                continue
            node = json.loads(node_data)
            node_id = node.get('id')
            space_id = node.get('space_id') or node.get('space')
            if not space_id:
                return node_id
            space_data = self.redis.get(f'hfs:space:{space_id}')
            if not space_data:
                return node_id
            space = json.loads(space_data)
            if space.get('status') not in ('running', 'starting'):
                return node_id
        return None
    
    def _find_pending_external(self):
        """查找 pending 状态的外部节点"""
        for key in self.redis.scan_iter('hfs:space:*'):
            data = self.redis.get(key)
            if not data:
                continue
            space = json.loads(data)
            if space.get('type') != 'external':
                continue
            if space.get('status') != 'pending':
                continue
            if space.get('project_id') != self.project_id:
                continue
            return space.get('id')
        return None
    
    def _bind_external_to_node(self, space_id, node_id):
        """将外部节点绑定到 Node"""
        now = int(time.time())
        space_key = f'hfs:space:{space_id}'
        space_data = self.redis.get(space_key)
        if space_data:
            space = json.loads(space_data)
            space['status'] = 'running'
            space['node_id'] = node_id
            space['started_at'] = now
            space['run_timeout'] = self.run_timeout  # 存储确定的超时值
            space['updated_at'] = now
            self.redis.set(space_key, json.dumps(space))
        
        # 更新 node 绑定
        self.redis.set(f'hfs:node:{self.project_id}:{node_id}', json.dumps({
            'id': node_id, 'space': space_id, 'space_id': space_id, 'status': 'running', 'updated_at': now
        }))
    
    def _load_config(self):
        """加载项目配置"""
        if not self.project_id:
            return get_scene_config('long_task')
        
        proj_data = self.redis.get(f'hfs:project:{self.project_id}')
        if not proj_data:
            return get_scene_config('long_task')
        
        project = json.loads(proj_data)
        return get_project_config(project)
    
    def _check_project_consistency(self):
        """检测 project_id 与 Redis 记录是否一致"""
        from . import audit
        
        space_data = self.redis.get(f'hfs:space:{self.space_id}')
        if not space_data:
            # Space 不存在，新创建的，一致
            return True
        
        space = json.loads(space_data)
        redis_project = space.get('project_id')
        
        if not redis_project:
            # Redis 没有记录 project，一致
            return True
        
        if redis_project == self.project_id:
            # 一致
            return True
        
        # 不一致，标记 failed 并退出
        print(f'[HFS] Project mismatch! Code: {self.project_id}, Redis: {redis_project}', flush=True)
        self.diag.error('project_mismatch', code_project=self.project_id, redis_project=redis_project)
        audit.log(self.redis, self.space_id, 'project_mismatch', f'worker/{self.instance_id}',
                  code_project=self.project_id, redis_project=redis_project)
        
        # 标记 Space 为 failed
        space['status'] = 'failed'
        space['updated_at'] = int(time.time())
        self.redis.set(f'hfs:space:{self.space_id}', json.dumps(space))
        
        return False

    def register(self):
        """注册 Space 并绑定 Node"""
        from . import audit
        
        self.diag.info('worker_starting', space_id=self.space_id, 
                       project_id=self.project_id, node_id=self.node_id,
                       external=self.external)
        
        # 检测 project_id 一致性
        if not self._check_project_consistency():
            return False
        
        # 审计：Worker 启动
        audit.log(self.redis, self.space_id, 'worker_start', f'worker/{self.instance_id}',
                  project=self.project_id, node=self.node_id, external=self.external)
        
        # 外部节点：注册为 pending，等待调度器分配
        if self.external:
            space_key = f'hfs:space:{self.space_id}'
            now = int(time.time())
            
            # 检查是否有空闲节点
            node_id = self._find_available_node()
            if node_id:
                # 有空闲节点，直接绑定
                space = {
                    'id': self.space_id,
                    'status': 'running',
                    'instance_id': self.instance_id,
                    'project_id': self.project_id,
                    'node_id': node_id,
                    'type': 'external',
                    'run_timeout': self.run_timeout,
                    'last_heartbeat': now,
                    'started_at': now,
                    'created_at': now,
                    'updated_at': now
                }
                self.redis.set(space_key, json.dumps(space))
                # 更新 node 绑定
                self.redis.set(f'hfs:node:{self.project_id}:{node_id}', json.dumps({
                    'id': node_id, 'space_id': self.space_id, 'space': self.space_id, 'status': 'running', 'updated_at': now
                }))
                self.node_id = node_id
                print(f'[HFS] External node bound to {node_id}: {self.space_id}')
            else:
                # 节点满，注册为 pending 等待调度
                space = {
                    'id': self.space_id,
                    'status': 'pending',
                    'instance_id': self.instance_id,
                    'project_id': self.project_id,
                    'node_id': '',
                    'type': 'external',
                    'run_timeout': self.run_timeout,
                    'last_heartbeat': now,
                    'created_at': now,
                    'updated_at': now
                }
                self.redis.set(space_key, json.dumps(space))
                print(f'[HFS] External node pending (nodes full): {self.space_id}')
            
            self.diag.info('external_registered', instance_id=self.instance_id, node_id=node_id)
            return True
        
        # 尝试绑定 Node（原子操作会同时更新 Space 状态）
        if self.node_id and self.project_id:
            ok, msg = atomic_bind(self.redis, self.project_id, self.node_id, 
                                 self.space_id, self.instance_id)
            if ok:
                self.diag.info('bind_success', msg=msg)
                print(f'[HFS] Bind: {msg}')
            else:
                # 绑定失败的原因
                self.diag.error('bind_failed', reason=msg)
                print(f'[HFS] Bind failed: {msg}')
                
                # 如果是因为 Space 已绑定到其他 Node，说明代码不一致，应该退出
                if msg == 'space_bound_to_other':
                    print(f'[HFS] Space bound to another node, code mismatch detected. Exiting...', flush=True)
                    audit.log(self.redis, self.space_id, 'bind_failed_exit', f'worker/{self.instance_id}',
                              reason=msg, project=self.project_id, node=self.node_id)
                    
                    # 标记 Space 为 failed
                    space_key = f'hfs:space:{self.space_id}'
                    space_data = self.redis.get(space_key)
                    if space_data:
                        space = json.loads(space_data)
                        space['status'] = 'failed'
                        space['updated_at'] = int(time.time())
                        self.redis.set(space_key, json.dumps(space))
                    
                    return False
                
                # 其他原因（如 node_not_idle），降级为 standalone
                print(f'[HFS] Running standalone')
                self.node_id = None
        
        # 只有无 Node 模式才需要手动创建 Space 记录
        # 有 Node 模式下，atomic_bind 已经处理了 Space 状态
        if not self.node_id:
            space_key = f'hfs:space:{self.space_id}'
            now = int(time.time())
            existing = self.redis.get(space_key)
            if existing:
                space = json.loads(existing)
                space['instance_id'] = self.instance_id
                space['last_heartbeat'] = now
                space['updated_at'] = now
            else:
                space = {
                    'id': self.space_id,
                    'status': 'starting',
                    'instance_id': self.instance_id,
                    'project_id': self.project_id or '',
                    'node_id': '',
                    'last_heartbeat': now,
                    'started_at': now,
                    'created_at': now,
                    'updated_at': now
                }
            self.redis.set(space_key, json.dumps(space))
        
        self.diag.info('worker_registered', instance_id=self.instance_id)
        print(f'[HFS] Registered: {self.space_id} (instance={self.instance_id})')
        return True
    
    def send_heartbeat(self):
        """发送心跳，返回 (ok, status/msg)"""
        start_time = time.time()
        ok, result = atomic_heartbeat(self.redis, self.space_id, self.instance_id)
        latency = (time.time() - start_time) * 1000  # ms
        
        self._heartbeat_count += 1
        
        if not ok:
            # instance_mismatch 表示被新 Space 抢占，需要退出
            if result == 'instance_mismatch':
                self.diag.info('replaced_detected', space_id=self.space_id)
                self._should_exit = True
                return True, 'replaced'  # 返回 True 让主循环检测 should_exit
            self.diag.error('heartbeat_failed', reason=result, count=self._heartbeat_count)
            return False, result
        
        # 记录心跳指标
        from . import metrics
        metrics.observe(self.redis, 'heartbeat_latency', latency, project=self.project_id)
        
        self.diag.metric('heartbeat_latency', latency, {'space_id': self.space_id})
        self.diag.info('heartbeat_sent', status=result, count=self._heartbeat_count, 
                       latency_ms=round(latency, 2))
        
        status = result
        if status == 'draining':
            self.diag.info('draining_detected', space_id=self.space_id)
            self._should_exit = True
        
        return True, status
    
    def should_exit(self):
        """是否应该退出"""
        return self._should_exit
    
    def run(self):
        """主循环"""
        if not self.register():
            return
        
        self._running = True
        self._started_at = int(time.time())
        
        # 启动调度线程（外部节点不执行调度）
        if self.project_id and not self.external:
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()
        
        # 启动项目脚本（外部节点 pending 时不启动，等绑定后再启动）
        if self.project_id and self.node_id:
            self._start_project_script()
        
        self.diag.info('worker_running', heartbeat_interval=self.heartbeat_interval,
                       run_timeout=self.run_timeout, external=self.external)
        timeout_str = '永不' if self.run_timeout is None else f'{self.run_timeout}s'
        print(f'[HFS] Worker 启动，心跳={self.heartbeat_interval}s，超时={timeout_str}')
        
        # 心跳循环
        while self._running:
            try:
                ok, result = self.send_heartbeat()
                
                if not ok:
                    print(f'[HFS] Heartbeat failed: {result}, exiting')
                    self._shutdown()
                    break
                
                # 外部节点：pending -> running 时启动 start_script
                if self.external and result == 'running' and not self._process:
                    # 从 Redis 获取绑定的 node_id
                    space_data = self.redis.get(f'hfs:space:{self.space_id}')
                    if space_data:
                        space = json.loads(space_data)
                        self.node_id = space.get('node_id')
                        if self.node_id:
                            print(f'[HFS] External node bound to {self.node_id}, starting script')
                            self._start_project_script()
                
                if self.should_exit():
                    print('[HFS] Draining detected, exiting gracefully')
                    self._shutdown()
                    
                    # 暂停 HF Space 容器释放资源
                    try:
                        from .hf import pause_space
                        # 从 Redis 获取 token
                        if self.space_id and '/' in self.space_id:
                            username = self.space_id.split('/')[0]
                            acc_data = self.redis.get(f'hfs:account:{username}')
                            if acc_data:
                                acc = json.loads(acc_data)
                                pause_space(self.space_id, acc.get('token'))
                                print(f'[HFS] Space paused: {self.space_id}')
                    except Exception as e:
                        print(f'[HFS] Failed to pause space: {e}')
                    
                    break
                
            except Exception as e:
                self.diag.error('heartbeat_exception', error=str(e))
                print(f'[HFS] Heartbeat error: {e}')
            
            time.sleep(self.heartbeat_interval)
    
    def _scheduler_loop(self):
        """调度线程 - 抢锁执行调度"""
        lock_key = f'hfs:lock:scheduler:{self.project_id}'
        
        while self._running:
            try:
                # 抢锁
                acquired = self.redis.set(lock_key, self.space_id, nx=True, ex=30)
                
                if acquired:
                    self.diag.info('scheduler_lock_acquired')
                    try:
                        self._do_schedule()
                    except Exception as e:
                        self.diag.error('schedule_error', error=str(e))
                        print(f'[HFS] Schedule error: {e}')
                    finally:
                        # 释放锁
                        if self.redis.get(lock_key) == self.space_id:
                            self.redis.delete(lock_key)
                
            except Exception as e:
                self.diag.error('scheduler_loop_error', error=str(e))
            
            # 随机睡眠避免同步
            time.sleep(random.uniform(8, 12))  # 测试用：10秒左右
    
    def _cleanup_zombie_spaces_globally(self):
        """跨项目清理僵尸 Space（只清理，不调度）"""
        from .health import detect_crashed_spaces
        from .state import atomic_transition, atomic_unbind
        from .policy import get_project_config
        
        # 获取所有项目
        all_projects = set()
        for key in self.redis.scan_iter('hfs:project:*'):
            if ':stats' not in key:
                project_id = key.split(':')[-1]
                all_projects.add(project_id)
        
        # 清理其他项目的僵尸（不包括自己的项目，自己的项目在后面处理）
        for project_id in all_projects:
            if project_id == self.project_id:
                continue
            
            # 获取项目配置
            proj_data = self.redis.get(f'hfs:project:{project_id}')
            if not proj_data:
                continue
            
            project = json.loads(proj_data)
            config = get_project_config(project)
            
            # 检测僵尸
            crashed = detect_crashed_spaces(
                self.redis, project_id,
                heartbeat_timeout=config.get('heartbeat_timeout', 60),
                startup_timeout=config.get('startup_timeout', 600)
            )
            
            # 清理僵尸
            for c in crashed:
                space_id = c['space_id']
                target_status = c.get('mark_as', 'failed')
                
                # 获取 node_id
                space_data = self.redis.get(f"hfs:space:{space_id}")
                node_id = None
                if space_data:
                    space = json.loads(space_data)
                    node_id = space.get('node_id')
                    current_status = space.get('status')
                    
                    # 标记并解绑
                    print(f'[Health] Cross-project cleanup: {space_id} ({project_id}): {current_status} -> {target_status}', flush=True)
                    atomic_transition(self.redis, space_id, current_status, target_status)
                    if node_id:
                        atomic_unbind(self.redis, project_id, node_id, space_id)
    
    def _do_schedule(self):
        """执行调度"""
        from .health import detect_crashed_spaces, validate_consistency, cleanup_spaces
        from .scheduler import Scheduler
        
        now = int(time.time())
        self.diag.info('do_schedule_start', project_id=self.project_id)
        
        # 0. 跨项目僵尸清理（轻量级，只清理不调度）
        self._cleanup_zombie_spaces_globally()
        
        # 1. 健康检查（自己的项目）
        crashed = detect_crashed_spaces(self.redis, self.project_id,
                                        heartbeat_timeout=self.config.get('heartbeat_timeout', 60))
        for c in crashed:
            self.diag.info('crashed_detected', space_id=c['space_id'], reason=c['reason'])
            space_id = c['space_id']
            
            # 根据 mark_as 决定标记为 failed 还是 unusable
            target_status = c.get('mark_as', 'failed')
            
            # 先获取 node_id（transition 会清空 node）
            space_data = self.redis.get(f"hfs:space:{space_id}")
            node_id = None
            if space_data:
                space = json.loads(space_data)
                node_id = space.get('node_id')
            
            if target_status == 'unusable':
                # starting 超时，标记 unusable 并解绑 Node
                # 先查 HF 状态用于诊断
                try:
                    from .hf import get_space_status
                    if space_data:
                        sp = json.loads(space_data)
                        acc_key = f"hfs:account:{sp.get('account_id')}"
                        acc_data = self.redis.get(acc_key)
                        if acc_data:
                            acc = json.loads(acc_data)
                            hf_status = get_space_status(space_id, acc.get('token'))
                            print(f"[Health] unusable: {space_id}, HF stage={hf_status.get('stage')}, started_at={sp.get('started_at')}", flush=True)
                except Exception as e:
                    print(f"[Health] unusable: {space_id}, HF check failed: {e}", flush=True)
                from .state import atomic_unbind
                atomic_transition(self.redis, space_id, 'starting', 'unusable')
                if node_id:
                    atomic_unbind(self.redis, self.project_id, node_id, space_id)
            else:
                # running 超时，标记 failed 并解绑 Node
                from .state import atomic_unbind
                atomic_transition(self.redis, space_id, 'running', 'failed')
                if node_id:
                    atomic_unbind(self.redis, self.project_id, node_id, space_id)
        
        # 2. 一致性验证
        issues = validate_consistency(self.redis, self.project_id)
        if issues:
            self.diag.info('consistency_issues', count=len(issues))
        
        # 3. 清理
        cleaned = cleanup_spaces(self.redis, self.project_id,
                                 cleanup_age=self.config.get('cleanup_age', 3600))
        
        # 4. 轮换检测 - 检查所有 running Space 是否超时
        run_timeout = self.config.get('run_timeout', 3600)
        self.diag.info('checking_rotation', run_timeout=run_timeout)
        
        scheduler = Scheduler(self.redis_url)
        created_in_this_schedule = False  # 标记本次调度是否已创建
        
        for key in self.redis.scan_iter('hfs:space:*'):
            data = self.redis.get(key)
            if not data:
                continue
            space = json.loads(data)
            space_project = space.get('project_id')
            if space_project != self.project_id:
                continue
            if space.get('status') != 'running':
                continue
            # 外部节点不参与轮换
            if space.get('type') == 'external':
                continue
            
            started_at = space.get('started_at', space.get('created_at', now))
            runtime = now - started_at
            space_id = space.get('id')
            
            # 使用 Space 存储的 timeout，如果没有则用配置值
            space_timeout = space.get('run_timeout')
            if space_timeout is None:
                # 配置值可能是 list，需要计算
                from .policy import calc_run_timeout
                space_timeout = int(calc_run_timeout(run_timeout, use_jitter=False))
            
            # Debug: 输出详细信息
            print(f'[DEBUG] Space {space_id}: now={now}, started_at={started_at}, runtime={runtime}, timeout={space_timeout}', flush=True)
            
            self.diag.info('space_runtime_check', space_id=space_id, 
                          runtime=runtime, timeout=space_timeout)
            
            if runtime > space_timeout:
                self.diag.info('rotation_triggered', space_id=space_id, 
                              runtime=runtime, timeout=space_timeout)
                print(f'[HFS] Space {space_id} 超时({runtime}s>{space_timeout}s)，触发轮换', flush=True)
                
                from . import metrics
                metrics.inc(self.redis, 'space_rotated', project=self.project_id)
                metrics.observe(self.redis, 'space_runtime', runtime, project=self.project_id)
                
                # 先创建替换者，只有成功创建后才标记 draining
                node_id = space.get('node_id')
                if node_id and not created_in_this_schedule:
                    self.diag.info('creating_replacement_for_rotation', node_id=node_id, old_space=space_id)
                    print(f'[HFS] 为轮换创建替换 Space (node={node_id})', flush=True)
                    
                    new_space_id, _ = scheduler.create_and_deploy_space(self.project_id, node_id)
                    if new_space_id:
                        self.diag.info('replacement_created', old_space=space_id, new_space=new_space_id, node_id=node_id)
                        print(f'[HFS] 替换 Space 创建成功: {space_id} → {new_space_id}', flush=True)
                        created_in_this_schedule = True
                        
                        # 只有成功创建替换者后，才标记 draining
                        atomic_transition(self.redis, space_id, 'running', 'draining')
                        print(f'[HFS] 标记 {space_id} 为 draining', flush=True)
                    else:
                        self.diag.error('replacement_creation_failed', node_id=node_id)
                        print(f'[HFS] 替换 Space 创建失败，保持 {space_id} 继续运行', flush=True)
                else:
                    if created_in_this_schedule:
                        print(f'[HFS] 本次调度已创建 Space，{space_id} 下次轮换', flush=True)
                    else:
                        print(f'[HFS] {space_id} 没有绑定 Node，无法创建替换者', flush=True)
        
        # 5. 为空闲 Node 或 draining Space 的 Node 创建 Space（每次调度最多创建一个）
        proj_data = self.redis.get(f'hfs:project:{self.project_id}')
        if proj_data:
            proj = json.loads(proj_data)
            required_nodes = proj.get('required_nodes', proj.get('min_nodes', 1))
            
            for key in self.redis.scan_iter(f'hfs:node:{self.project_id}:*'):
                if created_in_this_schedule:
                    break  # 本次调度已创建，跳过其他 Node
                
                data = self.redis.get(key)
                if not data:
                    continue
                node = json.loads(data)
                
                if node.get('status') not in ('idle', 'pending'):
                    continue
                
                node_id = node.get('id')
                space_id = node.get('space')
                
                # 情况1: Node 没有 Space，优先使用 pending 外部节点
                if not space_id:
                    pending_external = self._find_pending_external()
                    if pending_external:
                        self._bind_external_to_node(pending_external, node_id)
                        print(f'[HFS] 外部节点 {pending_external} 绑定到 Node {node_id}', flush=True)
                        created_in_this_schedule = True
                        continue
                    
                    self.diag.info('creating_space_for_node', node_id=node_id, reason='no_space')
                    print(f'[HFS] 为 Node {node_id} 创建 Space (无 Space)', flush=True)
                    
                    new_space_id, _ = scheduler.create_and_deploy_space(self.project_id, node_id)
                    if new_space_id:
                        self.diag.info('space_created', space_id=new_space_id, node_id=node_id)
                        created_in_this_schedule = True
                    else:
                        self.diag.error('space_creation_failed', node_id=node_id)
                    continue
                
                # 情况2: Node 有 Space，检查状态
                space_data = self.redis.get(f'hfs:space:{space_id}')
                if not space_data:
                    # Space 记录不存在，创建新的
                    self.diag.info('creating_space_for_node', node_id=node_id, reason='space_not_found')
                    print(f'[HFS] 为 Node {node_id} 创建 Space (Space 记录丢失)', flush=True)
                    
                    new_space_id, _ = scheduler.create_and_deploy_space(self.project_id, node_id)
                    if new_space_id:
                        self.diag.info('space_created', space_id=new_space_id, node_id=node_id)
                        created_in_this_schedule = True
                    continue
                
                space = json.loads(space_data)
                space_status = space.get('status')
                
                # 情况3: Space 是 draining 或 failed，优先使用 pending 外部节点
                if space_status in ('draining', 'failed'):
                    pending_external = self._find_pending_external()
                    if pending_external:
                        self._bind_external_to_node(pending_external, node_id)
                        print(f'[HFS] 外部节点 {pending_external} 替换 {space_id} (node={node_id})', flush=True)
                        created_in_this_schedule = True
                        continue
                    
                    self.diag.info('creating_space_for_node', node_id=node_id, reason=f'{space_status}_replacement')
                    print(f'[HFS] 为 Node {node_id} 创建替换 Space (当前 Space {space_status})', flush=True)
                    
                    new_space_id, _ = scheduler.create_and_deploy_space(self.project_id, node_id)
                    if new_space_id:
                        self.diag.info('space_created', space_id=new_space_id, node_id=node_id, 
                                      replaced=space_id)
                        print(f'[HFS] 替换 Space: {space_id} → {new_space_id}', flush=True)
                        created_in_this_schedule = True
                    else:
                        self.diag.error('space_creation_failed', node_id=node_id)
    
    def _start_project_script(self):
        """启动项目 start_script"""
        proj_data = self.redis.get(f'hfs:project:{self.project_id}')
        if not proj_data:
            return
        
        proj = json.loads(proj_data)
        start_cfg = proj.get('start_script', {})
        
        if start_cfg.get('type') == 'inline':
            script = start_cfg.get('inline')
            if script:
                self._start_process(script)
    
    def _start_process(self, script):
        """启动脚本进程"""
        if self._process:
            return
        
        # 确保环境变量设置
        import os
        os.environ['HFS_NODE_ID'] = self.node_id or ''
        os.environ['HFS_PROJECT_ID'] = self.project_id or ''
        
        self.diag.info('process_starting', script=script)
        print(f'[HFS] Starting: {script}', flush=True)
        print(f'[HFS] ENV: HFS_NODE_ID={os.environ.get("HFS_NODE_ID")}, HFS_PROJECT_ID={os.environ.get("HFS_PROJECT_ID")}', flush=True)
        self._process = subprocess.Popen(
            script, shell=True, start_new_session=True
        )
        self.diag.info('process_started', pid=self._process.pid)
        print(f'[HFS] Started, pid={self._process.pid}', flush=True)
    
    def _shutdown(self):
        """关闭 Worker"""
        from . import audit
        
        self._running = False
        self.diag.info('worker_stopping', heartbeat_count=self._heartbeat_count)
        
        # 审计：Worker 退出
        audit.log(self.redis, self.space_id, 'worker_stop', f'worker/{self.instance_id}',
                  heartbeat_count=self._heartbeat_count, should_exit=self._should_exit)
        
        # Kill 进程
        if self._process:
            try:
                pgid = os.getpgid(self._process.pid)
                os.killpg(pgid, signal.SIGTERM)
                self.diag.info('process_killed', pgid=pgid)
                print(f'[HFS] Killed process group {pgid}')
            except ProcessLookupError:
                pass
        
        # 执行 stop_script
        if self.project_id:
            proj_data = self.redis.get(f'hfs:project:{self.project_id}')
            if proj_data:
                proj = json.loads(proj_data)
                stop_cfg = proj.get('stop_script', {})
                if stop_cfg.get('type') == 'inline':
                    script = stop_cfg.get('inline')
                    if script:
                        try:
                            subprocess.run(script, shell=True, timeout=60)
                        except Exception as e:
                            self.diag.error('stop_script_failed', error=str(e))
                            print(f'[HFS] Stop script error: {e}')
        
        # 更新状态
        space_data = self.redis.get(f'hfs:space:{self.space_id}')
        if space_data:
            space = json.loads(space_data)
            if space.get('status') == 'draining':
                # transition 会自动清理 node 字段
                atomic_transition(self.redis, self.space_id, 'draining', 'exited')
                from . import metrics
                metrics.inc(self.redis, 'space_exited', project=self.project_id)
                self.diag.info('status_transitioned', from_status='draining', to_status='exited')
        
        self.diag.info('worker_stopped', total_heartbeats=self._heartbeat_count)
        print('[HFS] Worker exited')
        
        self.diag.info('worker_stopped', total_heartbeats=self._heartbeat_count)
        print('[HFS] Worker exited')
