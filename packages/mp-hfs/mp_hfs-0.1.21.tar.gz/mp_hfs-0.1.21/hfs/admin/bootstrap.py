"""Bootstrap commands for system initialization"""
import click
import json
import time


@click.group()
def bootstrap():
    """System bootstrap and initialization commands"""
    pass


@bootstrap.command('system')
@click.option('--config', type=click.Path(exists=True), help='Config file to bootstrap from')
@click.pass_context
def bootstrap_system(ctx, config):
    """Bootstrap entire system from config file"""
    r = ctx.obj['redis']
    
    if not config:
        click.echo("Error: --config required for system bootstrap", err=True)
        ctx.exit(1)
    
    import yaml
    with open(config) as f:
        cfg = yaml.safe_load(f)
    
    click.echo("\n🚀 Bootstrapping system...\n")
    
    # Import accounts
    accounts = cfg.get('accounts', {}).get('pool', [])
    if accounts:
        click.echo(f"📦 Importing {len(accounts)} accounts...")
        for acc in accounts:
            key = f'hfs:account:{acc["username"]}'
            if r.exists(key):
                click.echo(f"   ⚠️  Account exists: {acc['username']}")
            else:
                account_data = {
                    'username': acc['username'],
                    'token': acc['token'],
                    'status': acc.get('status', 'active'),
                    'max_spaces': acc.get('max_spaces', 6),
                    'max_spaces_per_project': acc.get('max_spaces_per_project', 4),
                    'created_at': int(time.time())
                }
                if acc.get('email'):
                    account_data['email'] = acc['email']
                r.set(key, json.dumps(account_data))
                click.echo(f"   ✓ Created: {acc['username']}")
    
    # Import projects
    projects = cfg.get('projects', [])
    if projects:
        click.echo(f"\n📦 Importing {len(projects)} projects...")
        for proj in projects:
            _create_project(r, proj)
    
    # Import policies
    policy = cfg.get('accounts', {}).get('policy', {})
    if policy:
        r.set('hfs:config:account_policy', json.dumps(policy))
        click.echo(f"\n✓ Imported account policy")
    
    # Import health config
    health = cfg.get('health', {})
    if health:
        r.set('hfs:config:health', json.dumps(health))
        click.echo(f"✓ Imported health config")
    
    # Import custom scenes
    scenes = cfg.get('scenes', {})
    if scenes:
        for scene_name, scene_config in scenes.items():
            r.hset('hfs:config:scenes', scene_name, json.dumps(scene_config))
        click.echo(f"✓ Imported {len(scenes)} custom scenes")
    
    click.echo(f"\n✅ System bootstrap complete!")


@bootstrap.command('project')
@click.argument('project_id')
@click.option('--config', type=click.Path(exists=True), help='Project config file')
@click.option('--no-reuse', is_flag=True, help='Force create new Space, skip reuse')
@click.pass_context
def bootstrap_project(ctx, project_id, config, no_reuse):
    """Bootstrap specific project - create first Space"""
    r = ctx.obj['redis']
    
    if config:
        # Bootstrap from config file
        import yaml
        with open(config) as f:
            proj = yaml.safe_load(f).get('project', {})
        
        if not proj.get('id'):
            proj['id'] = project_id
    else:
        # Bootstrap from existing project config
        proj_key = f'hfs:project:{project_id}'
        proj_data = r.get(proj_key)
        
        if not proj_data:
            click.echo(f"Project not found: {project_id}", err=True)
            ctx.exit(1)
        
        proj = json.loads(proj_data)
    
    click.echo(f"\n🚀 Bootstrapping project: {project_id}\n")
    
    # Ensure project exists
    _create_project(r, proj)
    
    # Find first idle node
    nodes = []
    for key in r.scan_iter(f'hfs:node:{project_id}:*'):
        data = r.get(key)
        if data:
            node = json.loads(data)
            nodes.append(node)
    
    if not nodes:
        click.echo("⚠️  No nodes found for project")
        return
    
    idle_node = None
    for node in nodes:
        if node.get('status') == 'idle':
            idle_node = node
            break
    
    if not idle_node:
        click.echo("⚠️  No idle nodes available")
        return
    
    click.echo(f"✓ Found idle node: {idle_node['id']}")
    
    # Create and deploy first Space
    click.echo(f"\n📦 Creating bootstrap Space...")
    
    from hfs.scheduler import Scheduler
    
    redis_url = ctx.obj['redis_url']
    scheduler = Scheduler(redis_url)
    
    # Create and deploy Space
    try:
        reuse = not no_reuse
        space_id, account = scheduler.create_and_deploy_space(
            project_id=project_id,
            node_id=idle_node['id'],
            reuse=reuse,
            urgent=True
        )
        
        if space_id:
            click.echo(f"✅ Bootstrap Space created: {space_id}")
            click.echo(f"   Account: {account}")
            click.echo(f"   Node: {idle_node['id']}")
            click.echo(f"\n⏳ Space is deploying, use 'stats show --project={project_id} --watch' to monitor")
        else:
            click.echo(f"❌ Failed to create Space")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        ctx.exit(1)


