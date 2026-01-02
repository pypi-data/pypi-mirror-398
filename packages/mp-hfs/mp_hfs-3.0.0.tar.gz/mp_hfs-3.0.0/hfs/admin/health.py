"""Health check commands"""
import click
import json
import time
from tabulate import tabulate


@click.group()
def health():
    """Health check and diagnostics commands"""
    pass


@health.command('check')
@click.option('--fix', is_flag=True, help='Automatically fix issues')
@click.option('--project', help='Check specific project only')
@click.pass_context
def check(ctx, fix, project):
    """Run health checks"""
    r = ctx.obj['redis']
    
    from hfs.health import validate_consistency
    
    # Get projects to check
    if project:
        projects = [project]
    else:
        projects = []
        for key in r.scan_iter('hfs:project:*'):
            if ':stats' in key or ':accounts' in key or ':spaces:' in key:
                continue
            data = r.get(key)
            if data:
                proj = json.loads(data)
                projects.append(proj.get('id'))
    
    click.echo(f"\n🔍 Running health checks on {len(projects)} project(s)...\n")
    
    total_issues = 0
    fixed_issues = 0
    
    for proj_id in projects:
        issues = validate_consistency(r, proj_id)
        
        if issues:
            click.echo(f"❌ {proj_id}: {len(issues)} issue(s) found")
            for issue in issues:
                click.echo(f"   - {issue}")
                total_issues += 1
            
            if fix:
                click.echo(f"   🔧 Attempting to fix...")
                # Auto-fix logic would go here
                # For now, just report
                click.echo(f"   ⚠️  Auto-fix not yet implemented")
        else:
            click.echo(f"✅ {proj_id}: No issues")
    
    click.echo(f"\n📊 Summary: {total_issues} issue(s) found")
    
    if total_issues > 0 and not fix:
        click.echo("   Use --fix to attempt automatic fixes")


@health.command('report')
@click.pass_context
def report(ctx):
    """Show health status summary"""
    r = ctx.obj['redis']
    
    click.echo("\n🏥 System Health Report\n")
    
    # Count entities
    account_count = 0
    active_accounts = 0
    for key in r.scan_iter('hfs:account:*'):
        if ':stats' in key:
            continue
        account_count += 1
        data = r.get(key)
        if data:
            acc = json.loads(data)
            if acc.get('status') == 'active':
                active_accounts += 1
    
    project_count = 0
    for key in r.scan_iter('hfs:project:*'):
        if ':stats' in key or ':accounts' in key:
            continue
        project_count += 1
    
    node_count = 0
    idle_nodes = 0
    for key in r.scan_iter('hfs:node:*'):
        node_count += 1
        data = r.get(key)
        if data:
            node = json.loads(data)
            if node.get('status') == 'idle':
                idle_nodes += 1
    
    space_count = 0
    running_spaces = 0
    failed_spaces = 0
    for key in r.scan_iter('hfs:space:*'):
        space_count += 1
        data = r.get(key)
        if data:
            space = json.loads(data)
            status = space.get('status')
            if status == 'running':
                running_spaces += 1
            elif status == 'failed':
                failed_spaces += 1
    
    # Display summary
    click.echo(f"📦 Resources:")
    click.echo(f"   Accounts: {active_accounts}/{account_count} active")
    click.echo(f"   Projects: {project_count}")
    click.echo(f"   Nodes: {node_count} ({idle_nodes} idle)")
    click.echo(f"   Spaces: {space_count} ({running_spaces} running, {failed_spaces} failed)")
    
    # Check for issues
    click.echo(f"\n🔍 Quick Checks:")
    
    issues = []
    
    if failed_spaces > 0:
        issues.append(f"⚠️  {failed_spaces} failed space(s)")
    
    if idle_nodes > node_count * 0.5:
        issues.append(f"⚠️  High idle node ratio ({idle_nodes}/{node_count})")
    
    # Check for stale heartbeats
    now = int(time.time())
    stale_count = 0
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if data:
            space = json.loads(data)
            if space.get('status') == 'running':
                last_hb = space.get('last_heartbeat', 0)
                if now - last_hb > 300:  # 5 minutes
                    stale_count += 1
    
    if stale_count > 0:
        issues.append(f"⚠️  {stale_count} space(s) with stale heartbeat (>5min)")
    
    if issues:
        for issue in issues:
            click.echo(f"   {issue}")
    else:
        click.echo(f"   ✅ No issues detected")


