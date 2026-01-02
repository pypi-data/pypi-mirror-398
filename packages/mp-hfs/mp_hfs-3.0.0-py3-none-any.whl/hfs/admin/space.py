"""Space management commands"""
import click
import json
import time
from tabulate import tabulate


@click.group()
def space():
    """Space management commands"""
    pass


@space.command('list')
@click.option('--project', help='Filter by project')
@click.option('--status', help='Filter by status')
@click.pass_context
def list_spaces(ctx, project, status):
    """List all spaces"""
    r = ctx.obj['redis']
    
    # 收集所有 space keys
    keys = [k for k in r.scan_iter('hfs:space:*')]
    if not keys:
        click.echo("No spaces found")
        return
    
    # Pipeline 批量获取
    pipe = r.pipeline()
    for key in keys:
        pipe.get(key)
    results = pipe.execute()
    
    spaces = []
    for data in results:
        if not data:
            continue
        sp = json.loads(data)
        
        # Filter by project
        space_project = sp.get('project_id') or sp.get('project', '')
        if project and space_project != project:
            continue
        
        # Filter by status
        space_status = sp.get('status', '')
        if status and space_status != status:
            continue
        
        # Calculate runtime
        runtime = '-'
        if sp.get('started_at') and space_status in ('running', 'draining'):
            runtime_sec = int(time.time() - sp['started_at'])
            runtime = f"{runtime_sec/3600:.1f}h"
        
        # Last heartbeat
        hb = '-'
        if sp.get('last_heartbeat'):
            elapsed = int(time.time() - sp['last_heartbeat'])
            hb = f"{elapsed}s"
        
        spaces.append([
            sp.get('id', '')[:35],
            space_project,
            space_status,
            sp.get('node_id') or sp.get('node', '-'),
            runtime,
            hb
        ])
    
    if spaces:
        click.echo(tabulate(spaces, headers=['Space ID', 'Project', 'Status', 'Node', 'Runtime', 'Last HB']))
    else:
        click.echo("No spaces found")


@space.command('show')
@click.argument('space_id')
@click.pass_context
def show_space(ctx, space_id):
    """Show space details"""
    r = ctx.obj['redis']
    
    key = f'hfs:space:{space_id}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Space not found: {space_id}", err=True)
        ctx.exit(1)
    
    sp = json.loads(data)
    
    click.echo(f"\n📋 Space: {space_id}\n")
    click.echo(f"Status: {sp.get('status', '?')}")
    click.echo(f"Project: {sp.get('project_id') or sp.get('project', '-')}")
    click.echo(f"Node: {sp.get('node_id') or sp.get('node', '-')}")
    click.echo(f"Account: {sp.get('account', '-')}")
    click.echo(f"Mode: {sp.get('mode', 'managed')}")
    
    if sp.get('instance_id'):
        click.echo(f"Instance: {sp.get('instance_id')}")
    
    # Timing info
    click.echo(f"\n⏱️  Timing:")
    
    if sp.get('created_at'):
        click.echo(f"   Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sp['created_at']))}")
    
    if sp.get('started_at'):
        runtime = int(time.time() - sp['started_at'])
        click.echo(f"   Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sp['started_at']))}")
        click.echo(f"   Runtime: {runtime}s ({runtime/3600:.1f}h)")
        
        if sp.get('run_timeout'):
            timeout = sp['run_timeout']
            remaining = timeout - runtime
            click.echo(f"   Timeout: {timeout}s ({timeout/3600:.1f}h)")
            click.echo(f"   Remaining: {remaining}s ({remaining/3600:.1f}h)")
    
    if sp.get('last_heartbeat'):
        elapsed = int(time.time() - sp['last_heartbeat'])
        click.echo(f"   Last heartbeat: {elapsed}s ago")
    
    if sp.get('updated_at'):
        click.echo(f"   Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sp['updated_at']))}")
    
    # HF status
    if sp.get('hf_status'):
        click.echo(f"\n🤗 HuggingFace Status: {sp.get('hf_status')}")


