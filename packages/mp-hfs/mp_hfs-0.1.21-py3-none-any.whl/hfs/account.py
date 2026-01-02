import redis
import json
import time
import random
from typing import Optional, Dict
DEFAULT_MAX_DAILY_CREATES = 20
DEFAULT_MAX_SPACES = 5
DEFAULT_MAX_SPACES_PER_PROJECT = 2
def select_account(r: redis.Redis, project_id: str = None, exclude_accounts: set = None) -> Optional[Dict]:
    proj = {}
    if project_id:
        proj_data = r.get(f'hfs:project:{project_id}')
        if proj_data:
            proj = json.loads(proj_data)
    specified_accounts = proj.get('accounts')
    exclude_accounts = exclude_accounts or set()
    space_counts = {}
    project_space_counts = {}
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if not data:
            continue
        space = json.loads(data)
        if space.get('status') not in ('running', 'starting', 'draining'):
            continue
        space_id = space.get('id', '')
        if '/' not in space_id:
            continue
        owner = space_id.split('/')[0]
        space_counts[owner] = space_counts.get(owner, 0) + 1
        if project_id and space.get('project_id') == project_id:
            project_space_counts[owner] = project_space_counts.get(owner, 0) + 1
    account_names = r.smembers('hfs:accounts')
    if not account_names:
        account_names = {k.split(':')[-1] for k in r.scan_iter('hfs:account:*') if ':stats' not in k}
    candidates = []
    for username in account_names:
        data = r.get(f'hfs:account:{username}')
        if not data:
            continue
        acc = json.loads(data)
        if username in exclude_accounts:
            continue
        if specified_accounts and username not in specified_accounts:
            continue
        if acc.get('status') == 'banned':
            continue
        if not specified_accounts and acc.get('status') == 'cooldown':
            if acc.get('cooldown_until', 0) > time.time():
                continue
            acc['status'] = 'active'
            r.set(f'hfs:account:{username}', json.dumps(acc))
        today_created = get_today_created(r, username)
        max_daily = acc.get('max_daily_creates', DEFAULT_MAX_DAILY_CREATES)
        if today_created >= max_daily:
            continue
        max_spaces = acc.get('max_spaces', DEFAULT_MAX_SPACES)
        current_spaces = space_counts.get(username, 0)
        if current_spaces >= max_spaces:
            continue
        if project_id and not specified_accounts:
            project_spaces = project_space_counts.get(username, 0)
            max_per_project = acc.get('max_spaces_per_project', DEFAULT_MAX_SPACES_PER_PROJECT)
            if project_spaces >= max_per_project:
                continue
        acc['_score'] = calc_account_score(r, username)
        acc['_space_ratio'] = current_spaces / max_spaces if max_spaces > 0 else 1
        candidates.append(acc)
    if not candidates:
        return None
    low_usage = [a for a in candidates if a['_space_ratio'] < 0.7]
    pool = low_usage if low_usage else candidates
    good = [a for a in pool if a['_score'] > 0.5]
    return random.choice(good) if good else max(pool, key=lambda x: x['_score'])
def calc_account_score(r: redis.Redis, username: str) -> float:
    usage_rate = get_usage_rate(r, username)
    success_rate = get_success_rate(r, username)
    cooldown_count = get_cooldown_count(r, username)
    cooldown_penalty = 1.0 if cooldown_count == 0 else 0.5
    return (1 - usage_rate) * 0.4 + success_rate * 0.4 + cooldown_penalty * 0.2
def get_usage_rate(r: redis.Redis, username: str) -> float:
    today_created = get_today_created(r, username)
    acc_data = r.get(f'hfs:account:{username}')
    max_daily = DEFAULT_MAX_DAILY_CREATES
    if acc_data:
        acc = json.loads(acc_data)
        max_daily = acc.get('max_daily_creates', DEFAULT_MAX_DAILY_CREATES)
    return min(1.0, today_created / max_daily)
def get_account_space_count(r: redis.Redis, username: str) -> int:
    count = 0
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if not data:
            continue
        space = json.loads(data)
        space_id = space.get('id', '')
        if '/' in space_id and space_id.split('/')[0] == username:
            if space.get('status') in ('running', 'starting', 'draining'):
                count += 1
    return count
def get_account_project_space_count(r: redis.Redis, username: str, project_id: str) -> int:
    count = 0
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if not data:
            continue
        space = json.loads(data)
        space_id = space.get('id', '')
        if '/' in space_id and space_id.split('/')[0] == username:
            space_project = space.get('project_id')
            if space_project == project_id:
                if space.get('status') in ('running', 'starting', 'draining'):
                    count += 1
    return count
def get_today_created(r: redis.Redis, username: str) -> int:
    stats_data = r.get(f'hfs:account:{username}:stats')
    if not stats_data:
        return 0
    stats = json.loads(stats_data)
    today = time.strftime('%Y-%m-%d')
    return stats.get('daily', {}).get(today, {}).get('created', 0)
def get_success_rate(r: redis.Redis, username: str) -> float:
    stats_data = r.get(f'hfs:account:{username}:stats')
    if not stats_data:
        return 1.0
    stats = json.loads(stats_data)
    total = stats.get('total_created', 0) + stats.get('total_failed', 0)
    return stats.get('total_created', 0) / total if total > 0 else 1.0
def get_cooldown_count(r: redis.Redis, username: str) -> int:
    stats_data = r.get(f'hfs:account:{username}:stats')
    if not stats_data:
        return 0
    return json.loads(stats_data).get('cooldown_count', 0)
def update_account_stats(r: redis.Redis, username: str, success: bool = True):
    stats_key = f'hfs:account:{username}:stats'
    stats_data = r.get(stats_key)
    stats = json.loads(stats_data) if stats_data else {}
    today = time.strftime('%Y-%m-%d')
    if success:
        stats['total_created'] = stats.get('total_created', 0) + 1
        stats['consecutive_failures'] = 0
    else:
        stats['total_failed'] = stats.get('total_failed', 0) + 1
        stats['consecutive_failures'] = stats.get('consecutive_failures', 0) + 1
        if stats['consecutive_failures'] >= 3:
            mark_cooldown(r, username, 3600, 'consecutive_failures')
            stats['consecutive_failures'] = 0
    daily = stats.setdefault('daily', {})
    day_stats = daily.setdefault(today, {'created': 0, 'failed': 0})
    day_stats['created' if success else 'failed'] += 1
    stats['updated_at'] = int(time.time())
    r.set(stats_key, json.dumps(stats))
def mark_cooldown(r: redis.Redis, username: str, duration: int = 3600, reason: str = 'rate_limited'):
    from . import metrics
    key = f'hfs:account:{username}'
    data = r.get(key)
    if not data:
        return
    acc = json.loads(data)
    acc['status'] = 'cooldown'
    acc['cooldown_until'] = int(time.time()) + duration
    acc['cooldown_reason'] = reason
    r.set(key, json.dumps(acc))
    metrics.inc(r, 'account_cooldown', account=username, reason=reason)
    stats_key = f'hfs:account:{username}:stats'
    stats_data = r.get(stats_key)
    stats = json.loads(stats_data) if stats_data else {}
    stats['cooldown_count'] = stats.get('cooldown_count', 0) + 1
    r.set(stats_key, json.dumps(stats))
def mark_account_used(r: redis.Redis, username: str):
    key = f'hfs:account:{username}'
    data = r.get(key)
    if not data:
        return
    acc = json.loads(data)
    acc['last_used'] = int(time.time())
    r.set(key, json.dumps(acc))