"""诊断日志模块"""
import time
import json
import redis
from typing import Dict, Any


class DiagLogger:
    """诊断日志收集器"""
    
    def __init__(self, redis_url: str, component: str, instance_id: str):
        """
        Args:
            redis_url: Redis 连接
            component: 组件名（worker/scheduler/health）
            instance_id: 实例 ID
        """
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.component = component
        self.instance_id = instance_id
    
    def log(self, level: str, event: str, data: Dict[str, Any] = None):
        """记录日志
        
        Args:
            level: 日志级别（INFO/WARN/ERROR）
            event: 事件名称
            data: 附加数据
        """
        log_entry = {
            'timestamp': time.time(),
            'component': self.component,
            'instance_id': self.instance_id,
            'level': level,
            'event': event,
            'data': data or {}
        }
        
        # 写入 Redis List（最近 1000 条）
        key = f'hfs:logs:{self.component}'
        self.redis.lpush(key, json.dumps(log_entry))
        self.redis.ltrim(key, 0, 999)
        
        # 同时输出到 stdout（Space 日志）
        print(f"[{level}] [{self.component}/{self.instance_id}] {event} {json.dumps(data or {})}")
    
    def info(self, event: str, **kwargs):
        """INFO 日志"""
        self.log('INFO', event, kwargs)
    
    def warn(self, event: str, **kwargs):
        """WARN 日志"""
        self.log('WARN', event, kwargs)
    
    def error(self, event: str, **kwargs):
        """ERROR 日志"""
        self.log('ERROR', event, kwargs)
    
    def metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            tags: 标签
        """
        metric_entry = {
            'timestamp': time.time(),
            'component': self.component,
            'instance_id': self.instance_id,
            'name': name,
            'value': value,
            'tags': tags or {}
        }
        
        # 写入时序数据（按小时分桶）
        hour_key = time.strftime('%Y%m%d%H')
        key = f'hfs:metrics:{hour_key}'
        self.redis.lpush(key, json.dumps(metric_entry))
        self.redis.expire(key, 86400 * 7)  # 保留 7 天


def get_recent_logs(redis_url: str, component: str = None, limit: int = 100):
    """获取最近的日志
    
    Args:
        redis_url: Redis 连接
        component: 组件名（可选）
        limit: 返回条数
    
    Returns:
        日志列表
    """
    r = redis.from_url(redis_url, decode_responses=True)
    
    if component:
        key = f'hfs:logs:{component}'
        logs = r.lrange(key, 0, limit - 1)
    else:
        # 获取所有组件的日志
        logs = []
        for comp in ['worker', 'scheduler', 'health']:
            key = f'hfs:logs:{comp}'
            logs.extend(r.lrange(key, 0, limit - 1))
    
    # 解析并排序
    parsed = [json.loads(log) for log in logs]
    parsed.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return parsed[:limit]


def get_metrics(redis_url: str, hours: int = 1):
    """获取指标数据
    
    Args:
        redis_url: Redis 连接
        hours: 最近几小时
    
    Returns:
        指标列表
    """
    r = redis.from_url(redis_url, decode_responses=True)
    
    metrics = []
    now = time.time()
    
    for i in range(hours):
        hour_ts = now - (i * 3600)
        hour_key = time.strftime('%Y%m%d%H', time.localtime(hour_ts))
        key = f'hfs:metrics:{hour_key}'
        
        data = r.lrange(key, 0, -1)
        metrics.extend([json.loads(m) for m in data])
    
    return metrics


def analyze_errors(redis_url: str, hours: int = 1):
    """分析错误日志
    
    Returns:
        错误统计
    """
    logs = get_recent_logs(redis_url, limit=1000)
    
    errors = [log for log in logs if log['level'] == 'ERROR']
    
    # 按事件类型统计
    error_counts = {}
    for err in errors:
        event = err['event']
        error_counts[event] = error_counts.get(event, 0) + 1
    
    return {
        'total_errors': len(errors),
        'error_types': error_counts,
        'recent_errors': errors[:10]
    }