@space.command('delete')
@click.argument('space_id')
@click.option('--force', is_flag=True, help='Force delete even if running')
@click.pass_context
def delete_space(ctx, space_id, force):
    """Delete space from Redis"""
    r = ctx.obj['redis']
    
    key = f'hfs:space:{space_id}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Space not found: {space_id}", err=True)
        ctx.exit(1)
    
    sp = json.loads(data)
    status = sp.get('status', '')
    
    # Check if running
    if status in ('running', 'starting', 'draining') and not force:
        click.echo(f"Space is {status}, cannot delete", err=True)
        click.echo("Use --force to delete anyway", err=True)
        ctx.exit(1)
    
    # Check if bound to node
    node_id = sp.get('node_id') or sp.get('node', '')
    if node_id:
        click.echo(f"⚠️  Warning: Space is bound to node {node_id}")
        if not force:
            click.echo("Use --force to delete anyway", err=True)
            ctx.exit(1)
    
    r.delete(key)
    
    click.echo(f"✅ Deleted space: {space_id}")
    
    if node_id:
        click.echo(f"   ⚠️  Note: Node binding not cleared, use 'node reset' if needed")


@space.command('cleanup')
@click.option('--dry-run', is_flag=True, help='Preview without deleting')
@click.option('--age', default=86400, help='Delete spaces older than AGE seconds (default: 24h)')
@click.option('--status', multiple=True, help='Only cleanup spaces with this status (can specify multiple)')
@click.pass_context
def cleanup_spaces(ctx, dry_run, age, status):
    """Cleanup old spaces"""
    r = ctx.obj['redis']
    
    now = int(time.time())
    cutoff = now - age
    
    # Default to cleanup exited/failed/unusable
    if not status:
        status = ('exited', 'failed', 'unusable')
    
    click.echo(f"\n🔍 Scanning for spaces to cleanup...")
    click.echo(f"   Age threshold: {age}s ({age/3600:.1f}h)")
    click.echo(f"   Status filter: {', '.join(status)}\n")
    
    candidates = []
    
    for key in r.scan_iter('hfs:space:*'):
        data = r.get(key)
        if data:
            space = json.loads(data)
            space_id = space.get('id')
            space_status = space.get('status')
            updated_at = space.get('updated_at', 0)
            
            # Check status filter
            if space_status not in status:
                continue
            
            # Check age
            if updated_at > cutoff:
                continue
            
            # Check not bound to node
            node_id = space.get('node_id') or space.get('node', '')
            if node_id:
                continue
            
            age_hours = (now - updated_at) / 3600
            candidates.append({
                'id': space_id,
                'status': space_status,
                'age': age_hours
            })
    
    if candidates:
        click.echo(f"Found {len(candidates)} space(s) to cleanup:\n")
        
        for space in candidates[:10]:
            click.echo(f"   {space['id']:40} {space['status']:10} {space['age']:.1f}h old")
        
        if len(candidates) > 10:
            click.echo(f"   ... and {len(candidates) - 10} more")
        
        if dry_run:
            click.echo(f"\n[DRY-RUN] Would delete {len(candidates)} space(s)")
        else:
            click.echo(f"\n🗑️  Deleting {len(candidates)} space(s)...")
            
            deleted = 0
            for space in candidates:
                key = f'hfs:space:{space["id"]}'
                r.delete(key)
                deleted += 1
            
            click.echo(f"✅ Deleted {deleted} space(s)")
    else:
        click.echo("✅ No spaces to cleanup")


@space.command('unbind')
@click.argument('space_id')
@click.pass_context
def unbind_space(ctx, space_id):
    """Unbind space from node"""
    r = ctx.obj['redis']
    
    key = f'hfs:space:{space_id}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Space not found: {space_id}", err=True)
        ctx.exit(1)
    
    space = json.loads(data)
    node_id = space.get('node_id') or space.get('node', '')
    project_id = space.get('project_id') or space.get('project', '')
    
    if not node_id:
        click.echo(f"Space is not bound to any node")
        return
    
    # Unbind space
    space['node_id'] = ''
    space['updated_at'] = int(time.time())
    r.set(key, json.dumps(space))
    
    # Unbind node
    if project_id and node_id:
        node_key = f'hfs:node:{project_id}:{node_id}'
        node_data = r.get(node_key)
        if node_data:
            node = json.loads(node_data)
            node['space_id'] = ''
            node['status'] = 'idle'
            node['updated_at'] = int(time.time())
            r.set(node_key, json.dumps(node))
            click.echo(f"✅ Unbound space from node: {project_id}:{node_id}")
        else:
            click.echo(f"✅ Unbound space (node not found: {project_id}:{node_id})")
    else:
        click.echo(f"✅ Unbound space")
