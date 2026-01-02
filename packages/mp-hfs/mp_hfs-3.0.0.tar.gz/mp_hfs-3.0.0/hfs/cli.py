"""Admin CLI - 支持 YAML 配置导入"""
import click
import redis
import yaml
import json
import time
from pathlib import Path

# Import command groups
from .admin.account import account
from .admin.project import project
from .admin.node import node
from .admin.space import space
from .admin.health import health
from .admin.stats import stats
from .admin.bootstrap import bootstrap


@click.group()
@click.option('--redis-url', envvar='HFS_REDIS_URL', help='Redis URL')
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.pass_context
def cli(ctx, redis_url, config):
    """HFS Admin CLI - 管理工具"""
    ctx.ensure_object(dict)
    
    # 加载配置文件
    if config:
        with open(config) as f:
            ctx.obj['config'] = yaml.safe_load(f)
        # 从配置文件获取 Redis URL
        if not redis_url:
            redis_url = ctx.obj['config'].get('redis', {}).get('url')
    
    # 默认 Redis URL
    if not redis_url:
        redis_url = 'redis://:AVNS_Ix8jMr-b59MU0Y18Hb4@redis-mbook3-macbook3pro.aivencloud.com:11866/6'
    
    # 保存 redis_url 供 Scheduler 等需要 URL 的模块使用
    ctx.obj['redis_url'] = redis_url
    
    # Admin CLI 添加超时防止卡死
    ctx.obj['redis'] = redis.from_url(
        redis_url, 
        decode_responses=True,
        socket_connect_timeout=10,
        socket_timeout=30
    )


# Register command groups
cli.add_command(account)
cli.add_command(project)
cli.add_command(node)
cli.add_command(space)
cli.add_command(health)
cli.add_command(stats)
cli.add_command(bootstrap)


@cli.group()
def system():
    """System configuration commands"""
    pass


@system.command('set-code-source')
@click.option('--source', type=click.Choice(['local', 'git']), default='local', help='代码来源')
@click.option('--git-url', help='Git 仓库 URL')
@click.option('--git-token', help='Git 访问 token (私有仓库需要)')
@click.option('--git-branch', default='hfs', help='Git 分支名/项目名 (默认 hfs)')
@click.option('--git-ref', help='Git tag (不指定则自动使用该分支最新 tag)')
@click.pass_context
def set_code_source(ctx, source, git_url, git_token, git_branch, git_ref):
    """设置系统代码来源"""
    r = ctx.obj['redis']
    
    if source == 'git' and not git_url:
        click.echo("Error: --git-url 必须指定", err=True)
        ctx.exit(1)
    
    config = {}
    data = r.get('hfs:system:config')
    if data:
        config = json.loads(data)
    
    config['code_source'] = source
    if source == 'git':
        config['git_url'] = git_url
        config['git_branch'] = git_branch
        if git_token:
            config['git_token'] = git_token
        if git_ref:
            config['git_ref'] = git_ref
        else:
            config.pop('git_ref', None)
    else:
        config.pop('git_url', None)
        config.pop('git_token', None)
        config.pop('git_branch', None)
        config.pop('git_ref', None)
    
    r.set('hfs:system:config', json.dumps(config))
    
    click.echo(f"✅ 代码来源已设置: {source}")
    if source == 'git':
        click.echo(f"   Git URL: {git_url}")
        click.echo(f"   Git Token: {'***' if git_token else '(未设置)'}")
        click.echo(f"   Git Branch: {git_branch}")
        if git_ref:
            click.echo(f"   Git Ref: {git_ref}")
        else:
            click.echo(f"   Git Ref: (自动使用 {git_branch}/* 最新 tag)")


@system.command('show')
@click.pass_context
def show_system_config(ctx):
    """显示系统配置"""
    r = ctx.obj['redis']
    
    data = r.get('hfs:system:config')
    if data:
        config = json.loads(data)
        click.echo("系统配置:")
        click.echo(f"  code_source: {config.get('code_source', 'local')}")
        if config.get('git_url'):
            click.echo(f"  git_url: {config.get('git_url')}")
        if config.get('git_branch'):
            click.echo(f"  git_branch: {config.get('git_branch')}")
        if config.get('git_ref'):
            click.echo(f"  git_ref: {config.get('git_ref')}")
    else:
        click.echo("系统配置: (默认)")
        click.echo("  code_source: local")


