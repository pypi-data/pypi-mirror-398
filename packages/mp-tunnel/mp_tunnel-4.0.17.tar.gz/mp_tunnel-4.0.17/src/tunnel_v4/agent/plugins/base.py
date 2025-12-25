"""
Base Plugin Interface
"""
import logging
from typing import Any, Optional

class Plugin:
    """
    Plugin 基类
    
    所有插件必须继承此类并实现 handle_message 方法
    """
    
    def __init__(self, agent, service_config: dict):
        """
        初始化插件
        
        Args:
            agent: Agent 实例
            service_config: 服务配置
        """
        self.agent = agent
        self.service_config = service_config
        self.service_name = service_config['name']
        self.logger = logging.getLogger(f'plugin.{self.service_name}')
    
    async def initialize(self):
        """
        初始化插件（可选）
        
        在插件注册后调用，用于初始化资源
        """
        pass
    
    async def handle_message(self, message: dict, payload: Optional[Any]):
        """
        处理消息
        
        Args:
            message: 消息对象
            payload: 消息载荷
        
        必须由子类实现
        """
        raise NotImplementedError('Plugin must implement handle_message')
    
    async def cleanup(self):
        """
        清理资源（可选）
        
        在插件卸载时调用
        """
        pass
    
    async def send_to_worker(self, message: dict, payload: Any = None):
        """
        发送消息到 Worker
        
        Args:
            message: 消息对象
            payload: 消息载荷
        """
        await self.agent.connection.send(message, payload)
    
    async def send_control(self, session_id: str, action: str, data: Any = None):
        """
        发送控制消息
        
        Args:
            session_id: Session ID
            action: 动作（ready, error, close）
            data: 数据
        """
        message = {
            'service': self.service_name,
            'session_id': session_id,
            'category': 'control',
            'action': action
        }
        
        await self.send_to_worker(message, data)
    
    async def send_data(self, session_id: str, data: Any):
        """
        发送数据消息
        
        Args:
            session_id: Session ID
            data: 数据
        
        Note: transport字段已移除 - Worker不使用该字段进行路由（仅根据session_id）
        """
        message = {
            'service': self.service_name,
            'session_id': session_id,
            'category': 'data',
            'action': 'data'
            # transport字段已移除：Worker是纯隧道，不关心协议类型
        }
        
        await self.send_to_worker(message, data)
    
    async def send_error(self, session_id: str, error_message: str, code: str = 'PLUGIN_ERROR'):
        """
        发送错误消息
        
        Args:
            session_id: Session ID
            error_message: 错误消息
            code: 错误代码
        """
        message = {
            'service': self.service_name,
            'session_id': session_id,
            'category': 'error',
            'action': 'error'
        }
        
        error_data = {
            'code': code,
            'message': error_message
        }
        
        await self.send_to_worker(message, error_data)
