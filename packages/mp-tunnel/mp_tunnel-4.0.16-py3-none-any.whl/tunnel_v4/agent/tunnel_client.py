"""
TunnelClient - 外部隧道客户端管理
支持 frp 等隧道软件
"""
import asyncio
import logging
import os
import tempfile
import subprocess
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger('tunnel_client')


class FrpClient:
    """frpc 客户端管理"""
    
    def __init__(self, tunnel_config: dict):
        """
        Args:
            tunnel_config: 隧道服务器配置
                - endpoint: frps 地址
                - port: frps 端口
                - token: 认证 token
        """
        self.tunnel_id = tunnel_config.get('id', 'default')
        self.endpoint = tunnel_config['endpoint']
        self.port = tunnel_config.get('port', 7000)
        self.token = tunnel_config.get('token', '')
        
        self.proxies: Dict[str, dict] = {}  # name -> proxy config
        self.process: Optional[subprocess.Popen] = None
        self.config_file: Optional[str] = None
        self._lock = asyncio.Lock()
    
    async def add_proxy(self, proxy_config: dict) -> str:
        """
        添加代理配置
        
        Args:
            proxy_config:
                - name: 代理名称
                - local_port: 本地端口 (与 plugin 二选一)
                - plugin: 内置插件 (socks5/http_proxy)
                - remote_port: 远程端口
                - protocol: tcp/http
        
        Returns:
            endpoint: 访问端点
        """
        async with self._lock:
            name = proxy_config['name']
            self.proxies[name] = proxy_config
            
            # 重新生成配置并重启
            await self._restart()
            
            # 返回端点
            return f"{self.endpoint}:{proxy_config.get('remote_port', 0)}"
    
    async def remove_proxy(self, name: str):
        """移除代理"""
        async with self._lock:
            if name in self.proxies:
                del self.proxies[name]
                if self.proxies:
                    await self._restart()
                else:
                    await self.stop()
    
    async def stop(self):
        """停止 frpc"""
        if self.process:
            logger.info(f"[{self.tunnel_id}] Stopping frpc")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        if self.config_file and os.path.exists(self.config_file):
            os.remove(self.config_file)
            self.config_file = None
    
    async def _restart(self):
        """重启 frpc"""
        await self.stop()
        await self._start()
    
    async def _start(self):
        """启动 frpc"""
        if not self.proxies:
            return
        
        # 生成配置文件
        config = self._generate_config()
        
        # 写入临时文件
        fd, self.config_file = tempfile.mkstemp(suffix='.toml', prefix='frpc_')
        with os.fdopen(fd, 'w') as f:
            f.write(config)
        
        logger.info(f"[{self.tunnel_id}] Starting frpc with {len(self.proxies)} proxies")
        logger.info(f"[{self.tunnel_id}] Config file: {self.config_file}")
        logger.info(f"[{self.tunnel_id}] Config:\n{config}")
        
        # 启动 frpc
        try:
            self.process = subprocess.Popen(
                ['frpc', '-c', self.config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # 等待启动
            await asyncio.sleep(2)
            
            if self.process.poll() is not None:
                stdout = self.process.stdout.read().decode() if self.process.stdout else ''
                stderr = self.process.stderr.read().decode() if self.process.stderr else ''
                logger.error(f"[{self.tunnel_id}] frpc exit code: {self.process.returncode}")
                logger.error(f"[{self.tunnel_id}] frpc stdout: {stdout}")
                logger.error(f"[{self.tunnel_id}] frpc stderr: {stderr}")
                raise RuntimeError(f"frpc failed to start: {stderr or stdout}")
            
            logger.info(f"[{self.tunnel_id}] frpc started, pid={self.process.pid}")
        except FileNotFoundError:
            raise RuntimeError("frpc not found. Please install frp client.")
    
    def _generate_config(self) -> str:
        """生成 frpc.toml 配置"""
        lines = [
            f'serverAddr = "{self.endpoint}"',
            f'serverPort = {self.port}',
        ]
        if self.token:
            lines.append(f'auth.token = "{self.token}"')
        lines.append('')
        
        for name, proxy in self.proxies.items():
            lines.append(f'[[proxies]]')
            lines.append(f'name = "{name}"')
            lines.append(f'type = "{proxy.get("protocol", "tcp")}"')
            
            # remotePort 必须在 [[proxies]] 下，不能在 plugin 下
            if proxy.get('remote_port'):
                lines.append(f'remotePort = {proxy["remote_port"]}')
            
            if proxy.get('plugin'):
                # 内置插件模式
                lines.append(f'[proxies.plugin]')
                lines.append(f'type = "{proxy["plugin"]}"')
            else:
                # 端口转发模式
                lines.append(f'localIP = "127.0.0.1"')
                lines.append(f'localPort = {proxy["local_port"]}')
            
            if proxy.get('tunnel_group'):
                lines.append(f'group = "{proxy["tunnel_group"]}"')
                lines.append(f'groupKey = "{proxy.get("group_key", "")}"')
            
            lines.append('')
        
        return '\n'.join(lines)
    
    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


class TunnelClientManager:
    """隧道客户端管理器 - 管理多个隧道服务器的客户端"""
    
    def __init__(self):
        self.clients: Dict[str, FrpClient] = {}  # tunnel_id -> client
        self._lock = asyncio.Lock()
    
    async def add_mapping(self, tunnel_config: dict, proxy_config: dict) -> str:
        """
        添加隧道映射
        
        Args:
            tunnel_config: 隧道服务器配置
            proxy_config: 代理配置
        
        Returns:
            endpoint: 访问端点
        """
        async with self._lock:
            tunnel_id = tunnel_config.get('id', 'default')
            
            # 获取或创建客户端
            if tunnel_id not in self.clients:
                self.clients[tunnel_id] = FrpClient(tunnel_config)
            
            client = self.clients[tunnel_id]
            return await client.add_proxy(proxy_config)
    
    async def remove_mapping(self, tunnel_id: str, proxy_name: str):
        """移除隧道映射"""
        async with self._lock:
            if tunnel_id in self.clients:
                client = self.clients[tunnel_id]
                await client.remove_proxy(proxy_name)
                
                # 如果没有代理了，移除客户端
                if not client.proxies:
                    del self.clients[tunnel_id]
    
    async def stop_all(self):
        """停止所有客户端"""
        async with self._lock:
            for client in self.clients.values():
                await client.stop()
            self.clients.clear()
    
    def get_status(self) -> dict:
        """获取所有客户端状态"""
        return {
            tunnel_id: {
                'running': client.is_running,
                'proxies': list(client.proxies.keys())
            }
            for tunnel_id, client in self.clients.items()
        }
