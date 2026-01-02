"""指标收集"""
import redis
import json
import time
import hashlib

def _labels_hash(labels: dict) -> str:
    if not labels:
        return 'default'
    s = '&'.join(f'{k}={v}' for k, v in sorted(labels.items()))
    return hashlib.md5(s.encode()).hexdigest()[:8]

def _key(typ: str, name: str, labels: dict, window: str = None) -> str:
    h = _labels_hash(labels)
    k = f'hfs:metric:{typ}:{name}:{h}'
    if window:
        k += f':{window}'
    return k

# Counter
def inc(r: redis.Redis, name: str, value: int = 1, **labels):
    """增加计数器"""
    # total
    r.incrby(_key('c', name, labels), value)
    # daily
    today = time.strftime('%Y-%m-%d')
    k = _key('c', name, labels, f'daily:{today}')
    r.incrby(k, value)
    r.expire(k, 7 * 86400)
    # hourly
    hour = time.strftime('%Y%m%d%H')
    k = _key('c', name, labels, f'hourly:{hour}')
    r.incrby(k, value)
    r.expire(k, 86400)

def get_counter(r: redis.Redis, name: str, window: str = None, **labels) -> int:
    """获取计数器值"""
    val = r.get(_key('c', name, labels, window))
    return int(val) if val else 0

# Gauge
def set_gauge(r: redis.Redis, name: str, value: float, **labels):
    """设置瞬时值"""
    r.set(_key('g', name, labels), value)

def get_gauge(r: redis.Redis, name: str, **labels) -> float:
    """获取瞬时值"""
    val = r.get(_key('g', name, labels))
    return float(val) if val else 0.0

# Histogram
BUCKETS = {
    'space_runtime': [60, 300, 900, 1800, 3600],
    'heartbeat_latency': [50, 100, 200, 500, 1000],
    'node_bindtime': [5, 10, 30, 60, 300],
}

def observe(r: redis.Redis, name: str, value: float, **labels):
    """记录直方图观测值"""
    key = _key('h', name, labels)
    data = r.get(key)
    h = json.loads(data) if data else {'count': 0, 'sum': 0, 'buckets': {}}
    
    h['count'] += 1
    h['sum'] += value
    
    buckets = BUCKETS.get(name, [100, 500, 1000, 5000])
    for b in buckets:
        if value <= b:
            h['buckets'][str(b)] = h['buckets'].get(str(b), 0) + 1
    h['buckets']['inf'] = h['buckets'].get('inf', 0) + 1
    
    r.set(key, json.dumps(h))

def get_histogram(r: redis.Redis, name: str, **labels) -> dict:
    """获取直方图"""
    data = r.get(_key('h', name, labels))
    return json.loads(data) if data else {'count': 0, 'sum': 0, 'buckets': {}}

def histogram_mean(r: redis.Redis, name: str, **labels) -> float:
    """获取直方图平均值"""
    h = get_histogram(r, name, **labels)
    return h['sum'] / h['count'] if h['count'] > 0 else 0

# 聚合
def aggregate_gauges(r: redis.Redis):
    """聚合瞬时值（每分钟调用）"""
    # 按项目统计 Space
    projects = set()
    space_counts = {}  # (project, status) -> count
    account_counts = {}  # account -> count
    account_project_counts = {}  # (account, project) -> count
    
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if not data:
            continue
        space = json.loads(data)
        project = space.get('project_id')
        status = space.get('status')
        space_id = space.get('id', '')
        account = space_id.split('/')[0] if '/' in space_id else None
        
        if project:
            projects.add(project)
        
        if status in ('running', 'starting', 'draining', 'standby'):
            space_counts[(project, status)] = space_counts.get((project, status), 0) + 1
            if account:
                account_counts[account] = account_counts.get(account, 0) + 1
                account_project_counts[(account, project)] = account_project_counts.get((account, project), 0) + 1
    
    # 写入 Gauge
    for (project, status), count in space_counts.items():
        set_gauge(r, 'active_spaces', count, project=project, status=status)
    
    for account, count in account_counts.items():
        set_gauge(r, 'account_spaces', count, account=account)
    
    for (account, project), count in account_project_counts.items():
        set_gauge(r, 'account_project_spaces', count, account=account, project=project)
    
    # 统计 idle nodes
    for project in projects:
        idle = 0
        for key in r.scan_iter(f'hfs:node:{project}:*'):
            data = r.get(key)
            if data:
                node = json.loads(data)
                if not node.get('space'):
                    idle += 1
        set_gauge(r, 'idle_nodes', idle, project=project)
