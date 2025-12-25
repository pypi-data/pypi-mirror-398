#!/usr/bin/env python3
"""
简化的 Exec Client - 一次性执行
"""
import asyncio
import websockets
import logging
import warnings
import ssl

# 抑制SSL相关警告
warnings.filterwarnings("ignore", category=DeprecationWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 抑制asyncio SSL错误日志
logging.getLogger('asyncio').setLevel(logging.CRITICAL)


async def run_exec_client(node_id: str, worker_url: str, token: str, command: str = None) -> int:
    # 设置异常处理器来抑制SSL transport错误
    def exception_handler(loop, context):
        exception = context.get('exception')
        if isinstance(exception, (OSError, ConnectionError, ssl.SSLError)):
            # 抑制SSL transport相关错误
            return
        # 其他异常正常处理
        loop.default_exception_handler(context)
    
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    
    if not worker_url.startswith('ws'):
        worker_url = 'wss://' + worker_url.replace('https://', '').replace('http://', '')
    
    service_url = f"{worker_url}/ws/exec?node_id={node_id}&token={token}"
    
    logger.info(f"Client connecting to: {service_url}")
    print(f"🔌 连接到: {node_id}")
    
    ws = None
    try:
        ws = await websockets.connect(service_url)
        logger.info("Client WebSocket connected")
        print("✅ 已连接")
        print(f"\n💻 执行: {command}")
        print("-" * 60)
        
        # 发送命令
        logger.info(f"Client sending command: {repr(command)}")
        try:
            await ws.send(command.encode())
        except (OSError, ConnectionError, RuntimeError):
            logger.error("Failed to send command due to connection error")
            print("❌ 发送命令失败")
            return 1
        
        # 接收结果
        try:
            logger.info("Client waiting for response...")
            result = await asyncio.wait_for(ws.recv(), timeout=30)
            logger.info(f"Client received response: {type(result)}, length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            if isinstance(result, bytes):
                print(result.decode('utf-8', errors='ignore'), end='')
            else:
                print(result, end='')
            print("-" * 60)
            print("✅ 完成")
            
            return 0
        except asyncio.TimeoutError:
            logger.error("Client timeout waiting for response")
            print("❌ 超时")
            return 1
            
    except Exception as e:
        logger.error(f"Client error: {e}")
        print(f"❌ 错误: {e}")
        return 1
    finally:
        if ws:
            try:
                await asyncio.wait_for(ws.close(), timeout=0.5)
            except (OSError, ConnectionError, RuntimeError, asyncio.TimeoutError):
                # SSL transport errors during connection closure are common
                pass
            except Exception:
                pass
