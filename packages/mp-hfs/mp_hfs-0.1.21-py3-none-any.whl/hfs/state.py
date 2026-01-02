import time
import json
def atomic_bind(r, project_id, node_id, space_id, instance_id):
    from . import audit
    old_space = r.get(f'hfs:space:{space_id}')
    old_instance = None
    if old_space:
        old_instance = json.loads(old_space).get('instance_id')
    script = r.register_script(BIND_SCRIPT)
    result = script(
        keys=[f'hfs:node:{project_id}:{node_id}', f'hfs:space:{space_id}'],
        args=[node_id, space_id, instance_id, int(time.time())]
    )
    audit.log(r, space_id, 'bind', f'worker/{instance_id}',
              node=node_id, old_instance=old_instance, 
              new_instance=instance_id, result=result[1])
    return result[0] > 0, result[1]
def atomic_heartbeat(r, space_id, instance_id):
    from . import audit
    script = r.register_script(HEARTBEAT_SCRIPT)
    result = script(
        keys=[f'hfs:space:{space_id}'],
        args=[instance_id, int(time.time())]
    )
    if result[0] <= 0 or result[1] in ('instance_mismatch', 'draining'):
        audit.log(r, space_id, 'heartbeat', f'worker/{instance_id}',
                  ok=result[0] > 0, result=result[1])
    return result[0] > 0, result[1]
def atomic_transition(r, space_id, from_status, to_status):
    from . import audit
    script = r.register_script(TRANSITION_SCRIPT)
    result = script(
        keys=[f'hfs:space:{space_id}'],
        args=[from_status, to_status, int(time.time())]
    )
    audit.log(r, space_id, 'transition', 'scheduler',
              from_status=from_status, to_status=to_status, result=result[1])
    return result[0] > 0, result[1]
def atomic_unbind(r, project_id, node_id, space_id):
    from . import audit
    script = r.register_script(UNBIND_SCRIPT)
    result = script(
        keys=[f'hfs:node:{project_id}:{node_id}', f'hfs:space:{space_id}'],
        args=[int(time.time())]
    )
    audit.log(r, space_id, 'unbind', 'scheduler', node=node_id, result=result[1])
    return result[0] > 0, result[1]