"""Account management commands"""
import click
import json
import time
from tabulate import tabulate


@click.group()
def account():
    """Account management commands"""
    pass


@account.command('list')
@click.option('--status', help='Filter by status (active/cooldown/disabled)')
@click.pass_context
def list_accounts(ctx, status):
    """List all accounts"""
    r = ctx.obj['redis']
    
    # 收集所有 Space keys，Pipeline 批量获取
    space_keys = [k for k in r.scan_iter('hfs:space:*', count=500)]
    space_stats = {}  # {username: {'running': N, 'processing': M, 'idle': K, 'unusable': U}}
    
    if space_keys:
        pipe = r.pipeline()
        for k in space_keys:
            pipe.get(k)
        space_results = pipe.execute()
        
        for sdata in space_results:
            if not sdata:
                continue
            s = json.loads(sdata)
            space_id = s.get('id', '')
            if '/' in space_id:
                space_username = space_id.split('/')[0]
                if space_username not in space_stats:
                    space_stats[space_username] = {'running': 0, 'processing': 0, 'idle': 0, 'unusable': 0}
                
                space_status = s.get('status', '')
                if space_status == 'running':
                    space_stats[space_username]['running'] += 1
                elif space_status in ('starting', 'draining'):
                    space_stats[space_username]['processing'] += 1
                elif space_status in ('idle', 'exited', 'failed'):
                    space_stats[space_username]['idle'] += 1
                elif space_status == 'unusable':
                    space_stats[space_username]['unusable'] += 1
    
    # 收集账号 keys，Pipeline 批量获取
    acc_keys = [k for k in r.scan_iter('hfs:account:*', count=100) 
                if ':stats' not in (k.decode() if isinstance(k, bytes) else k)
                and ':spaces:' not in (k.decode() if isinstance(k, bytes) else k)]
    
    if not acc_keys:
        click.echo("No accounts found")
        return
    
    pipe = r.pipeline()
    for k in acc_keys:
        pipe.get(k)
    acc_results = pipe.execute()
    
    accounts = []
    for key, data in zip(acc_keys, acc_results):
        if not data:
            continue
        key_str = key.decode() if isinstance(key, bytes) else key
            
        acc = json.loads(data)
        username = acc.get('username', '')
        acc_status = acc.get('status', 'active')
        
        if status and acc_status != status:
            continue
        
        # Check cooldown
        cooldown_until = acc.get('cooldown_until', 0)
        if acc_status == 'cooldown' and cooldown_until <= time.time():
            acc_status = 'active'  # cooldown 已过期
            # 写回 Redis 恢复状态
            acc['status'] = 'active'
            r.set(key_str, json.dumps(acc))
        
        # 从预统计数据获取 Space 数量
        stats = space_stats.get(username, {'running': 0, 'processing': 0, 'idle': 0, 'unusable': 0})
        running = stats['running']
        processing = stats['processing']
        idle = stats['idle']
        unusable = stats['unusable']
        
        max_spaces = acc.get('max_spaces', 6)
        
        # Run/Proc/Idle 和 Max/Unusable
        rpi = f"{running}/{processing}/{idle}"
        mu = f"{max_spaces}/{unusable}"
        
        # 可用性判断：running + processing + idle < max
        active_count = running + processing + idle
        if acc_status == 'banned':
            available = "banned"
        elif acc_status == 'cooldown' and acc.get('cooldown_until', 0) > time.time():
            available = "cooldown"
        elif active_count >= max_spaces:
            available = "full"
        else:
            available = "✓"
        
        accounts.append([
            username,
            acc_status,
            rpi,
            mu,
            available,
        ])
    
    if accounts:
        click.echo(tabulate(accounts, headers=['Username', 'Status', 'Run/Proc/Idle', 'Max/Unusable', 'Avail']))
    else:
        click.echo("No accounts found")


@account.command('create')
@click.argument('token')
@click.option('--max-spaces', default=6, help='Maximum spaces per account')
@click.option('--max-daily-creates', default=10, help='Maximum daily creates')
@click.option('--max-spaces-per-project', default=3, help='Maximum spaces per project')
@click.pass_context
def create_account(ctx, token, max_spaces, max_daily_creates, max_spaces_per_project):
    """Create account (auto-fetch username from HuggingFace)"""
    r = ctx.obj['redis']
    
    # 从 HuggingFace 获取用户名
    try:
        from hfs.hf import whoami
        user_info = whoami(token)
        if not user_info:
            click.echo("Error: Failed to get username from token", err=True)
            ctx.exit(1)
        username = user_info.get('name')
        if not username:
            click.echo("Error: No username in token response", err=True)
            ctx.exit(1)
        click.echo(f"\n✅ Account created: {user_info}")
    except Exception as e:
        click.echo(f"Error: Failed to verify token: {e}", err=True)
        ctx.exit(1)
    
    # 检查账号是否已存在
    acc_key = f'hfs:account:{username}'
    if r.exists(acc_key):
        click.echo(f"Account already exists: {username}", err=True)
        click.echo("Use 'account update' to modify existing account", err=True)
        ctx.exit(1)
    
    # 创建账号
    account = {
        'id': username,
        'username': username,
        'token': token,
        'status': 'active',
        'max_spaces': max_spaces,
        'max_daily_creates': max_daily_creates,
        'max_spaces_per_project': max_spaces_per_project,
        'created_at': int(time.time()),
        'updated_at': int(time.time())
    }
    
    r.set(acc_key, json.dumps(account))
    r.sadd('hfs:accounts', username)
    
    click.echo(f"\n✅ Account created: {username}")
    click.echo(f"   Max Spaces: {max_spaces}")
    click.echo(f"   Max Daily Creates: {max_daily_creates}")
    click.echo(f"   Max Spaces per Project: {max_spaces_per_project}")


