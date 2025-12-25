from setuptools import setup, find_packages
import os

# 检测是否为开发环境（向上查找 .git 目录）
def is_dev_environment():
    # 如果设置了 RELEASE_BUILD，强制为发布环境
    if os.environ.get('RELEASE_BUILD') == '1':
        return False
    
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, '.git')):
            return True
        parent = os.path.dirname(current)
        if parent == current:  # 到达根目录
            break
        current = parent
    return False

IS_DEV = is_dev_environment()

# 包名和命令区分
PACKAGE_NAME = "tunnel-system-v4" if IS_DEV else "mp_tunnel"
CLI_COMMAND = "tunnel4" if IS_DEV else "tunnel"

# 在安装时设置环境标识
ENV_MARKER = "dev" if IS_DEV else "prod"

setup(
    name=PACKAGE_NAME,
    version="4.0.17",
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["tunnel_v4*"]),
    install_requires=[
        "websockets>=10.0",
        "psutil>=5.9.0",
        "click>=8.0.0",
        "aiohttp>=3.8.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            f"{CLI_COMMAND}=tunnel_v4.cli:cli",
        ],
    },
    package_data={
        "tunnel_v4": [".env_marker"],
    },
    include_package_data=True,
    python_requires=">=3.10",
    author="Tunnel System Team",
    description="Tunnel System V4 - Cloudflare Workers based tunnel system",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tunnel-v4",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
