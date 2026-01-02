"""Node management commands"""
import click
import json
import time
from tabulate import tabulate


@click.group()
def node():
    """Node management commands"""
    pass


@node.command('list')
@click.option('--project', help='Filter by project')
@click.option('--status', help='Filter by status (idle/pending/running)')
@click.pass_context
def list_nodes(ctx, project, status):
    """List all nodes"""
    r = ctx.obj['redis']
    
    pattern = f'hfs:node:{project}:*' if project else 'hfs:node:*'
    nodes = []
    
    for key in r.scan_iter(pattern):
        data = r.get(key)
        if data:
            node = json.loads(data)
            node_status = node.get('status', 'idle')
            
            if status and node_status != status:
                continue
            
            space_id = node.get('space_id') or node.get('space', '')
            
            # Get space status, runtime and timeout if bound
            space_status = '-'
            runtime = '-'
            timeout = '-'
            
            if space_id:
                space_key = f'hfs:space:{space_id}'
                space_data = r.get(space_key)
                if space_data:
                    space = json.loads(space_data)
                    space_status = space.get('status', '?')
                    
                    # Calculate runtime
                    if space.get('started_at'):
                        runtime_sec = int(time.time() - space['started_at'])
                        runtime = f"{runtime_sec/3600:.1f}h"
                    
                    # Get timeout
                    if space.get('run_timeout'):
                        timeout = f"{space['run_timeout']/3600:.1f}h"
            
            # Calculate status duration
            status_duration = '-'
            if node.get('updated_at'):
                duration_sec = int(time.time() - node['updated_at'])
                status_duration = f"{duration_sec/3600:.1f}h"
            
            nodes.append([
                node.get('project_id', ''),
                node.get('id', ''),
                node_status,
                status_duration,
                space_id[:25] if space_id else '-',
                space_status,
                runtime,
                timeout
            ])
    
    if nodes:
        click.echo(tabulate(nodes, headers=['Project', 'Node ID', 'Status', 'Duration', 'Space', 'Space Status', 'Runtime', 'Timeout']))
    else:
        click.echo("No nodes found")


@node.command('show')
@click.argument('project_id')
@click.argument('node_id')
@click.pass_context
def show_node(ctx, project_id, node_id):
    """Show node details"""
    r = ctx.obj['redis']
    
    key = f'hfs:node:{project_id}:{node_id}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Node not found: {project_id}:{node_id}", err=True)
        ctx.exit(1)
    
    node = json.loads(data)
    
    click.echo(f"\n📋 Node: {project_id}:{node_id}\n")
    click.echo(f"Status: {node.get('status', 'idle')}")
    
    space_id = node.get('space_id') or node.get('space', '')
    if space_id:
        click.echo(f"Space: {space_id}")
        
        # Show space details
        space_key = f'hfs:space:{space_id}'
        space_data = r.get(space_key)
        if space_data:
            space = json.loads(space_data)
            click.echo(f"  Status: {space.get('status', '?')}")
            click.echo(f"  Instance: {space.get('instance_id', '-')}")
            
            if space.get('last_heartbeat'):
                elapsed = int(time.time() - space['last_heartbeat'])
                click.echo(f"  Last heartbeat: {elapsed}s ago")
            
            if space.get('started_at'):
                runtime = int(time.time() - space['started_at'])
                click.echo(f"  Runtime: {runtime}s ({runtime/3600:.1f}h)")
    else:
        click.echo(f"Space: (none)")
    
    if node.get('updated_at'):
        click.echo(f"\nUpdated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(node['updated_at']))}")


@node.command('reset')
@click.argument('project_id')
@click.argument('node_id')
@click.pass_context
def reset_node(ctx, project_id, node_id):
    """Reset node to idle state"""
    r = ctx.obj['redis']
    
    key = f'hfs:node:{project_id}:{node_id}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Node not found: {project_id}:{node_id}", err=True)
        ctx.exit(1)
    
    node = json.loads(data)
    old_status = node.get('status', 'idle')
    old_space = node.get('space_id') or node.get('space', '')
    
    # Reset to idle
    node['status'] = 'idle'
    node['space_id'] = ''
    node['updated_at'] = int(time.time())
    
    r.set(key, json.dumps(node))
    
    click.echo(f"✅ Reset node: {project_id}:{node_id}")
    click.echo(f"   Status: {old_status} → idle")
    
    if old_space:
        click.echo(f"   Unbound space: {old_space}")
        click.echo(f"   ⚠️  Note: Space state not changed, only node binding cleared")


@node.command('reset-all')
@click.argument('project_id')
@click.option('--confirm', is_flag=True, help='Confirm reset all nodes')
@click.pass_context
def reset_all_nodes(ctx, project_id, confirm):
    """Reset all nodes in project to idle"""
    r = ctx.obj['redis']
    
    # Check project exists
    proj_key = f'hfs:project:{project_id}'
    if not r.exists(proj_key):
        click.echo(f"Project not found: {project_id}", err=True)
        ctx.exit(1)
    
    # Find all nodes
    nodes = []
    for key in r.scan_iter(f'hfs:node:{project_id}:*'):
        data = r.get(key)
        if data:
            node = json.loads(data)
            nodes.append((key, node))
    
    if not nodes:
        click.echo(f"No nodes found for project: {project_id}")
        return
    
    click.echo(f"Found {len(nodes)} nodes in {project_id}")
    
    if not confirm:
        click.echo("Use --confirm to reset all nodes")
        return
    
    # Reset all
    reset_count = 0
    for key, node in nodes:
        node['status'] = 'idle'
        node['space_id'] = ''
        node['updated_at'] = int(time.time())
        r.set(key, json.dumps(node))
        reset_count += 1
    
    click.echo(f"✅ Reset {reset_count} nodes in {project_id}")