@account.command('show')
@click.argument('username')
@click.pass_context
def show_account(ctx, username):
    """Show account details"""
    r = ctx.obj['redis']
    
    key = f'hfs:account:{username}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Account not found: {username}", err=True)
        ctx.exit(1)
    
    acc = json.loads(data)
    
    click.echo(f"\n📋 Account: {username}\n")
    click.echo(f"Status: {acc.get('status', 'active')}")
    click.echo(f"Token: {acc.get('token', '')[:20]}...")
    click.echo(f"Max Spaces: {acc.get('max_spaces', 6)}")
    click.echo(f"Max Spaces per Project: {acc.get('max_spaces_per_project', 4)}")
    click.echo(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(acc.get('created_at', 0)))}")
    
    # Show stats if available
    stats_key = f"{key}:stats"
    stats_data = r.get(stats_key)
    if stats_data:
        stats = json.loads(stats_data)
        
        # Cooldown info
        cooldown = stats.get('cooldown', {})
        if cooldown.get('until', 0) > time.time():
            remaining = int(cooldown['until'] - time.time())
            click.echo(f"\n⏸️  Cooldown: {remaining}s remaining")
            click.echo(f"   Reason: {cooldown.get('reason', 'unknown')}")
            click.echo(f"   Count: {cooldown.get('count', 0)}")
        
        # Today's stats
        today = stats.get('today', {})
        if today:
            click.echo(f"\n📊 Today ({today.get('date', '-')})")
            click.echo(f"   Created: {today.get('spaces_created', 0)}")
            click.echo(f"   Failed: {today.get('spaces_failed', 0)}")
        
        # Total stats
        total = stats.get('total', {})
        if total:
            click.echo(f"\n📈 Total")
            click.echo(f"   Created: {total.get('spaces_created', 0)}")
            click.echo(f"   Failed: {total.get('spaces_failed', 0)}")
    
    # Count current spaces
    space_count = 0
    for space_key in r.scan_iter('hfs:space:*'):
        space_data = r.get(space_key)
        if space_data:
            space = json.loads(space_data)
            if space.get('account') == username and space.get('status') in ('running', 'starting'):
                space_count += 1
    
    click.echo(f"\n🚀 Current Running Spaces: {space_count}")


