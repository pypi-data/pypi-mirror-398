"""审计日志 - 记录关键操作用于问题定位"""
import time
import json

MAX_ENTRIES = 200  # 每个 space 最多保留条数


def log(redis, space_id: str, op: str, by: str, **data):
    """记录审计日志
    
    Args:
        redis: Redis 连接
        space_id: Space ID
        op: 操作类型 (bind, heartbeat, transition, deploy, restart, etc.)
        by: 操作者 (worker/xxx, scheduler, etc.)
        **data: 额外数据
    """
    key = f'hfs:audit:{space_id}'
    entry = {
        'ts': int(time.time() * 1000),  # 毫秒精度
        'op': op,
        'by': by,
        **data
    }
    redis.rpush(key, json.dumps(entry))
    redis.ltrim(key, -MAX_ENTRIES, -1)  # 保留最新的


def get(redis, space_id: str, limit: int = 50) -> list:
    """获取审计日志"""
    key = f'hfs:audit:{space_id}'
    entries = redis.lrange(key, -limit, -1)
    return [json.loads(e) for e in entries]


def dump(redis, space_id: str):
    """打印审计日志"""
    entries = get(redis, space_id)
    print(f'=== Audit: {space_id} ({len(entries)} entries) ===')
    for e in entries:
        ts = time.strftime('%H:%M:%S', time.localtime(e['ts'] / 1000))
        ms = e['ts'] % 1000
        op = e.get('op', '?')
        by = e.get('by', '?')
        extra = {k: v for k, v in e.items() if k not in ('ts', 'op', 'by')}
        print(f'[{ts}.{ms:03d}] {op:15} by {by:20} {extra}')
