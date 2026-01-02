"""HuggingFace API 封装 - 全部使用 REST API"""
import requests
import random
import tempfile
import subprocess
import shutil
import os
import time
import json
from typing import Optional, Dict

HF_API_BASE = "https://huggingface.co/api"

DOCKER_TEMPLATES = [
    'SpacesExamples/Gradio-Docker-Template',
]


def _api_call(path: str, token: str, method: str = "GET", params: dict = None, json_data: dict = None) -> Optional[Dict]:
    """通用 REST API 调用"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{HF_API_BASE}/{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=headers, params=params, json=json_data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return None
        
        if resp.status_code == 200:
            return resp.json() if resp.text else {}
        else:
            print(f'[HF] API {method} {path} failed: {resp.status_code}', flush=True)
            print(f'[HF] Response: {resp.text[:500]}', flush=True)
            return None
    except Exception as e:
        print(f'[HF] API {method} {path} error: {e}', flush=True)
        return None


def whoami(token: str) -> Optional[Dict]:
    """获取当前用户信息"""
    return _api_call("whoami-v2", token)


def get_space_info(space_id: str, token: str = None) -> Optional[Dict]:
    """获取 Space 详细信息"""
    return _api_call(f"spaces/{space_id}", token)


def get_space_status(space_id: str, token: str = None) -> Optional[Dict]:
    """查询 Space 状态"""
    info = get_space_info(space_id, token)
    if not info:
        return None
    runtime = info.get('runtime', {})
    return {
        'id': info.get('id'),
        'stage': runtime.get('stage', 'unknown'),
        'hardware': runtime.get('hardware', {}).get('current')
    }


def pause_space(space_id: str, token: str) -> bool:
    """暂停 Space"""
    result = _api_call(f"spaces/{space_id}/pause", token, method="POST")
    return result is not None


def restart_space(space_id: str, token: str, factory_reboot: bool = False) -> bool:
    """重启 Space"""
    params = {"factory": True} if factory_reboot else {}
    result = _api_call(f"spaces/{space_id}/restart", token, method="POST", params=params)
    if result is not None:
        print(f'[HF] Restart ok: {space_id}, factory={factory_reboot}', flush=True)
    return result is not None


def delete_space(space_id: str, token: str) -> bool:
    """删除 Space"""
    result = _api_call(f"repos/{space_id}", token, method="DELETE")
    return result is not None


def duplicate_space(from_id: str, to_id: str, token: str, private: bool = True) -> Optional[Dict]:
    """复制 Space"""
    json_data = {
        "repository": to_id,
        "private": private,
        "hardware": "cpu-basic"  # HF 现在要求必须指定 hardware
    }
    return _api_call(f"spaces/{from_id}/duplicate", token, method="POST", json_data=json_data)


def create_space(space_id: str, token: str, template: str = None) -> Optional[Dict]:
    """创建 HuggingFace Space（通过复制模板）"""
    user = whoami(token)
    if not user:
        print('[HF] Failed to get username')
        return None
    
    username = user.get('name')
    full_space_id = f"{username}/{space_id}"
    
    if not template:
        template = random.choice(DOCKER_TEMPLATES)
    
    try:
        result = duplicate_space(template, full_space_id, token, private=True)
        if result:
            return {
                'id': full_space_id,
                'url': f"https://huggingface.co/spaces/{full_space_id}",
                'template': template
            }
    except Exception as e:
        print(f"[HF] Create space failed: {e}")
    return None


def deploy_worker(space_id: str, token: str, redis_url: str,
                  project_id: str = None, node_id: str = None,
                  code_source: str = None, git_url: str = None, 
                  git_token: str = None, git_branch: str = None, git_ref: str = None) -> bool:
    """通过 git clone/push 部署 Worker 到 Space
    
    Args:
        code_source: 代码来源 "local"(默认) 或 "git"
        git_url: Git 仓库 URL (code_source=git 时必填)
        git_token: Git 访问 token (私有仓库需要)
        git_branch: Git 分支名/项目名 (用于过滤 tag，默认 hfs)
        git_ref: Git tag (可选，不指定则自动使用最新)
    """
    # 从 space_id 提取 username（格式: username/space-name）
    if '/' in space_id:
        username = space_id.split('/')[0]
    else:
        user = whoami(token)
        if not user:
            print('[HF] Failed to get username')
            return False
        username = user.get('name')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f'[HF] Cloning {space_id}...', flush=True)
        clone_url = f"https://{username}:{token}@huggingface.co/spaces/{space_id}"
        result = subprocess.run(['git', 'clone', clone_url, tmpdir],
                               capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f'[HF] Git clone failed: {result.stderr[:100]}', flush=True)
            return False
        
        subprocess.run(['git', 'config', 'user.email', 'hfs@example.com'], cwd=tmpdir)
        subprocess.run(['git', 'config', 'user.name', 'HFS'], cwd=tmpdir)
        
        # 获取 hfs 代码
        hfs_dst = os.path.join(tmpdir, 'hfs')
        if os.path.exists(hfs_dst):
            shutil.rmtree(hfs_dst)
        
        if code_source == 'git' and git_url:
            # 从 Git 仓库拉取
            git_tmp = os.path.join(tmpdir, '_git_src')
            git_branch = git_branch or 'hfs'  # 默认分支名
            
            # 构建带认证的 URL（如果是私有仓库）
            auth_git_url = git_url
            if git_token and 'github.com' in git_url and '@' not in git_url:
                # 注入 token: https://github.com/... -> https://token@github.com/...
                auth_git_url = git_url.replace('https://github.com', f'https://{git_token}@github.com')
            
            # 如果没指定 ref，获取该分支的最新 tag
            # tag 格式: {branch}/v0.1.19，需要匹配当前分支前缀
            if not git_ref:
                print(f'[HF] Fetching latest tag for {git_branch} from {git_url}...', flush=True)
                result = subprocess.run(
                    ['git', 'ls-remote', '--tags', '--sort=-v:refname', auth_git_url],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    # 过滤匹配 {branch}/* 的 tag
                    for line in result.stdout.strip().split('\n'):
                        if f'refs/tags/{git_branch}/' in line:
                            git_ref = line.split('refs/tags/')[-1].replace('^{}', '')
                            print(f'[HF] Using latest tag: {git_ref}', flush=True)
                            break
                
                if not git_ref:
                    print(f'[HF] No tags found for {git_branch}, using branch', flush=True)
                    git_ref = git_branch
            
            print(f'[HF] Fetching code from {git_url} @ {git_ref}...', flush=True)
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', '--branch', git_ref, auth_git_url, git_tmp],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                print(f'[HF] Git fetch failed: {result.stderr[:200]}', flush=True)
                return False
            
            # 复制 hfs 目录
            git_hfs_src = os.path.join(git_tmp, 'hfs')
            if os.path.exists(git_hfs_src):
                shutil.copytree(git_hfs_src, hfs_dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            else:
                print(f'[HF] hfs/ not found in git repo', flush=True)
                return False
        else:
            # 从本地复制（默认）
            print(f'[HF] Copying local code...', flush=True)
            hfs_src = os.path.join(os.path.dirname(__file__))
            if not os.path.exists(os.path.join(hfs_src, 'worker.py')):
                print('[HF] Cannot find hfs source')
                return False
            shutil.copytree(hfs_src, hfs_dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        
        main_py = f'''#!/usr/bin/env python3
import os, sys, json, time, traceback

REDIS_URL = "{redis_url}"
SPACE_ID = "{space_id}"

def log_to_redis(msg, level='INFO'):
    try:
        import redis
        from urllib.parse import urlparse
        p = urlparse(REDIS_URL)
        db = int(p.path.lstrip('/')) if p.path else 0
        r = redis.Redis(host=p.hostname, port=p.port or 6379, password=p.password, db=db, decode_responses=True)
        entry = {{'ts': int(time.time()), 'space': SPACE_ID, 'level': level, 'msg': msg}}
        r.lpush('hfs:boot:logs', json.dumps(entry))
        r.ltrim('hfs:boot:logs', 0, 999)
    except: pass

log_to_redis('main.py starting')
try:
    os.environ['HFS_REDIS_URL'] = REDIS_URL
    os.environ['HFS_SPACE_ID'] = SPACE_ID
    os.environ['HFS_PROJECT_ID'] = "{project_id or ''}"
    os.environ['HFS_NODE_ID'] = "{node_id or ''}"
    from hfs.worker import Worker
    worker = Worker(redis_url=REDIS_URL, space_id=SPACE_ID,
                    project_id=os.environ.get('HFS_PROJECT_ID') or None,
                    node_id=os.environ.get('HFS_NODE_ID') or None)
    worker.run()
except Exception as e:
    log_to_redis(f'CRASH: {{traceback.format_exc()}}', 'ERROR')
    raise
'''
        with open(os.path.join(tmpdir, 'main.py'), 'w') as f:
            f.write(main_py)
        
        app_py = '''import gradio as gr
demo = gr.Interface(fn=lambda x: f"Echo: {x}", inputs="text", outputs="text", title="HFS Worker")
demo.launch(server_name="0.0.0.0", server_port=7860)
'''
        with open(os.path.join(tmpdir, 'app.py'), 'w') as f:
            f.write(app_py)
        
        dockerfile = '''FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install redis huggingface_hub gradio requests
COPY hfs/ ./hfs/
COPY main.py .
COPY app.py .
CMD python main.py & python app.py
'''
        with open(os.path.join(tmpdir, 'Dockerfile'), 'w') as f:
            f.write(dockerfile)
        
        print(f'[HF] Pushing...', flush=True)
        subprocess.run(['git', 'add', '.'], cwd=tmpdir)
        subprocess.run(['git', 'commit', '-m', 'Deploy HFS worker'], cwd=tmpdir, capture_output=True)
        
        result = subprocess.run(['git', 'push'], cwd=tmpdir, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f'[HF] Git push failed: {result.stderr[:100]}', flush=True)
            return False
        
        print(f'[HF] Worker deployed to {space_id}', flush=True)
        return True


def wait_for_build(space_id: str, token: str, timeout: int = 300, redis_client=None) -> str:
    """等待 Space 构建完成
    
    Returns:
        最终状态 ('RUNNING', 'PAUSED', 'STOPPED', 'SLEEPING') 或 None
    """
    start = time.time()
    last_stage = None
    paused_count = 0  # 连续 PAUSED 计数
    
    while time.time() - start < timeout:
        try:
            if redis_client:
                space_data = redis_client.get(f'hfs:space:{space_id}')
                if space_data:
                    space = json.loads(space_data)
                    if space.get('status') == 'running':
                        last_hb = space.get('last_heartbeat', 0)
                        if time.time() - last_hb < 60:
                            print(f'[HF] Worker running (heartbeat ok)', flush=True)
                            return 'RUNNING'
            
            status = get_space_status(space_id, token)
            if not status:
                time.sleep(5)
                continue
            
            stage = status.get('stage')
            
            # RUNNING 立即返回
            if stage == 'RUNNING':
                print(f'[HF] Build completed: {stage}', flush=True)
                return stage
            
            # PAUSED/STOPPED/SLEEPING 需要连续多次才返回（避免 factory_reboot 后立即返回）
            if stage in ('PAUSED', 'STOPPED', 'SLEEPING'):
                if last_stage == stage:
                    paused_count += 1
                    if paused_count >= 3:  # 连续 3 次（15秒）才返回
                        print(f'[HF] Build completed: {stage}', flush=True)
                        return stage
                else:
                    paused_count = 1
            else:
                paused_count = 0
            
            if stage == 'RUNTIME_ERROR':
                if last_stage == 'RUNTIME_ERROR':
                    elapsed = time.time() - start
                    if elapsed > 60:
                        print(f'[HF] Build failed: persistent RUNTIME_ERROR', flush=True)
                        return None
            
            last_stage = stage
            print(f'[HF] Building... stage={stage}', flush=True)
            time.sleep(5)
        except Exception as e:
            print(f'[HF] Check build status failed: {e}', flush=True)
            time.sleep(5)
    
    print(f'[HF] Build timeout after {timeout}s', flush=True)
    return None
