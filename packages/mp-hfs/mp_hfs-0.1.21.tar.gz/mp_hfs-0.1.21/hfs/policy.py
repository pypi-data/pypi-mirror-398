"""策略配置（按 v2 设计文档 POLICY.md）"""
import random

# 轮换策略
ROTATION = {
    'jitter': 0.2,  # 20% 随机抖动，避免同时超时
}

# 测试场景配置
TEST_SCENES = {
    'mock_fast': {
        'description': 'Mock 快速测试',
        'run_timeout': 60,
        'heartbeat_interval': 8,
        'heartbeat_timeout': 25,
        'startup_timeout': 30,
        'draining_timeout': 20,
        'reuse_interval': 15,
        'cleanup_age': 300,
    },
    'mock_normal': {
        'description': 'Mock 正常测试',
        'run_timeout': 120,
        'heartbeat_interval': 10,
        'heartbeat_timeout': 30,
        'startup_timeout': 60,
        'draining_timeout': 30,
        'reuse_interval': 30,
        'cleanup_age': 600,
    },
    'online_fast': {
        'description': '在线快速测试',
        'run_timeout': 120,
        'heartbeat_interval': 10,
        'heartbeat_timeout': 30,
        'startup_timeout': 180,
        'draining_timeout': 60,
        'reuse_interval': 30,
        'cleanup_age': 1800,
    },
    'online_normal': {
        'description': '在线正常测试',
        'run_timeout': 300,
        'heartbeat_interval': 15,
        'heartbeat_timeout': 45,
        'startup_timeout': 300,
        'draining_timeout': 120,
        'reuse_interval': 60,
        'cleanup_age': 3600,
    },
}

# 场景预设配置
SCENES = {
    'dev_test': {
        'description': '开发测试，快速迭代',
        'run_timeout': 300,
        'create_interval': 30,
        'heartbeat_interval': 10,
        'heartbeat_timeout': 30,
        'startup_timeout': 180,
        'draining_timeout': 60,
        'cooldown_on_rate_limit': 300,
        'cleanup_age': 1800,  # 30分钟，给足时间观察和复用
        'reuse_interval': 60,
    },
    'short_task': {
        'description': '短任务',
        'run_timeout': 1800,
        'create_interval': 180,
        'heartbeat_interval': 15,
        'heartbeat_timeout': 60,
        'startup_timeout': 300,
        'draining_timeout': 180,
        'cooldown_on_rate_limit': 3600,
        'cleanup_age': 1800,
        'reuse_interval': 300,
    },
    'long_task': {
        'description': '长任务',
        'run_timeout': 3600,
        'create_interval': 300,
        'heartbeat_interval': 30,
        'heartbeat_timeout': 90,
        'startup_timeout': 600,
        'draining_timeout': 300,
        'cooldown_on_rate_limit': 86400,
        'cleanup_age': 3600,
        'reuse_interval': 300,
    },
    'production': {
        'description': '生产环境（默认）',
        'run_timeout': (21600, 36000),  # 6-10小时随机
        'create_interval': 600,  # 10分钟
        'heartbeat_interval': 60,  # 60秒
        'heartbeat_timeout': 180,  # 3分钟
        'startup_timeout': 900,  # 15分钟
        'draining_timeout': 600,  # 10分钟
        'cooldown_on_rate_limit': 86400,  # 24小时
        'cleanup_age': 7200,  # 2小时
        'reuse_interval': 28800,  # 8小时（接近超时时长）
    }
}

# Space 命名策略
NAMING = {
    'prefixes': ['my', 'simple', 'quick', 'easy', 'mini', 'test', 'dev', 'new', 'basic', 'lite'],
    'words': ['chatbot', 'demo', 'app', 'tool', 'helper', 'project', 'space', 'translator', 'analyzer'],
    'number_probability': 0.5,
    'number_range': (1, 99),
}


def get_scene_config(scene_name):
    """获取场景配置，支持测试场景"""
    # 先查测试场景
    if scene_name in TEST_SCENES:
        return TEST_SCENES[scene_name].copy()
    # 再查正式场景
    return SCENES.get(scene_name, SCENES['production']).copy()


def get_test_scene(scene_name):
    """获取测试场景配置"""
    return TEST_SCENES.get(scene_name, TEST_SCENES['mock_fast']).copy()


def get_project_config(project):
    """获取项目配置（场景 + 项目覆盖）"""
    scene = project.get('scene', 'production')
    config = get_scene_config(scene)
    
    # 项目配置覆盖
    if 'config' in project:
        config.update(project['config'])
    
    # 处理 timeout 配置
    if 'timeout' in project:
        timeout_cfg = project['timeout']
        if 'min_seconds' in timeout_cfg and 'max_seconds' in timeout_cfg:
            config['run_timeout'] = (timeout_cfg['min_seconds'], timeout_cfg['max_seconds'])
        elif 'seconds' in timeout_cfg:
            config['run_timeout'] = timeout_cfg['seconds']
    
    return config


def calc_run_timeout(base_timeout, use_jitter=True):
    """计算运行超时（支持范围随机或 jitter）
    
    Args:
        base_timeout: 基础超时时间，可以是数字或 (min, max) 元组
        use_jitter: 是否使用 jitter（项目指定账号时可关闭）
    """
    # 支持范围随机：(min, max)
    if isinstance(base_timeout, (tuple, list)) and len(base_timeout) == 2:
        return random.uniform(base_timeout[0], base_timeout[1])
    
    # 传统 jitter 模式
    if not use_jitter:
        return base_timeout
    
    jitter = base_timeout * ROTATION['jitter']
    return base_timeout + random.uniform(-jitter, jitter)


def generate_space_name():
    """生成自然的 Space 名称"""
    prefix = random.choice(NAMING['prefixes'])
    word = random.choice(NAMING['words'])
    
    name = f'{prefix}-{word}'
    
    # 50% 概率添加数字
    if random.random() < NAMING['number_probability']:
        num = random.randint(*NAMING['number_range'])
        name = f'{name}-{num}'
    
    return name
