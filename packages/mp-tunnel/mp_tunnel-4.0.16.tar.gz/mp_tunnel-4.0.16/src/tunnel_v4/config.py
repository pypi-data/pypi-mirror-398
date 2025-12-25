"""
Tunnel V4 Configuration
"""
import os
import subprocess

# 版本信息
VERSION = "4.0.16"

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
def get_default_env():
    """根据 .env_marker 文件确定默认环境"""
    try:
        marker_file = os.path.join(os.path.dirname(__file__), '.env_marker')
        if os.path.exists(marker_file):
            with open(marker_file) as f:
                env = f.read().strip()
                return env if env in ['dev', 'prod'] else 'prod'
    except:
        pass
    return 'prod'

ENV = os.environ.get('TUNNEL_ENV', get_default_env())

WORKER_URLS = {
    'dev': 'wss://tunnel-v4-dev.day84mask-eac.workers.dev',
    'prod': 'wss://tunnel.somo4.eu.org',
}

DEFAULT_WORKER_URL = WORKER_URLS.get(ENV, WORKER_URLS['prod'])

def get_worker_url():
    """获取 Worker URL，优先使用环境变量"""
    return os.environ.get('TUNNEL_WORKER_URL', DEFAULT_WORKER_URL)
