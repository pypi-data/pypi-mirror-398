"""Space 生命周期：创建、绑定、销毁"""
import json
import time
import random

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

from .account import set_cooldown


def create_space(r, account, project_id, node_id):
    """创建新 Space 并绑定到 Node"""
    api = HfApi(token=account['hf_token'])
    username = account.get('username') or api.whoami()['name']
    
    # 生成自然命名
    name = _generate_name()
    repo_id = f'{username}/{name}'
    space_id = f'{username}_{name}'
    
    print(f'[HFS] Creating space: {repo_id}')
    
    try:
        # 创建 Space (private)
        api.create_repo(repo_id, repo_type='space', space_sdk='gradio', private=True)
        print(f'[HFS] Created repo: {repo_id}')
    except HfHubHTTPError as e:
        error_msg = str(e)
        if '429' in error_msg or 'rate limit' in error_msg.lower():
            set_cooldown(r, account['id'], reason='rate_limited')
            raise Exception('Rate limit exceeded')
        raise
    
    # 记录到 Redis
    now = int(time.time())
    space = {
        'id': space_id,
        'repo_id': repo_id,
        'account': account['id'],
        'project_id': project_id,
        'node_id': node_id,
        'status': 'idle',
        'created_at': now,
        'updated_at': now
    }
    r.set(f'hfs:space:{space_id}', json.dumps(space))
    
    return space_id, repo_id, api


def upload_worker(api, repo_id, hfs_package_path):
    """上传 worker 代码到 Space"""
    import os
    
    # 上传 hfs 包
    for filename in os.listdir(hfs_package_path):
        if filename.endswith('.py'):
            filepath = os.path.join(hfs_package_path, filename)
            api.upload_file(
                path_or_fileobj=filepath,
                path_in_repo=f'hfs/{filename}',
                repo_id=repo_id,
                repo_type='space'
            )
    
    # 上传 sitecustomize.py
    sitecustomize = 'import hfs.worker\n'
    api.upload_file(
        path_or_fileobj=sitecustomize.encode(),
        path_in_repo='sitecustomize.py',
        repo_id=repo_id,
        repo_type='space'
    )
    
    # 上传 requirements.txt
    requirements = 'redis\nhuggingface_hub\ngradio\n'
    api.upload_file(
        path_or_fileobj=requirements.encode(),
        path_in_repo='requirements.txt',
        repo_id=repo_id,
        repo_type='space'
    )
    
    # 上传默认 app.py
    app_py = '''import gradio as gr
demo = gr.Interface(fn=lambda x: f"Hello {x}", inputs="text", outputs="text")
demo.launch()
'''
    api.upload_file(
        path_or_fileobj=app_py.encode(),
        path_in_repo='app.py',
        repo_id=repo_id,
        repo_type='space'
    )
    
    print(f'[HFS] Uploaded worker to {repo_id}')


def set_secrets(api, repo_id, secrets: dict):
    """设置 Space secrets"""
    for key, value in secrets.items():
        api.add_space_secret(repo_id, key, value)
    print(f'[HFS] Set {len(secrets)} secrets')


def delete_space(r, api, space_id, repo_id):
    """删除 Space"""
    try:
        api.delete_repo(repo_id, repo_type='space')
        print(f'[HFS] Deleted repo: {repo_id}')
    except Exception as e:
        print(f'[HFS] Delete repo failed: {e}')
    
    r.delete(f'hfs:space:{space_id}')


def _generate_name():
    """生成自然风格的 Space 名称"""
    prefixes = ['my', 'simple', 'quick', 'easy', 'mini', 'test', 'dev', 'new', 'basic', 'lite']
    words = ['chatbot', 'demo', 'app', 'tool', 'helper', 'project', 'space', 'translator', 'analyzer']
    
    prefix = random.choice(prefixes)
    word = random.choice(words)
    
    # 50% 概率加数字后缀
    if random.random() > 0.5:
        return f'{prefix}-{word}-{random.randint(1, 99)}'
    return f'{prefix}-{word}'