cli.add_command(system)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='预览不执行')
@click.pass_context
def import_config(ctx, config_file, dry_run):
    """从 YAML 配置文件导入账号和项目"""
    r = ctx.obj['redis']
    
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    # 导入账号
    accounts = config.get('accounts', {}).get('pool', [])
    click.echo(f"\n📦 Found {len(accounts)} accounts")
    
    for acc in accounts:
        username = acc['username']
        if dry_run:
            click.echo(f"  [DRY-RUN] Would import: {username}")
        else:
            # 使用 String+JSON 格式，key 前缀为 hfs:account:
            account_data = {
                'username': username,
                'token': acc['token'],
                'email': acc.get('email', ''),
                'score': acc.get('score', 100),
                'status': acc.get('status', 'active'),
                'max_spaces': acc.get('max_spaces', 3),
                'created_at': int(time.time())
            }
            r.set(f'hfs:account:{username}', json.dumps(account_data))
            click.echo(f"  ✓ Imported: {username}")
    
    # 导入账号策略
    policy = config.get('accounts', {}).get('policy', {})
    if policy and not dry_run:
        r.set('hfs:config:account_policy', json.dumps(policy))
        click.echo(f"\n✓ Imported account policy")
    
    # 导入项目
    projects = config.get('projects', [])
    click.echo(f"\n📦 Found {len(projects)} projects")
    
    for proj in projects:
        project_id = proj['id']
        if dry_run:
            click.echo(f"  [DRY-RUN] Would import: {project_id}")
        else:
            # 保存项目配置（使用 String+JSON 格式）
            project_data = {
                'id': project_id,
                'scene': proj.get('scene', 'production'),
                'description': proj.get('description', ''),
                'config': proj.get('config', {}),
                'nodes': proj.get('nodes', {}),
                'accounts': proj.get('accounts', {}),
                'created_at': int(time.time())
            }
            r.set(f'hfs:project:{project_id}', json.dumps(project_data))
            click.echo(f"  ✓ Imported: {project_id}")
            
            # 初始化节点（使用 String+JSON 格式，project_id 字段）
            node_ids = proj.get('nodes', {}).get('ids', [])
            for node_id in node_ids:
                node_data = {
                    'id': node_id,
                    'project_id': project_id,
                    'status': 'idle',
                    'space': '',
                    'created_at': int(time.time()),
                    'updated_at': int(time.time())
                }
                r.set(f'hfs:node:{project_id}:{node_id}', json.dumps(node_data))
            if node_ids:
                click.echo(f"    ✓ Initialized {len(node_ids)} nodes")
    
    # 导入自定义场景
    scenes = config.get('scenes', {})
    if scenes and not dry_run:
        for scene_name, scene_config in scenes.items():
            r.hset('hfs:config:scenes', scene_name, json.dumps(scene_config))
        click.echo(f"\n✓ Imported {len(scenes)} custom scenes")
    
    # 导入健康检查配置
    health = config.get('health', {})
    if health and not dry_run:
        r.set('hfs:config:health', json.dumps(health))
        click.echo(f"\n✓ Imported health config")
    
    if dry_run:
        click.echo("\n[DRY-RUN] No changes made")
    else:
        click.echo("\n✅ Import completed")


@cli.command()
@click.argument('output_file', type=click.Path())
@click.pass_context
def export_config(ctx, output_file):
    """导出当前配置到 YAML 文件"""
    r = ctx.obj['redis']
    
    config = {
        'redis': {
            'url': 'redis://:password@host:port/db'
        },
        'accounts': {
            'pool': [],
            'policy': {}
        },
        'projects': [],
        'scenes': {},
        'health': {}
    }
    
    # 导出账号（使用 String+JSON 格式）
    for key in r.scan_iter('hfs:account:*'):
        acc_data_str = r.get(key)
        if acc_data_str:
            acc_data = json.loads(acc_data_str)
            config['accounts']['pool'].append({
                'username': acc_data.get('username'),
                'token': acc_data.get('token'),
                'email': acc_data.get('email', ''),
                'score': acc_data.get('score', 100),
                'status': acc_data.get('status', 'active'),
                'max_spaces': acc_data.get('max_spaces', 3)
            })
    
    # 导出账号策略
    policy_data = r.get('hfs:config:account_policy')
    if policy_data:
        config['accounts']['policy'] = json.loads(policy_data)
    
    # 导出项目（使用 String+JSON 格式）
    for key in r.scan_iter('hfs:project:*'):
        proj_data_str = r.get(key)
        if proj_data_str:
            proj_data = json.loads(proj_data_str)
            project = {
                'id': proj_data.get('id'),
                'scene': proj_data.get('scene', 'production'),
                'description': proj_data.get('description', ''),
                'config': proj_data.get('config', {}),
                'nodes': proj_data.get('nodes', {}),
                'accounts': proj_data.get('accounts', {})
            }
            config['projects'].append(project)
    
    # 导出自定义场景
    scenes_data = r.hgetall('hfs:config:scenes')
    if scenes_data:
        for scene_name, scene_config in scenes_data.items():
            config['scenes'][scene_name] = json.loads(scene_config)
    
    # 导出健康检查配置
    health_data = r.get('hfs:config:health')
    if health_data:
        config['health'] = json.loads(health_data)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    click.echo(f"✅ Exported to {output_file}")


