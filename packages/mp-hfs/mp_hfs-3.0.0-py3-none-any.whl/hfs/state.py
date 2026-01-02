"""状态机 + 原子操作（按 v2 设计文档 STATE.md）"""
import time
import json

# Lua: bind - 原子绑定 Node-Space
# 逻辑：Node 可被抢占（轮换），Space 不可被抢占
BIND_SCRIPT = """
local node_key, space_key = KEYS[1], KEYS[2]
local node_id, space_id, instance_id, ts = ARGV[1], ARGV[2], ARGV[3], ARGV[4]

local node = redis.call('GET', node_key)
if not node then return {0, 'node_not_found'} end

local nd = cjson.decode(node)

-- Space 不存在则创建
local space = redis.call('GET', space_key)
local sd
if not space then
    sd = {
        id = space_id,
        status = 'idle',
        instance_id = '',
        project_id = nd.project_id or '',
        node_id = '',
        last_heartbeat = 0,
        created_at = tonumber(ts),
        updated_at = tonumber(ts)
    }
else
    sd = cjson.decode(space)
end

local function is_empty(v)
    return v == nil or v == cjson.null or v == ''
end

-- Space 已绑定其他 Node：拒绝
if not is_empty(sd.node_id) and sd.node_id ~= node_id then
    return {-1, 'space_bound_to_other'}
end

-- 已绑定到彼此
if nd.space_id == space_id and sd.node_id == node_id then
    if sd.instance_id == instance_id then
        return {1, 'already_bound'}
    else
        -- 新 instance 更新
        sd.instance_id = instance_id
        -- 如果是从 exited/idle/failed 状态复用，重置 started_at
        -- draining 不复用，因为 Worker 正在退出
        if sd.status == 'exited' or sd.status == 'idle' or sd.status == 'failed' then
            sd.started_at = tonumber(ts)
        end
        sd.status = 'starting'
        sd.updated_at = tonumber(ts)
        redis.call('SET', space_key, cjson.encode(sd))
        return {1, 'instance_updated'}
    end
end

-- Node 已绑定其他 Space：抢占（轮换场景）
-- 清空旧 Space 的 instance_id 和 node_id，使其心跳返回 instance_mismatch
local old_space_id = nd.space_id
if old_space_id and old_space_id ~= cjson.null and old_space_id ~= '' and old_space_id ~= space_id then
    local old_space_key = 'hfs:space:' .. old_space_id
    local old_space = redis.call('GET', old_space_key)
    if old_space then
        local old_sd = cjson.decode(old_space)
        local old_project_id = old_sd.project_id or ''
        old_sd.instance_id = ''
        old_sd.node_id = cjson.null
        old_sd.updated_at = tonumber(ts)
        redis.call('SET', old_space_key, cjson.encode(old_sd))
        
        -- 从 active SET 移除旧 Space
        if old_project_id ~= '' then
            redis.call('SREM', 'hfs:project:' .. old_project_id .. ':spaces:active', old_space_id)
        end
        local old_username = string.match(old_space_id, '^([^/]+)/')
        if old_username then
            redis.call('SREM', 'hfs:account:' .. old_username .. ':spaces:active', old_space_id)
        end
    end
end

-- 执行绑定
nd.space_id = space_id
nd.status = 'pending'
nd.updated_at = tonumber(ts)

-- 如果是从 exited/idle/failed 状态复用，重置 started_at
if sd.status == 'exited' or sd.status == 'idle' or sd.status == 'failed' then
    sd.started_at = tonumber(ts)
end

sd.node_id = node_id
sd.status = 'starting'
sd.instance_id = instance_id
sd.project_id = nd.project_id or ''  -- 更新 project_id（复用时可能变化）
sd.updated_at = tonumber(ts)

redis.call('SET', node_key, cjson.encode(nd))
redis.call('SET', space_key, cjson.encode(sd))

-- 添加到 active SET 索引
local project_id = sd.project_id or ''
if project_id ~= '' then
    redis.call('SADD', 'hfs:project:' .. project_id .. ':spaces:active', space_id)
end
local username = string.match(space_id, '^([^/]+)/')
if username then
    redis.call('SADD', 'hfs:account:' .. username .. ':spaces:active', space_id)
end

return {1, 'bound'}
"""

