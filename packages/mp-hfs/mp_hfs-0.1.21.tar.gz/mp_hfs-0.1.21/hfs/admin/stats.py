"""Statistics and monitoring commands"""
import click
import json
import time
from tabulate import tabulate


@click.group()
def stats():
    """Statistics and monitoring commands"""
    pass


@stats.command('show')
@click.option('--project', help='Show stats for specific project')
@click.option('--accounts', is_flag=True, help='Show account statistics')
@click.option('--watch', is_flag=True, help='Watch mode (refresh every interval)')
@click.option('--interval', default=5, help='Watch interval in seconds')
@click.pass_context
def show_stats(ctx, project, accounts, watch, interval):
    """Show system statistics"""
    r = ctx.obj['redis']
    
    if watch:
        import os
        try:
            while True:
                os.system('clear' if os.name != 'nt' else 'cls')
                _display_stats(r, project, accounts)
                click.echo(f"\n⏱️  Refreshing every {interval}s... (Ctrl+C to stop)")
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo("\n\nStopped")
    else:
        _display_stats(r, project, accounts)


def _display_stats(r, project_filter, show_accounts):
    """Display statistics"""
    
    if show_accounts:
        _display_account_stats(r)
    elif project_filter:
        _display_project_stats(r, project_filter)
    else:
        _display_system_stats(r)


def _display_system_stats(r):
    """Display system-wide statistics"""
    
    click.echo(f"\n📊 System Statistics - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Overall counts
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
    
    total_projects = 0
    for key in r.scan_iter('hfs:project:*'):
        if ':stats' in key or ':accounts' in key:
            continue
        total_projects += 1
    
    total_nodes = 0
    nodes_by_status = {'idle': 0, 'pending': 0, 'running': 0}
    for key in r.scan_iter('hfs:node:*'):
        total_nodes += 1
        data = r.get(key)
        if data:
            node = json.loads(data)
            status = node.get('status', 'idle')
            nodes_by_status[status] = nodes_by_status.get(status, 0) + 1
    
    total_spaces = 0
    spaces_by_status = {}
    for key in r.scan_iter('hfs:space:*'):
        total_spaces += 1
        data = r.get(key)
        if data:
            space = json.loads(data)
            status = space.get('status', 'unknown')
            spaces_by_status[status] = spaces_by_status.get(status, 0) + 1
    
    # Display
    click.echo(f"Accounts: {active_accounts}/{total_accounts} active")
    click.echo(f"Projects: {total_projects}")
    click.echo(f"Nodes: {total_nodes} (idle={nodes_by_status.get('idle', 0)}, pending={nodes_by_status.get('pending', 0)}, running={nodes_by_status.get('running', 0)})")
    click.echo(f"Spaces: {total_spaces}")
    
    # Space status breakdown
    if spaces_by_status:
        click.echo(f"\n📦 Space Status:")
        for status, count in sorted(spaces_by_status.items(), key=lambda x: -x[1]):
            click.echo(f"   {status:12} {count:3}")
    
    # Per-project summary
    click.echo(f"\n📋 Projects:")
    
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
            for node_key in r.scan_iter(f'hfs:node:{project_id}:*'):
                node_count += 1
            
            # Count running spaces
            running = 0
            for space_key in r.scan_iter('hfs:space:*'):
                space_data = r.get(space_key)
                if space_data:
                    space = json.loads(space_data)
                    if space.get('project_id') == project_id and space.get('status') == 'running':
                        running += 1
            
            projects.append([project_id, proj.get('scene', '-'), node_count, running])
    
    if projects:
        click.echo(tabulate(projects, headers=['Project', 'Scene', 'Nodes', 'Running']))


def _display_project_stats(r, project_id):
    """Display project-specific statistics"""
    
    click.echo(f"\n📊 Project Statistics: {project_id} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get project data
    proj_key = f'hfs:project:{project_id}'
    proj_data = r.get(proj_key)
    
    if not proj_data:
        click.echo(f"Project not found: {project_id}")
        return
    
    proj = json.loads(proj_data)
    
    click.echo(f"Scene: {proj.get('scene', 'production')}")
    
    # Node stats
    nodes = []
    for key in r.scan_iter(f'hfs:node:{project_id}:*'):
        data = r.get(key)
        if data:
            node = json.loads(data)
            nodes.append(node)
    
    click.echo(f"Nodes: {len(nodes)}")
    
    node_status_count = {}
    for node in nodes:
        status = node.get('status', 'idle')
        node_status_count[status] = node_status_count.get(status, 0) + 1
    
    for status, count in node_status_count.items():
        click.echo(f"   {status}: {count}")
    
    # Space stats
    spaces = []
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if data:
            space = json.loads(data)
            if space.get('project_id') == project_id:
                spaces.append(space)
    
    click.echo(f"\nSpaces: {len(spaces)}")
    
    space_status_count = {}
    for space in spaces:
        status = space.get('status', 'unknown')
        space_status_count[status] = space_status_count.get(status, 0) + 1
    
    for status, count in sorted(space_status_count.items()):
        click.echo(f"   {status}: {count}")
    
    # Project stats from Redis
    stats_key = f'hfs:project:{project_id}:stats'
    stats_data = r.get(stats_key)
    
    if stats_data:
        stats = json.loads(stats_data)
        
        click.echo(f"\n📈 Metrics:")
        
        if stats.get('last_space_created'):
            elapsed = int(time.time() - stats['last_space_created'])
            click.echo(f"   Last space created: {elapsed}s ago ({elapsed/3600:.1f}h)")
        
        today = stats.get('today', {})
        if today:
            click.echo(f"   Today: created={today.get('spaces_created', 0)}, failed={today.get('spaces_failed', 0)}, reused={today.get('spaces_reused', 0)}")


def _display_account_stats(r):
    """Display account statistics"""
    
    click.echo(f"\n📊 Account Statistics - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    accounts = []
    
    for key in r.scan_iter('hfs:account:*'):
        if ':stats' in key:
            continue
        
        data = r.get(key)
        if data:
            acc = json.loads(data)
            username = acc.get('username')
            
            # Count running spaces
            running = 0
            for space_key in r.scan_iter('hfs:space:*'):
                space_data = r.get(space_key)
                if space_data:
                    space = json.loads(space_data)
                    if space.get('account') == username and space.get('status') in ('running', 'starting'):
                        running += 1
            
            # Get stats
            stats_key = f"{key}:stats"
            stats_data = r.get(stats_key)
            
            created_today = 0
            failed_today = 0
            total_created = 0
            total_failed = 0
            
            if stats_data:
                stats = json.loads(stats_data)
                today = stats.get('today', {})
                created_today = today.get('spaces_created', 0)
                failed_today = today.get('spaces_failed', 0)
                
                total = stats.get('total', {})
                total_created = total.get('spaces_created', 0)
                total_failed = total.get('spaces_failed', 0)
            
            accounts.append([
                username,
                acc.get('status', 'active'),
                running,
                f"{created_today}/{failed_today}",
                f"{total_created}/{total_failed}"
            ])
    
    if accounts:
        click.echo(tabulate(accounts, headers=['Username', 'Status', 'Running', 'Today (C/F)', 'Total (C/F)']))