@cli.command()
@click.pass_context
def show_config(ctx):
    """显示当前配置摘要"""
    r = ctx.obj['redis']
    
    # 账号统计
    total_accounts = 0
    active_accounts = 0
    for key in r.scan_iter('hfs:account:*'):
        if ':stats' in key:
            continue
        total_accounts += 1
        data = r.get(key)
        if data:
            acc = json.loads(data)
            if acc.get('status') == 'active':
                active_accounts += 1
    
    click.echo(f"\n📊 Configuration Summary\n")
    click.echo(f"Accounts: {active_accounts}/{total_accounts} active")
    
    # 项目统计
    projects = []
    for key in r.scan_iter('hfs:project:*'):
        if ':stats' in key or ':accounts' in key:
            continue
        data = r.get(key)
        if data:
            proj = json.loads(data)
            projects.append(proj)
    
    click.echo(f"Projects: {len(projects)}")
    
    for proj in projects:
        project_id = proj.get('id')
        scene = proj.get('scene', 'production')
        
        # Count nodes
        node_count = 0
        for node_key in r.scan_iter(f'hfs:node:{project_id}:*'):
            node_count += 1
        
        click.echo(f"  - {project_id}: {scene} ({node_count} nodes)")
    
    # 自定义场景
    scenes = r.hgetall('hfs:config:scenes')
    if scenes:
        click.echo(f"\nCustom Scenes: {len(scenes)}")
        for scene_name in scenes.keys():
            click.echo(f"  - {scene_name}")


@cli.command('config-set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set configuration value"""
    r = ctx.obj['redis']
    
    # Parse nested key (e.g., "account_policy.score_decay.on_failure")
    parts = key.split('.')
    
    if len(parts) == 1:
        # Simple key
        r.set(f'hfs:config:{key}', value)
        click.echo(f"✅ Set {key} = {value}")
    else:
        # Nested key
        config_key = f'hfs:config:{parts[0]}'
        data = r.get(config_key)
        
        if data:
            config = json.loads(data)
        else:
            config = {}
        
        # Navigate to nested location
        current = config
        for part in parts[1:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Try to parse value as JSON
        try:
            parsed_value = json.loads(value)
        except:
            parsed_value = value
        
        # Set value
        current[parts[-1]] = parsed_value
        
        r.set(config_key, json.dumps(config))
        click.echo(f"✅ Set {key} = {parsed_value}")


@cli.command('config-get')
@click.argument('key')
@click.pass_context
def config_get(ctx, key):
    """Get configuration value"""
    r = ctx.obj['redis']
    
    # Parse nested key
    parts = key.split('.')
    
    if len(parts) == 1:
        # Simple key
        value = r.get(f'hfs:config:{key}')
        if value:
            click.echo(value)
        else:
            click.echo(f"Key not found: {key}", err=True)
            ctx.exit(1)
    else:
        # Nested key
        config_key = f'hfs:config:{parts[0]}'
        data = r.get(config_key)
        
        if not data:
            click.echo(f"Config not found: {parts[0]}", err=True)
            ctx.exit(1)
        
        config = json.loads(data)
        
        # Navigate to nested location
        current = config
        for part in parts[1:]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                click.echo(f"Key not found: {key}", err=True)
                ctx.exit(1)
        
        # Output value
        if isinstance(current, (dict, list)):
            click.echo(json.dumps(current, indent=2))
        else:
            click.echo(current)


if __name__ == '__main__':
    cli()