# Lua: heartbeat - 原子心跳
# starting 时自动转 running，同时更新 Node 状态
HEARTBEAT_SCRIPT = """
local space_key = KEYS[1]
local instance_id, ts = ARGV[1], ARGV[2]

local space = redis.call('GET', space_key)
if not space then return {0, 'not_found'} end

local sd = cjson.decode(space)

if sd.instance_id ~= instance_id then
    return {-1, 'instance_mismatch'}
end

sd.last_heartbeat = tonumber(ts)
local was_starting = (sd.status == 'starting')
if was_starting then
    sd.status = 'running'
end

redis.call('SET', space_key, cjson.encode(sd))

-- 同步更新 Node 状态
if was_starting and sd.node_id and sd.node_id ~= cjson.null and sd.node_id ~= '' then
    local project_id = sd.project_id or ''
    if project_id ~= '' then
        local node_key = 'hfs:node:' .. project_id .. ':' .. sd.node_id
        local node = redis.call('GET', node_key)
        if node then
            local nd = cjson.decode(node)
            nd.status = 'running'
            nd.updated_at = tonumber(ts)
            redis.call('SET', node_key, cjson.encode(nd))
        end
    end
end

return {1, sd.status}
"""

# Lua: transition - 原子状态转换
TRANSITION_SCRIPT = """
local space_key = KEYS[1]
local from_status, to_status, ts = ARGV[1], ARGV[2], ARGV[3]

local space = redis.call('GET', space_key)
if not space then return {0, 'not_found'} end

local sd = cjson.decode(space)

if sd.status ~= from_status then
    return {-1, 'status_mismatch'}
end

sd.status = to_status
sd.updated_at = tonumber(ts)

-- 转换到 exited/failed 时清理 node_id 和 space_id 绑定
if to_status == 'exited' or to_status == 'failed' then
    -- 先保存 node_id，再清空
    local old_node_id = sd.node_id
    sd.node_id = cjson.null
    
    -- 同步清理 Node 的 space_id
    if old_node_id and old_node_id ~= cjson.null and old_node_id ~= '' then
        local project_id = sd.project_id or ''
        if project_id ~= '' then
            local node_key = 'hfs:node:' .. project_id .. ':' .. old_node_id
            local node = redis.call('GET', node_key)
            if node then
                local nd = cjson.decode(node)
                nd.space_id = cjson.null
                nd.status = 'idle'
                nd.updated_at = tonumber(ts)
                redis.call('SET', node_key, cjson.encode(nd))
            end
        end
    end
end

redis.call('SET', space_key, cjson.encode(sd))

-- 转换到终态时从 active SET 移除
if to_status == 'exited' or to_status == 'failed' or to_status == 'unusable' then
    local space_id = sd.id or ''
    local project_id = sd.project_id or ''
    if project_id ~= '' then
        redis.call('SREM', 'hfs:project:' .. project_id .. ':spaces:active', space_id)
    end
    local username = string.match(space_id, '^([^/]+)/')
    if username then
        redis.call('SREM', 'hfs:account:' .. username .. ':spaces:active', space_id)
    end
end

return {1, 'ok'}
"""

