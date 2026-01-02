"""配置文件加载器 - 支持 YAML 配置"""
import yaml
import os
from typing import Dict, Any, Optional


class Config:
    """统一配置管理"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.data = {}
        if config_file:
            self.load(config_file)
    
    def load(self, config_file: str):
        """加载 YAML 配置文件"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号路径"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def get_redis_url(self) -> str:
        """获取 Redis URL"""
        # 优先使用环境变量
        if os.getenv('HFS_REDIS_URL'):
            return os.getenv('HFS_REDIS_URL')
        
        # 从配置文件读取
        url = self.get('redis.url')
        if url:
            return url
        
        # 从分开的配置构建
        host = self.get('redis.host', 'localhost')
        port = self.get('redis.port', 6379)
        password = self.get('redis.password', '')
        db = self.get('redis.db', 0)
        
        if password:
            return f'redis://:{password}@{host}:{port}/{db}'
        return f'redis://{host}:{port}/{db}'
    
    def get_accounts(self) -> list:
        """获取账号列表"""
        return self.get('accounts.pool', [])
    
    def get_account_policy(self) -> Dict[str, Any]:
        """获取账号策略"""
        return self.get('accounts.policy', {})
    
    def get_projects(self) -> list:
        """获取项目列表"""
        return self.get('projects', [])
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取指定项目配置"""
        projects = self.get_projects()
        for proj in projects:
            if proj.get('id') == project_id:
                return proj
        return None
    
    def get_scenes(self) -> Dict[str, Any]:
        """获取自定义场景配置"""
        return self.get('scenes', {})
    
    def get_health_config(self) -> Dict[str, Any]:
        """获取健康检查配置"""
        return self.get('health', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get('monitoring', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})


def load_config(config_file: Optional[str] = None) -> Config:
    """加载配置文件
    
    优先级：
    1. 指定的配置文件
    2. 环境变量 HFS_CONFIG
    3. 当前目录 hfs.yaml
    4. ~/.hfs/config.yaml
    5. /etc/hfs/config.yaml
    """
    if config_file:
        return Config(config_file)
    
    # 尝试多个位置
    search_paths = [
        os.getenv('HFS_CONFIG'),
        'hfs.yaml',
        os.path.expanduser('~/.hfs/config.yaml'),
        '/etc/hfs/config.yaml'
    ]
    
    for path in search_paths:
        if path and os.path.exists(path):
            return Config(path)
    
    # 没有配置文件，返回空配置
    return Config()