@bootstrap.command('status')
@click.pass_context
def bootstrap_status(ctx):
    """Check bootstrap status"""
    r = ctx.obj['redis']
    
    click.echo("\n📊 Bootstrap Status\n")
    
    # Check accounts
    account_count = 0
    for key in r.scan_iter('hfs:account:*'):
        if ':stats' not in key:
            account_count += 1
    
    click.echo(f"Accounts: {account_count}")
    
    # Check projects
    projects = []
    for key in r.scan_iter('hfs:project:*'):
        if ':stats' in key or ':accounts' in key:
            continue
        data = r.get(key)
        if data:
            proj = json.loads(data)
            project_id = proj.get('id')
            
            # Count nodes
            node_count = 0
            idle_count = 0
            for node_key in r.scan_iter(f'hfs:node:{project_id}:*'):
                node_count += 1
                node_data = r.get(node_key)
                if node_data:
                    node = json.loads(node_data)
                    if node.get('status') == 'idle':
                        idle_count += 1
            
            # Count running spaces
            running = 0
            for space_key in r.scan_iter('hfs:space:*'):
                space_data = r.get(space_key)
                if space_data:
                    space = json.loads(space_data)
                    if space.get('project_id') == project_id and space.get('status') == 'running':
                        running += 1
            
            projects.append({
                'id': project_id,
                'nodes': node_count,
                'idle': idle_count,
                'running': running
            })
    
    click.echo(f"Projects: {len(projects)}")
    for proj in projects:
        status = "✅" if proj['running'] > 0 else "⚠️"
        click.echo(f"  {status} {proj['id']}: {proj['nodes']} nodes ({proj['idle']} idle), {proj['running']} running")
    
    # Check if system is ready
    if account_count > 0 and len(projects) > 0:
        has_running = any(p['running'] > 0 for p in projects)
        if has_running:
            click.echo(f"\n✅ System is operational")
        else:
            click.echo(f"\n⚠️  System configured but no workers running")
    else:
        click.echo(f"\n❌ System not bootstrapped")


def _create_project(r, proj):
    """Helper to create project and nodes"""
    project_id = proj['id']
    
    # Create project
    proj_key = f'hfs:project:{project_id}'
    if r.exists(proj_key):
        click.echo(f"   ⚠️  Project exists: {project_id}")
    else:
        project_data = {
            'id': project_id,
            'scene': proj.get('scene', 'production'),
            'created_at': int(time.time())
        }
        
        if proj.get('description'):
            project_data['description'] = proj['description']
        if proj.get('required_nodes'):
            project_data['required_nodes'] = proj['required_nodes']
        if proj.get('config'):
            project_data['config'] = proj['config']
        if proj.get('start_script'):
            project_data['start_script'] = proj['start_script']
        if proj.get('stop_script'):
            project_data['stop_script'] = proj['stop_script']
        
        r.set(proj_key, json.dumps(project_data))
        click.echo(f"   ✓ Created project: {project_id}")
    
    # Create nodes
    nodes_config = proj.get('nodes', {})
    if isinstance(nodes_config, list):
        node_ids = nodes_config
    else:
        node_ids = nodes_config.get('ids', [])
        # Handle pattern-based node generation
        if nodes_config.get('pattern') and nodes_config.get('count'):
            pattern = nodes_config['pattern']
            count = nodes_config['count']
            node_ids = [pattern.replace('{num}', str(i)) for i in range(1, count + 1)]
    
    # 如果没有配置 nodes，使用默认规则：{project_id}-{num}
    if not node_ids:
        required_nodes = proj.get('required_nodes', proj.get('min_nodes', 1))
        node_ids = [f'{project_id}-{i}' for i in range(1, required_nodes + 1)]
        click.echo(f"   ℹ️  No nodes configured, using default: {node_ids}")
    
    if node_ids:
        created = 0
        for node_id in node_ids:
            node_key = f'hfs:node:{project_id}:{node_id}'
            if not r.exists(node_key):
                node_data = {
                    'id': node_id,
                    'project_id': project_id,
                    'status': 'idle',
                    'space': '',
                    'created_at': int(time.time()),
                    'updated_at': int(time.time())
                }
                r.set(node_key, json.dumps(node_data))
                created += 1
        
        if created > 0:
            click.echo(f"   ✓ Created {created} nodes")
        
        # 更新项目配置中的 nodes 列表（供调度器使用）
        proj_data = r.get(proj_key)
        if proj_data:
            project = json.loads(proj_data)
            project['nodes'] = node_ids
            r.set(proj_key, json.dumps(project))
            click.echo(f"   ✓ Updated project nodes list")
