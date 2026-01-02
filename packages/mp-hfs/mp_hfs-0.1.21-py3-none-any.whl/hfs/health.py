import time
import json
DEFAULT_HEARTBEAT_TIMEOUT = 60
DEFAULT_STARTUP_TIMEOUT = 300
DEFAULT_DRAINING_TIMEOUT = 300
DEFAULT_CLEANUP_AGE = 3600
def detect_crashed_spaces(r, project_id, heartbeat_timeout=None, startup_timeout=None, draining_timeout=None):
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
        if status not in ('running', 'starting', 'draining'):
            continue
        if status == 'draining':
            timeout = draining_timeout
            last_hb = space.get('last_heartbeat', 0)
            if now - last_hb > timeout:
                from .state import atomic_transition
                atomic_transition(r, space['id'], 'draining', 'exited')
            continue
        if status == 'starting':
            timeout = startup_timeout
            base_time = space.get('started_at') or space.get('created_at') or 0
        else:
            timeout = heartbeat_timeout
            base_time = space.get('last_heartbeat', 0)
        if base_time > 0 and now - base_time > timeout:
            if status == 'starting':
                crashed.append({
                    'space_id': space['id'],
                    'reason': 'startup_timeout',
                    'last_heartbeat': base_time,
                    'timeout': timeout,
                    'mark_as': 'unusable'
                })
            else:
                crashed.append({
                    'space_id': space['id'],
                    'reason': 'heartbeat_timeout',
                    'last_heartbeat': base_time,
                    'timeout': timeout,
                    'mark_as': 'failed'
                })
    return crashed
def validate_consistency(r, project_id):
    issues = []
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
    for space_id, space in spaces.items():
        node_id = space.get('node_id')
        if node_id and node_id not in nodes:
            issues.append({
                'type': 'space_orphan',
                'space_id': space_id,
                'node_id': node_id,
                'reason': 'node_not_found'
            })
    for node_id, node in nodes.items():
        space_id = node.get('space_id') or node.get('space')
        if space_id and space_id not in spaces:
            issues.append({
                'type': 'node_orphan',
                'node_id': node_id,
                'space_id': space_id,
                'reason': 'space_not_found'
            })
            from .state import atomic_unbind
            ok, msg = atomic_unbind(r, project_id, node_id, space_id)
            print(f'[Health] Fixed node_orphan: {node_id} -> {space_id}, result={ok}', flush=True)
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
    cleanup_age = cleanup_age or DEFAULT_CLEANUP_AGE
    cleaned = []
    now = int(time.time())
    UNUSABLE_COOLDOWN = 7 * 24 * 3600
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
        if status == 'unusable':
            if age > UNUSABLE_COOLDOWN:
                from .hf import get_space_status
                space_id = space['id']
                username = space_id.split('/')[0] if '/' in space_id else None
                if username:
                    acc_data = r.get(f'hfs:account:{username}')
                    if acc_data:
                        acc = json.loads(acc_data)
                        hf_status = get_space_status(space_id, acc.get('token'))
                        if hf_status and hf_status.get('status') == 'RUNNING':
                            space['status'] = 'exited'
                            space['updated_at'] = now
                            r.set(key, json.dumps(space))
                            cleaned.append({'space_id': space_id, 'action': 'recovered'})
                        else:
                            r.delete(key)
                            cleaned.append({'space_id': space_id, 'action': 'deleted'})
    return cleaned