# Lua: unbind - 原子解绑
UNBIND_SCRIPT = """
local node_key, space_key = KEYS[1], KEYS[2]
local ts = ARGV[1]

local node = redis.call('GET', node_key)
local space = redis.call('GET', space_key)

if node then
    local nd = cjson.decode(node)
    nd.space_id = cjson.null
    nd.status = 'idle'
    nd.updated_at = tonumber(ts)
    redis.call('SET', node_key, cjson.encode(nd))
end

if space then
    local sd = cjson.decode(space)
    sd.node_id = cjson.null
    sd.updated_at = tonumber(ts)
    redis.call('SET', space_key, cjson.encode(sd))
end

return {1, 'unbound'}
"""

# Lua: transition_and_unbind - 原子转换并解绑
TRANSITION_AND_UNBIND_SCRIPT = """
local space_key = KEYS[1]
local node_key = KEYS[2]
local from_status, to_status, ts = ARGV[1], ARGV[2], ARGV[3]

local space = redis.call('GET', space_key)
if not space then return {0, 'space_not_found'} end

local sd = cjson.decode(space)

-- 检查状态
if sd.status ~= from_status then
    return {-1, 'status_mismatch'}
end

-- 获取 node_id（在清空前）
local node_id = sd.node_id

-- 转换状态
sd.status = to_status
sd.updated_at = tonumber(ts)
sd.node_id = cjson.null

redis.call('SET', space_key, cjson.encode(sd))

-- 解绑 node（如果有）
if node_id and node_key then
    local node = redis.call('GET', node_key)
    if node then
        local nd = cjson.decode(node)
        nd.space_id = cjson.null
        nd.status = 'idle'
        nd.updated_at = tonumber(ts)
        redis.call('SET', node_key, cjson.encode(nd))
    end
end

return {1, 'ok'}
"""


def atomic_bind(r, project_id, node_id, space_id, instance_id):
    """原子绑定 Node-Space"""
    from . import audit
    
    # 记录 bind 前状态
    old_space = r.get(f'hfs:space:{space_id}')
    old_instance = None
    if old_space:
        old_instance = json.loads(old_space).get('instance_id')
    
    script = r.register_script(BIND_SCRIPT)
    result = script(
        keys=[f'hfs:node:{project_id}:{node_id}', f'hfs:space:{space_id}'],
        args=[node_id, space_id, instance_id, int(time.time())]
    )
    
    # 审计日志
    audit.log(r, space_id, 'bind', f'worker/{instance_id}',
              node=node_id, old_instance=old_instance, 
              new_instance=instance_id, result=result[1])
    
    return result[0] > 0, result[1]


def atomic_heartbeat(r, space_id, instance_id):
    """原子心跳"""
    from . import audit
    
    script = r.register_script(HEARTBEAT_SCRIPT)
    result = script(
        keys=[f'hfs:space:{space_id}'],
        args=[instance_id, int(time.time())]
    )
    
    # 审计日志（只记录异常情况，避免日志过多）
    if result[0] <= 0 or result[1] in ('instance_mismatch', 'draining'):
        audit.log(r, space_id, 'heartbeat', f'worker/{instance_id}',
                  ok=result[0] > 0, result=result[1])
    
    return result[0] > 0, result[1]


def atomic_transition(r, space_id, from_status, to_status):
    """原子状态转换"""
    from . import audit
    
    script = r.register_script(TRANSITION_SCRIPT)
    result = script(
        keys=[f'hfs:space:{space_id}'],
        args=[from_status, to_status, int(time.time())]
    )
    
    # 审计日志
    audit.log(r, space_id, 'transition', 'scheduler',
              from_status=from_status, to_status=to_status, result=result[1])
    
    return result[0] > 0, result[1]


def atomic_unbind(r, project_id, node_id, space_id):
    """原子解绑"""
    from . import audit
    
    script = r.register_script(UNBIND_SCRIPT)
    result = script(
        keys=[f'hfs:node:{project_id}:{node_id}', f'hfs:space:{space_id}'],
        args=[int(time.time())]
    )
    
    # 审计日志
    audit.log(r, space_id, 'unbind', 'scheduler', node=node_id, result=result[1])
    
    return result[0] > 0, result[1]
