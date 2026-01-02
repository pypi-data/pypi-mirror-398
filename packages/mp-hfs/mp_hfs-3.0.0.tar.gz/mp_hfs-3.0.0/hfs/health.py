"""健康检查（按 v2 设计文档 HEALTH.md）"""
import time
import json

# 默认超时配置
DEFAULT_HEARTBEAT_TIMEOUT = 60
DEFAULT_STARTUP_TIMEOUT = 300
DEFAULT_DRAINING_TIMEOUT = 300
DEFAULT_CLEANUP_AGE = 3600


def detect_crashed_spaces(r, project_id, heartbeat_timeout=None, startup_timeout=None, draining_timeout=None):
    """检测心跳超时的 Space"""
    heartbeat_timeout = heartbeat_timeout or DEFAULT_HEARTBEAT_TIMEOUT
    startup_timeout = startup_timeout or DEFAULT_STARTUP_TIMEOUT
    draining_timeout = draining_timeout or DEFAULT_DRAINING_TIMEOUT
    
    crashed = []
    now = int(time.time())
    
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if not data:
            continue
        space = json.loads(data)
        
        space_project = space.get('project_id')
        if space_project != project_id:
            continue
        
        status = space.get('status')
        # exited 状态不检查心跳
        if status not in ('running', 'starting', 'draining'):
            continue
        
        # draining 状态心跳超时是正常的（Worker 已停止心跳），应转为 exited
        if status == 'draining':
            timeout = draining_timeout
            last_hb = space.get('last_heartbeat', 0)
            if now - last_hb > timeout:
                # 标记为 exited 而不是 failed
                from .state import atomic_transition
                atomic_transition(r, space['id'], 'draining', 'exited')
            continue
        
        # 获取超时时间和基准时间
        if status == 'starting':
            timeout = startup_timeout
            # starting 状态用 started_at 或 created_at 作为基准，因为还没发送过心跳
            base_time = space.get('started_at') or space.get('created_at') or 0
        else:
            timeout = heartbeat_timeout
            base_time = space.get('last_heartbeat', 0)
        
        if base_time > 0 and now - base_time > timeout:
            # starting 超时可能是 HF 平台问题，标记 unusable
            if status == 'starting':
                crashed.append({
                    'space_id': space['id'],
                    'reason': 'startup_timeout',
                    'last_heartbeat': base_time,
                    'timeout': timeout,
                    'mark_as': 'unusable'  # 标记为 unusable
                })
            else:
                # running 超时是 crashed，标记 failed（可能是项目代码问题）
                crashed.append({
                    'space_id': space['id'],
                    'reason': 'heartbeat_timeout',
                    'last_heartbeat': base_time,
                    'timeout': timeout,
                    'mark_as': 'failed'  # 标记为 failed，可以复用
                })
    
    return crashed


def validate_consistency(r, project_id):
    """验证数据一致性，返回问题列表"""
    issues = []
    
    # 收集所有 Space 和 Node
    spaces = {}
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if data:
            space = json.loads(data)
            space_project = space.get('project_id')
            if space_project == project_id:
                spaces[space['id']] = space
    
    nodes = {}
    for key in r.scan_iter(f'hfs:node:{project_id}:*'):
        data = r.get(key)
        if data:
            node = json.loads(data)
            nodes[node['id']] = node
    
    # 1. Space 指向的 Node 不存在
    for space_id, space in spaces.items():
        node_id = space.get('node_id')
        if node_id and node_id not in nodes:
            issues.append({
                'type': 'space_orphan',
                'space_id': space_id,
                'node_id': node_id,
                'reason': 'node_not_found'
            })
    
    # 2. Node 指向的 Space 不存在 - 自动修复
    for node_id, node in nodes.items():
        space_id = node.get('space_id') or node.get('space')
        if space_id and space_id not in spaces:
            issues.append({
                'type': 'node_orphan',
                'node_id': node_id,
                'space_id': space_id,
                'reason': 'space_not_found'
            })
            # 自动解绑
            from .state import atomic_unbind
            ok, msg = atomic_unbind(r, project_id, node_id, space_id)
            print(f'[Health] Fixed node_orphan: {node_id} -> {space_id}, result={ok}', flush=True)
    
    # 3. 双向绑定不一致
    for space_id, space in spaces.items():
        node_id = space.get('node_id')
        if node_id and node_id in nodes:
            node = nodes[node_id]
            node_space = node.get('space_id') or node.get('space')
            if node_space != space_id:
                issues.append({
                    'type': 'binding_mismatch',
                    'space_id': space_id,
                    'node_id': node_id,
                    'space_points_to': node_id,
                    'node_points_to': node.get('space')
                })
    
    return issues


def cleanup_spaces(r, project_id, cleanup_age=None):
    """清理过期的 Space
    
    策略：
    - exited/failed 不标记 unusable，保留用于复用
    - unusable 有 7 天冷静期，之后尝试恢复或删除
    """
    cleanup_age = cleanup_age or DEFAULT_CLEANUP_AGE
    cleaned = []
    now = int(time.time())
    
    UNUSABLE_COOLDOWN = 7 * 24 * 3600  # 7 天
    
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if not data:
            continue
        space = json.loads(data)
        
        space_project = space.get('project_id')
        if space_project != project_id:
            continue
        
        status = space.get('status')
        updated_at = space.get('updated_at', 0)
        age = now - updated_at
        
        # unusable 超过 7 天，尝试恢复或删除
        if status == 'unusable':
            if age > UNUSABLE_COOLDOWN:
                # 尝试验证 Space 是否可用
                from .hf import get_space_status
                space_id = space['id']
                username = space_id.split('/')[0] if '/' in space_id else None
                
                if username:
                    acc_data = r.get(f'hfs:account:{username}')
                    if acc_data:
                        acc = json.loads(acc_data)
                        hf_status = get_space_status(space_id, acc.get('token'))
                        
                        if hf_status and hf_status.get('status') == 'RUNNING':
                            # Space 可用，恢复为 exited
                            space['status'] = 'exited'
                            space['updated_at'] = now
                            r.set(key, json.dumps(space))
                            cleaned.append({'space_id': space_id, 'action': 'recovered'})
                        else:
                            # Space 不可用，删除
                            r.delete(key)
                            cleaned.append({'space_id': space_id, 'action': 'deleted'})
    
    return cleaned
