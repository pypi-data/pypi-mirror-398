"""
TunnelConnection - Agent 端

职责：
1. 封装 WebSocket 消息的发送和接收
2. 实现混合数据传输格式（JSON + Binary）
3. 处理消息分帧和重组
"""
import json
import asyncio
import re
import logging
from typing import Any, Optional, Tuple, Callable

# 获取 logger
logger = logging.getLogger('tunnel_connection')

class TunnelConnection:
    INLINE_THRESHOLD = 64 * 1024  # 64KB (Step 4: 推荐值)
    CHUNK_SIZE = 512 * 1024  # 512KB per chunk (避免 WebSocket 消息过大)
    
    def __init__(self, ws):
        """
        初始化连接
        
        Args:
            ws: WebSocket 连接对象
        """
        self.ws = ws
        self.pending_binary_frame = None
        self.closed = False
        self.message_handlers = []
        logger.debug(f'TunnelConnection initialized, ws={ws}')
    
    def on_message(self, handler: Callable):
        """注册消息处理器"""
        self.message_handlers.append(handler)
    
    async def send(self, message: dict, payload: Any = None) -> None:
        """
        发送消息
        
        Args:
            message: 消息对象（不含 payload 数据）
            payload: 实际数据（可选）
        
        Raises:
            ConnectionError: 连接已关闭
        """
        if self.closed:
            logger.warning(f'[CONN:DIAG] Attempt to send on closed connection: {message.get("type", message.get("action"))}')
            raise ConnectionError('Connection is closed')

        try:
            session_id = message.get('session_id', 'N/A')
            action = message.get('action', 'N/A')
            payload_size = len(payload) if payload else 0
            
            # 只记录控制消息
            if payload is None:
                logger.info(f'[CONN:SEND] session={session_id[-8:] if len(session_id) > 8 else session_id}, action={action}')
            
            # 1. 纯控制消息（无 payload）
            if payload is None:
                logger.debug(f'[CONN:DIAG] Sending control message: type={message.get("type")}, action={message.get("action")}')
                await self.ws.send(json.dumps(message))
                return
            
            # 2. 特殊处理：如果 payload 是 dict 且包含 bytes
            if isinstance(payload, dict) and self._contains_bytes(payload):
                # 将 bytes 值转换为 base64 字符串，以便 JSON 序列化
                payload = self._prepare_dict_for_json(payload)
            
            # 3. 转换为 bytes
            payload_bytes = self._to_bytes(payload)
            payload_size = len(payload_bytes)
            
            # 4. 小数据：内联
            if payload_size < self.INLINE_THRESHOLD:
                message['payload'] = {
                    'encoding': self._detect_encoding(payload_bytes),
                    'inline': True,
                    'data': self._encode(payload_bytes)
                }
                await self.ws.send(json.dumps(message))
                return
            
            # 5. 大数据：判断是否需要分块
            if payload_size <= self.CHUNK_SIZE:
                # 单块：直接发送
                message['payload'] = {
                    'encoding': 'binary',
                    'inline': False,
                    'size': payload_size
                }
                await self.ws.send(json.dumps(message))
                await self.ws.send(payload_bytes)
            else:
                # 超大数据：分块发送
                import uuid
                transfer_id = str(uuid.uuid4())
                total_chunks = (payload_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
                
                # 发送第一个消息（包含分块信息）
                message['payload'] = {
                    'encoding': 'binary',
                    'inline': False,
                    'chunked': True,
                    'transfer_id': transfer_id,
                    'total_size': payload_size,
                    'chunk_size': self.CHUNK_SIZE,
                    'total_chunks': total_chunks
                }
                await self.ws.send(json.dumps(message))
                
                # 分块发送 payload
                for chunk_index in range(total_chunks):
                    start = chunk_index * self.CHUNK_SIZE
                    end = min(start + self.CHUNK_SIZE, payload_size)
                    chunk_data = payload_bytes[start:end]
                    
                    # 发送块头（JSON）
                    chunk_msg = {
                        'type': 'chunk',
                        'transfer_id': transfer_id,
                        'chunk_index': chunk_index,
                        'chunk_size': len(chunk_data)
                    }
                    await self.ws.send(json.dumps(chunk_msg))
                    
                    # 发送块数据（binary）
                    await self.ws.send(chunk_data)
        
        except (OSError, ConnectionError, RuntimeError) as e:
            # 捕获SSL transport错误、连接错误和事件循环关闭错误
            logger.error(f'[CONN:DIAG] Send failed (connection error): {e}')
            self.closed = True
            raise ConnectionError(f'Failed to send message: {e}')
        except Exception as e:
            # 捕获其他异常
            logger.error(f'[CONN:DIAG] Send failed (unexpected): {e}')
            self.closed = True
            raise ConnectionError(f'Unexpected error sending message: {e}')
    
    async def receive(self) -> Tuple[dict, Optional[Any]]:
        """
        接收消息
        
        Returns:
            (message, payload) 元组
        
        Raises:
            ConnectionError: 连接已关闭
            ValueError: 消息格式错误
        """
        if self.closed:
            logger.warning('[CONN:DIAG] Attempt to receive on closed connection')
            raise ConnectionError('Connection is closed')
        
        try:
            data = await self.ws.recv()
            logger.debug(f'[CONN:DIAG] Received data: type={type(data).__name__}, len={len(data) if data else 0}')
        except Exception as e:
            logger.error(f'[CONN:DIAG] Receive failed: {e}')
            self.closed = True
            raise ConnectionError(f'Failed to receive: {e}')
        
        # 处理消息
        if isinstance(data, str):
            # JSON 消息
            return await self._handle_json_message(data)
        elif isinstance(data, bytes):
            # 心跳包（单字节 0x00）- 忽略
            if len(data) == 1 and data[0] == 0:
                return {'type': 'heartbeat'}, None
            # Binary 消息
            return self._handle_binary_message(data)
        else:
            raise ValueError(f'Unknown message type: {type(data)}')
    
    async def _handle_json_message(self, json_str: str) -> Tuple[dict, Optional[Any]]:
        """处理 JSON 消息"""
        message = json.loads(json_str)
        
        # 1. 无 payload 的控制消息
        if 'payload' not in message:
            return message, None
        
        payload_desc = message['payload']
        
        # 2. 内联数据
        if payload_desc.get('inline'):
            payload = self._decode_inline(payload_desc)
            return message, payload
        
        # 3. 分离数据 - 等待后续 binary frame
        if self.pending_binary_frame:
            import logging
            logging.warning('Previous binary frame not received, overwriting')
        
        self.pending_binary_frame = message
        
        # 接收 binary frame
        try:
            binary_data = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
        except asyncio.TimeoutError:
            self.pending_binary_frame = None
            raise ValueError('Timeout waiting for binary frame')
        
        if not isinstance(binary_data, bytes):
            self.pending_binary_frame = None
            raise ValueError(f'Expected binary frame, got {type(binary_data)}')
        
        # 验证大小
        expected_size = payload_desc['size']
        actual_size = len(binary_data)
        
        if actual_size != expected_size:
            import logging
            logging.warning(f'Binary frame size mismatch: expected {expected_size}, got {actual_size}')
        
        message = self.pending_binary_frame
        self.pending_binary_frame = None
        
        return message, binary_data
    
    def _handle_binary_message(self, data: bytes) -> Tuple[dict, bytes]:
        """处理 Binary 消息（意外情况）"""
        if not self.pending_binary_frame:
            raise ValueError('Unexpected binary frame without JSON header')
        
        message = self.pending_binary_frame
        self.pending_binary_frame = None
        
        return message, data
    
    def _to_bytes(self, data: Any) -> bytes:
        """转换为 bytes"""
        if isinstance(data, bytes):
            return data
        if isinstance(data, bytearray):
            return bytes(data)
        if isinstance(data, str):
            return data.encode('utf-8')
        if isinstance(data, (dict, list)):
            # 对于 dict/list，需要处理其中的 bytes 值
            # 检查是否包含 bytes
            if self._contains_bytes(data):
                # 如果包含 bytes，使用混合格式（JSON + binary）
                # 这种情况交给上层的 send() 方法处理分离逻辑
                # 这里直接返回，让 send() 决定如何处理
                raise TypeError(f'Dict/list contains bytes, should be handled by send() method')
            return json.dumps(data).encode('utf-8')
        
        raise TypeError(f'Cannot convert to bytes: {type(data)}')
    
    def _contains_bytes(self, obj) -> bool:
        """检查对象是否包含 bytes"""
        if isinstance(obj, bytes):
            return True
        if isinstance(obj, dict):
            return any(self._contains_bytes(v) for v in obj.values())
        if isinstance(obj, list):
            return any(self._contains_bytes(v) for v in obj)
        return False
    
    def _prepare_dict_for_json(self, obj):
        """将 dict 中的 bytes 转换为 base64，使其可以 JSON 序列化"""
        import base64
        
        if isinstance(obj, bytes):
            # bytes → base64 字符串
            return base64.b64encode(obj).decode('ascii')
        elif isinstance(obj, dict):
            return {k: self._prepare_dict_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_dict_for_json(v) for v in obj]
        else:
            return obj
    
    def _detect_encoding(self, data: bytes) -> str:
        """检测编码"""
        try:
            text = data.decode('utf-8')
            # 检查是否包含控制字符（除了常见的 \n \r \t）
            if re.search(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', text):
                return 'binary'
            return 'utf8'
        except UnicodeDecodeError:
            return 'binary'
    
    def _encode(self, data: bytes):
        """编码为内联数据"""
        encoding = self._detect_encoding(data)
        
        if encoding == 'utf8':
            return data.decode('utf-8')
        else:
            # 小二进制数据，转换为数组
            return list(data)
    
    def _decode_inline(self, payload: dict) -> Any:
        """解码内联数据"""
        encoding = payload.get('encoding', 'utf8')
        data = payload['data']
        
        if encoding == 'utf8':
            return data  # 字符串
        elif encoding == 'json':
            return data  # JSON 对象
        elif isinstance(data, list):
            # 字节数组 → bytes
            return bytes(data)
        else:
            return data
    
    async def close(self):
        """关闭连接"""
        if not self.closed:
            logger.debug('[CONN:DIAG] Closing connection')
            self.closed = True
            try:
                await self.ws.close()
                logger.debug('[CONN:DIAG] Connection closed successfully')
            except (RuntimeError, ConnectionError, OSError) as e:
                # 忽略事件循环关闭或连接已断开的错误
                logger.debug(f'[CONN:DIAG] Close error (ignored): {e}')
