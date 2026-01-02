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
    return _api_call("whoami-v2", token)
def get_space_info(space_id: str, token: str = None) -> Optional[Dict]:
    return _api_call(f"spaces/{space_id}", token)
def get_space_status(space_id: str, token: str = None) -> Optional[Dict]:
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
    result = _api_call(f"spaces/{space_id}/pause", token, method="POST")
    return result is not None
def restart_space(space_id: str, token: str, factory_reboot: bool = False) -> bool:
    params = {"factory": True} if factory_reboot else {}
    result = _api_call(f"spaces/{space_id}/restart", token, method="POST", params=params)
    if result is not None:
        print(f'[HF] Restart ok: {space_id}, factory={factory_reboot}', flush=True)
    return result is not None
def delete_space(space_id: str, token: str) -> bool:
    result = _api_call(f"repos/{space_id}", token, method="DELETE")
    return result is not None
def duplicate_space(from_id: str, to_id: str, token: str, private: bool = True) -> Optional[Dict]:
    json_data = {
        "repository": to_id,
        "private": private,
        "hardware": "cpu-basic"
    }
    return _api_call(f"spaces/{from_id}/duplicate", token, method="POST", json_data=json_data)
def create_space(space_id: str, token: str, template: str = None) -> Optional[Dict]:
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
        hfs_dst = os.path.join(tmpdir, 'hfs')
        if os.path.exists(hfs_dst):
            shutil.rmtree(hfs_dst)
        if code_source == 'git' and git_url:
            git_tmp = os.path.join(tmpdir, '_git_src')
            git_branch = git_branch or 'hfs'
            auth_git_url = git_url
            if git_token and 'github.com' in git_url and '@' not in git_url:
                auth_git_url = git_url.replace('https://github.com', f'https://{git_token}@github.com')
            if not git_ref:
                print(f'[HF] Fetching latest tag for {git_branch} from {git_url}...', flush=True)
                result = subprocess.run(
                    ['git', 'ls-remote', '--tags', '--sort=-v:refname', auth_git_url],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
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
            git_hfs_src = os.path.join(git_tmp, 'hfs')
            if os.path.exists(git_hfs_src):
                shutil.copytree(git_hfs_src, hfs_dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            else:
                print(f'[HF] hfs/ not found in git repo', flush=True)
                return False
        else:
            print(f'[HF] Copying local code...', flush=True)
            hfs_src = os.path.join(os.path.dirname(__file__))
            if not os.path.exists(os.path.join(hfs_src, 'worker.py')):
                print('[HF] Cannot find hfs source')
                return False
            shutil.copytree(hfs_src, hfs_dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        with open(os.path.join(tmpdir, 'main.py'), 'w') as f:
            f.write(main_py)
        with open(os.path.join(tmpdir, 'app.py'), 'w') as f:
            f.write(app_py)
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
    start = time.time()
    last_stage = None
    paused_count = 0
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
            if stage == 'RUNNING':
                print(f'[HF] Build completed: {stage}', flush=True)
                return stage
            if stage in ('PAUSED', 'STOPPED', 'SLEEPING'):
                if last_stage == stage:
                    paused_count += 1
                    if paused_count >= 3:
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