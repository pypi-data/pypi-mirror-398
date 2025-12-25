"""
Terminal 插件

Agent 端实现远程终端，使用 PTY 提供类似 SSH 的体验
"""
import asyncio
import os
import pty
import struct
import fcntl
import termios
import signal
import logging
from typing import Dict, Any
from .base import Plugin


class TerminalPlugin(Plugin):
    """Terminal 插件"""
    
    def __init__(self, agent, service_config: dict):
        super().__init__(agent, service_config)
        self.sessions = {}  # session_id -> {master_fd, pid, read_task}
    
    async def initialize(self):
        """初始化插件"""
        self.logger.info("Terminal plugin initialized")
    
    async def handle_message(self, message: dict, payload: Any):
        """处理消息"""
        session_id = None
        try:
            session_id = message.get('session_id')
            
            if not session_id:
                self.logger.error("Message missing session_id")
                return
            
            # 忽略 control 消息（init 等）
            category = message.get('category')
            if category == 'control':
                action = message.get('action')
                if action == 'init':
                    # 初始化终端
                    await self._init_terminal(session_id, message)
                elif action == 'close':
                    # 关闭终端
                    await self._cleanup_session(session_id)
                return
            
            # 处理连接关闭
            if payload is None:
                if session_id in self.sessions:
                    self.logger.info(f"Client disconnected: {session_id}, keeping shell alive for reconnection")
                    # 不要 cleanup，让 shell 继续运行，等待客户端重连
                    # 只有显式的 close 消息才会真正清理
                return
            
            # 转换 payload 为 bytes
            if isinstance(payload, str):
                data = payload.encode('utf-8')
            elif isinstance(payload, bytes):
                data = payload
            else:
                self.logger.error(f"Unexpected payload type: {type(payload)}")
                return
            
            # 处理特殊控制序列
            if len(data) == 1 and data[0] == 0:
                # 心跳包，忽略
                return
            elif len(data) > 0 and data[0] == 0x01:
                try:
                    import json
                    msg = json.loads(data[1:].decode('utf-8'))
                    if msg.get('type') == 'resize':
                        await self._handle_resize(session_id, msg.get('rows', 24), msg.get('cols', 80))
                        return
                except Exception as e:
                    self.logger.debug(f"Failed to parse control message: {e}")
            
            # 处理终端数据（写入 PTY）
            await self._handle_input(session_id, data)
            
        except Exception as e:
            self.logger.error(f'CRITICAL: Terminal plugin error: {e}', exc_info=True)
            import traceback
            self.logger.error(f'Terminal plugin traceback: {traceback.format_exc()}')
            # 不要让异常传播，只清理当前session
            if session_id:
                try:
                    await self._cleanup_session(session_id)
                except Exception as cleanup_e:
                    self.logger.error(f'Terminal cleanup error: {cleanup_e}')
                    pass  # 清理失败也不要抛异常
    
    async def _init_terminal(self, session_id: str, message: dict):
        """初始化终端会话"""
        if session_id in self.sessions:
            self.logger.warning(f"Session already exists: {session_id}")
            return
        
        # 获取终端大小
        term_size = message.get('term_size', {})
        rows = term_size.get('rows', 24)
        cols = term_size.get('cols', 80)
        
        # 创建 PTY
        try:
            # 获取 shell
            shell = os.environ.get('SHELL', '/bin/bash')
            
            # Fork 进程并创建 PTY
            pid, master_fd = pty.fork()
            
            if pid == 0:
                # 子进程 - 设置环境变量并执行 shell
                os.environ['TERM'] = 'xterm-256color'
                os.environ['LINES'] = str(rows)
                os.environ['COLUMNS'] = str(cols)
                os.execvp(shell, [shell])
            else:
                # 父进程 - 管理 PTY
                # 设置 master_fd 为非阻塞
                flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
                fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                # 设置终端大小
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                self.logger.info(f"Terminal size: {rows}x{cols}")
                
                # 保存 session
                self.sessions[session_id] = {
                    'master_fd': master_fd,
                    'pid': pid,
                    'read_task': None
                }
                
                # 启动读取任务
                read_task = asyncio.create_task(
                    self._read_from_pty(session_id, master_fd)
                )
                self.sessions[session_id]['read_task'] = read_task
                
                self.logger.info(f"Terminal created: {session_id}, pid={pid}, shell={shell}")
                
                # 发送ready消息激活会话
                await self.send_control(session_id, 'ready')
                
        except Exception as e:
            self.logger.error(f"Failed to create terminal: {e}")
            import traceback
            traceback.print_exc()
    
    async def _handle_input(self, session_id: str, data: bytes):
        """处理客户端输入（写入 PTY）"""
        if session_id not in self.sessions:
            self.logger.warning(f"Session not found: {session_id}")
            return
        
        session = self.sessions[session_id]
        master_fd = session['master_fd']
        
        # 过滤心跳包（支持字节和字符串格式）
        if data == b'\x00' or data == b'\\x00' or (isinstance(data, str) and data in ['\x00', '\\x00']):
            return
        
        # 检查是否是特殊退出命令
        data_str = data.decode('utf-8', errors='ignore').strip() if isinstance(data, bytes) else data.strip()
        if data_str == '~~exit':
            self.logger.info(f"Special exit command detected for session {session_id}")
            # 直接关闭会话，不发送到PTY
            await self._cleanup_session(session_id)
            return
        
        # 记录输入（用于调试 tmux 问题）
        if len(data) < 100:  # 只记录短命令
            self.logger.debug(f"PTY input: {repr(data[:100])}")
        
        try:
            # 确保数据是字节格式
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # 写入 PTY
            os.write(master_fd, data)
                
        except OSError as e:
            self.logger.error(f"Failed to write to PTY: {e}")
            await self._cleanup_session(session_id)
    
    async def _handle_resize(self, session_id: str, rows: int, cols: int):
        """处理终端大小调整"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        master_fd = session['master_fd']
        
        try:
            # 设置新的终端大小
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
            
            # 发送 SIGWINCH 信号给子进程
            os.kill(session['pid'], signal.SIGWINCH)
            
            self.logger.info(f"Terminal resized: {rows}x{cols}")
        except Exception as e:
            self.logger.error(f"Failed to resize terminal: {e}")
    
    async def _read_from_pty(self, session_id: str, master_fd: int):
        """从 PTY 读取输出并发送给客户端"""
        total_bytes = 0
        message_count = 0
        try:
            while session_id in self.sessions:
                try:
                    # 非阻塞读取
                    data = os.read(master_fd, 8192)
                    
                    if not data:
                        # EOF - shell已退出
                        self.logger.info(f"Shell exited (EOF), sent {message_count} messages, {total_bytes} bytes")
                        break
                    
                    # 统计
                    total_bytes += len(data)
                    message_count += 1
                    
                    # 每100条消息记录一次
                    if message_count % 100 == 0:
                        self.logger.info(f"PTY stats: {message_count} messages, {total_bytes} bytes")
                    
                    # 发送给客户端，不等待完成（fire and forget）
                    asyncio.create_task(self.send_data(session_id, data))
                    
                except BlockingIOError:
                    # 没有数据，继续等待
                    await asyncio.sleep(0.01)
                except OSError as e:
                    # PTY 关闭（shell 退出）是正常的
                    if e.errno == 5:  # Input/output error
                        self.logger.info(f"Shell exited (PTY closed), sent {message_count} messages, {total_bytes} bytes")
                    else:
                        self.logger.error(f"PTY read error: {e}, sent {message_count} messages")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error reading from PTY: {e}, sent {message_count} messages")
        finally:
            self.logger.info(f"PTY read loop ended for {session_id}, total: {message_count} messages, {total_bytes} bytes")
            await self._cleanup_session(session_id)
    
    # 使用 base.py 的标准方法 send_data
    # 已删除自定义 send() 方法，统一使用 self.send_data()
    
    async def _cleanup_session(self, session_id: str):
        """清理 session"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # 取消读取任务
        if session.get('read_task'):
            session['read_task'].cancel()
        
        # 关闭 PTY
        try:
            os.close(session['master_fd'])
        except Exception:
            pass
        
        # 终止子进程
        try:
            os.kill(session['pid'], signal.SIGTERM)
            # 等待子进程结束
            try:
                os.waitpid(session['pid'], os.WNOHANG)
            except Exception:
                pass
        except Exception:
            pass
        
        # 删除 session
        del self.sessions[session_id]
        self.logger.info(f"Terminal session cleaned up: {session_id}")
    
    async def cleanup(self):
        """清理资源"""
        for session_id in list(self.sessions.keys()):
            await self._cleanup_session(session_id)
        self.logger.info("Terminal plugin cleanup")