@health.command('orphans')
@click.option('--cleanup', is_flag=True, help='Clean up orphaned resources')
@click.pass_context
def orphans(ctx, cleanup):
    """Find orphaned resources"""
    r = ctx.obj['redis']
    
    click.echo("\n🔍 Scanning for orphaned resources...\n")
    
    orphans = []
    
    # Find spaces without nodes
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if data:
            space = json.loads(data)
            space_id = space.get('id')
            node_id = space.get('node_id')
            status = space.get('status')
            
            # If space claims to be bound but node doesn't exist or doesn't point back
            if node_id and status in ('running', 'starting', 'draining'):
                project_id = space.get('project_id')
                node_key = f'hfs:node:{project_id}:{node_id}'
                node_data = r.get(node_key)
                
                if not node_data:
                    orphans.append({
                        'type': 'space_no_node',
                        'space_id': space_id,
                        'node_id': node_id,
                        'status': status
                    })
                else:
                    node = json.loads(node_data)
                    node_space = node.get('space_id') or node.get('space')
                    if node_space != space_id:
                        orphans.append({
                            'type': 'space_node_mismatch',
                            'space_id': space_id,
                            'node_id': node_id,
                            'node_space': node_space
                        })
    
    # Find nodes with non-existent spaces
    for key in r.scan_iter('hfs:node:*'):
        data = r.get(key)
        if data:
            node = json.loads(data)
            node_id = node.get('id')
            project_id = node.get('project_id')
            space_id = node.get('space_id') or node.get('space')
            
            if space_id:
                space_key = f'hfs:space:{space_id}'
                if not r.exists(space_key):
                    orphans.append({
                        'type': 'node_no_space',
                        'node_id': f"{project_id}:{node_id}",
                        'space_id': space_id
                    })
    
    if orphans:
        click.echo(f"Found {len(orphans)} orphaned resource(s):\n")
        
        for orphan in orphans:
            if orphan['type'] == 'space_no_node':
                click.echo(f"❌ Space {orphan['space_id']} ({orphan['status']}) → node {orphan['node_id']} doesn't exist")
            elif orphan['type'] == 'space_node_mismatch':
                click.echo(f"❌ Space {orphan['space_id']} → node {orphan['node_id']} points to {orphan['node_space']}")
            elif orphan['type'] == 'node_no_space':
                click.echo(f"❌ Node {orphan['node_id']} → space {orphan['space_id']} doesn't exist")
        
        if cleanup:
            click.echo(f"\n🔧 Cleaning up...")
            cleaned = 0
            
            for orphan in orphans:
                if orphan['type'] == 'space_no_node':
                    # Unbind space from non-existent node
                    space_key = f'hfs:space:{orphan["space_id"]}'
                    data = r.get(space_key)
                    if data:
                        space = json.loads(data)
                        space['node_id'] = ''
                        space['node_id'] = ''
                        space['status'] = 'failed'
                        r.set(space_key, json.dumps(space))
                        cleaned += 1
                        click.echo(f"   ✓ Unbound space {orphan['space_id']}")
                
                elif orphan['type'] == 'node_no_space':
                    # Clear node's space reference
                    parts = orphan['node_id'].split(':')
                    if len(parts) == 2:
                        node_key = f'hfs:node:{parts[0]}:{parts[1]}'
                        data = r.get(node_key)
                        if data:
                            node = json.loads(data)
                            node['space_id'] = ''
                            node['status'] = 'idle'
                            r.set(node_key, json.dumps(node))
                            cleaned += 1
                            click.echo(f"   ✓ Cleared node {orphan['node_id']}")
            
            click.echo(f"\n✅ Cleaned {cleaned} orphan(s)")
        else:
            click.echo(f"\nUse --cleanup to fix these issues")
    else:
        click.echo("✅ No orphaned resources found")


@health.command('stuck-nodes')
@click.option('--reset', is_flag=True, help='Reset stuck nodes')
@click.pass_context
def stuck_nodes(ctx, reset):
    """Find and reset stuck nodes"""
    r = ctx.obj['redis']
    
    click.echo("\n🔍 Scanning for stuck nodes...\n")
    
    now = int(time.time())
    stuck = []
    
    for key in r.scan_iter('hfs:node:*'):
        data = r.get(key)
        if data:
            node = json.loads(data)
            node_id = node.get('id')
            project_id = node.get('project_id')
            status = node.get('status')
            space_id = node.get('space_id') or node.get('space')
            
            # Node is pending but space is not starting/running
            if status == 'pending' and space_id:
                space_key = f'hfs:space:{space_id}'
                space_data = r.get(space_key)
                
                if space_data:
                    space = json.loads(space_data)
                    space_status = space.get('status')
                    
                    # Stuck if space is failed/exited but node still pending
                    if space_status in ('failed', 'exited', 'unusable'):
                        stuck.append({
                            'node_id': f"{project_id}:{node_id}",
                            'space_id': space_id,
                            'space_status': space_status
                        })
    
    if stuck:
        click.echo(f"Found {len(stuck)} stuck node(s):\n")
        
        for item in stuck:
            click.echo(f"❌ Node {item['node_id']} → space {item['space_id']} ({item['space_status']})")
        
        if reset:
            click.echo(f"\n🔧 Resetting stuck nodes...")
            
            for item in stuck:
                parts = item['node_id'].split(':')
                if len(parts) == 2:
                    node_key = f'hfs:node:{parts[0]}:{parts[1]}'
                    data = r.get(node_key)
                    if data:
                        node = json.loads(data)
                        node['space_id'] = ''
                        node['status'] = 'idle'
                        node['updated_at'] = now
                        r.set(node_key, json.dumps(node))
                        click.echo(f"   ✓ Reset {item['node_id']}")
            
            click.echo(f"\n✅ Reset {len(stuck)} node(s)")
        else:
            click.echo(f"\nUse --reset to fix these nodes")
    else:
        click.echo("✅ No stuck nodes found")