@account.command('update')
@click.argument('username', required=False)
@click.option('--status', help='Update status (active/banned/cooldown) - single account only')
@click.option('--max-spaces', type=int, help='Max concurrent spaces per account')
@click.option('--max-daily-creates', type=int, help='Max spaces created per day')
@click.option('--max-spaces-per-project', type=int, help='Max spaces per project per account')
@click.option('--token', help='Update token - single account only')
@click.option('-y', '--yes', is_flag=True, help='Skip confirmation for global update')
@click.pass_context
def update_account(ctx, username, status, max_spaces, max_daily_creates, max_spaces_per_project, token, yes):
    """Update account settings
    
    If USERNAME is specified, update single account.
    If USERNAME is omitted, update ALL accounts (only global options).
    
    Global options (can apply to all): --max-spaces, --max-daily-creates, --max-spaces-per-project
    Single-only options: --status, --token
    """
    r = ctx.obj['redis']
    
    # 检查是否有单账号专用选项
    single_only_options = []
    if status:
        single_only_options.append('--status')
    if token:
        single_only_options.append('--token')
    
    # 全局更新模式
    if not username:
        if single_only_options:
            click.echo(f"Error: {', '.join(single_only_options)} can only be used with specific USERNAME", err=True)
            ctx.exit(1)
        
        if not any([max_spaces, max_daily_creates, max_spaces_per_project]):
            click.echo("Error: No update options specified", err=True)
            ctx.exit(1)
        
        # 收集所有账号
        accounts = []
        for key in r.scan_iter('hfs:account:*', count=100):
            key_str = key.decode() if isinstance(key, bytes) else key
            if ':stats' in key_str:
                continue
            accounts.append(key_str)
        
        if not accounts:
            click.echo("No accounts found", err=True)
            ctx.exit(1)
        
        # 显示将要更新的内容
        updates = []
        if max_spaces:
            updates.append(f"max_spaces={max_spaces}")
        if max_daily_creates:
            updates.append(f"max_daily_creates={max_daily_creates}")
        if max_spaces_per_project:
            updates.append(f"max_spaces_per_project={max_spaces_per_project}")
        
        click.echo(f"⚠️  Will update ALL {len(accounts)} accounts: {', '.join(updates)}")
        
        if not yes:
            if not click.confirm("Confirm?"):
                click.echo("Cancelled")
                return
        
        # 执行更新
        for key in accounts:
            data = r.get(key)
            if not data:
                continue
            acc = json.loads(data)
            if max_spaces:
                acc['max_spaces'] = max_spaces
            if max_daily_creates:
                acc['max_daily_creates'] = max_daily_creates
            if max_spaces_per_project:
                acc['max_spaces_per_project'] = max_spaces_per_project
            acc['updated_at'] = int(time.time())
            r.set(key, json.dumps(acc))
        
        click.echo(f"✅ Updated {len(accounts)} accounts")
        return
    
    # 单账号更新模式
    key = f'hfs:account:{username}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Account not found: {username}", err=True)
        ctx.exit(1)
    
    acc = json.loads(data)
    updated = False
    
    if status:
        acc['status'] = status
        updated = True
        click.echo(f"✓ Updated status: {status}")
    
    if max_spaces:
        acc['max_spaces'] = max_spaces
        updated = True
        click.echo(f"✓ Updated max_spaces: {max_spaces}")
    
    if max_daily_creates:
        acc['max_daily_creates'] = max_daily_creates
        updated = True
        click.echo(f"✓ Updated max_daily_creates: {max_daily_creates}")
    
    if max_spaces_per_project:
        acc['max_spaces_per_project'] = max_spaces_per_project
        updated = True
        click.echo(f"✓ Updated max_spaces_per_project: {max_spaces_per_project}")
    
    if token:
        acc['token'] = token
        updated = True
        click.echo(f"✓ Updated token")
    
    if updated:
        acc['updated_at'] = int(time.time())
        r.set(key, json.dumps(acc))
        click.echo(f"\n✅ Account updated: {username}")
    else:
        click.echo("No changes specified")


@account.command('delete')
@click.argument('username')
@click.option('--force', is_flag=True, help='Force delete even if has spaces')
@click.pass_context
def delete_account(ctx, username, force):
    """Delete account"""
    r = ctx.obj['redis']
    
    key = f'hfs:account:{username}'
    if not r.exists(key):
        click.echo(f"Account not found: {username}", err=True)
        ctx.exit(1)
    
    # Check if account has spaces
    space_count = 0
    for skey in r.scan_iter(f'hfs:space:{username}/*', count=100):
        space_count += 1
    
    if space_count > 0 and not force:
        click.echo(f"Error: Account has {space_count} spaces", err=True)
        click.echo("Use --force to delete anyway", err=True)
        ctx.exit(1)
    
    r.delete(key)
    click.echo(f"✅ Deleted account: {username}")


@account.command('disable')
@click.argument('username')
@click.pass_context
def disable_account(ctx, username):
    """Disable account"""
    r = ctx.obj['redis']
    
    key = f'hfs:account:{username}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Account not found: {username}", err=True)
        ctx.exit(1)
    
    acc = json.loads(data)
    acc['status'] = 'disabled'
    r.set(key, json.dumps(acc))
    
    click.echo(f"✅ Disabled account: {username}")


@account.command('enable')
@click.argument('username')
@click.pass_context
def enable_account(ctx, username):
    """Enable account"""
    r = ctx.obj['redis']
    
    key = f'hfs:account:{username}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Account not found: {username}", err=True)
        ctx.exit(1)
    
    acc = json.loads(data)
    acc['status'] = 'active'
    r.set(key, json.dumps(acc))
    
    # Clear cooldown if any
    stats_key = f"{key}:stats"
    stats_data = r.get(stats_key)
    if stats_data:
        stats = json.loads(stats_data)
        if 'cooldown' in stats:
            stats['cooldown'] = {}
            r.set(stats_key, json.dumps(stats))
            click.echo("✓ Cleared cooldown")
    
    click.echo(f"✅ Enabled account: {username}")


@account.command('reset-score')
@click.argument('username')
@click.option('--score', default=100, help='New score value')
@click.pass_context
def reset_score(ctx, username, score):
    """Reset account score"""
    r = ctx.obj['redis']
    
    key = f'hfs:account:{username}'
    data = r.get(key)
    
    if not data:
        click.echo(f"Account not found: {username}", err=True)
        ctx.exit(1)
    
    acc = json.loads(data)
    old_score = acc.get('score', 100)
    acc['score'] = score
    r.set(key, json.dumps(acc))
    
    click.echo(f"✅ Reset score: {username}")
    click.echo(f"   {old_score} → {score}")
