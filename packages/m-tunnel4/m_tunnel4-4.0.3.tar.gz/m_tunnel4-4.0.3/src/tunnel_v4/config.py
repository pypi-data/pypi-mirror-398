"""
Tunnel V4 Configuration
"""
import os
import subprocess

# 版本信息
VERSION = "4.0.3"

# 获取 Git commit hash（构建时）
def get_git_hash():
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(__file__)
        ).decode('ascii').strip()
    except:
        return None

GIT_HASH = get_git_hash()

# Worker URL 配置
ENV = os.environ.get('TUNNEL_ENV', 'prod')

WORKER_URLS = {
    'dev': 'wss://tunnel-v4-dev.day84mask-eac.workers.dev',
    'prod': 'wss://tunnel-v4-prod.day84mask-eac.workers.dev',
}

DEFAULT_WORKER_URL = WORKER_URLS.get(ENV, WORKER_URLS['prod'])

def get_worker_url():
    """获取 Worker URL，优先使用环境变量"""
    return os.environ.get('TUNNEL_WORKER_URL', DEFAULT_WORKER_URL)
