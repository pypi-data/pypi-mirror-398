"""
TCP Forward Client - 本地端口转发

监听本地端口，转发 TCP 流量到 Agent 的目标服务
"""
import asyncio
import websockets
import logging


async def run_tcp_client(
    service_name: str,
    node_id: str,
    worker_url: str,
    token: str,
    local_port: int
) -> int:
    """
    运行本地 TCP 端口转发
    
    Args:
        service_name: 服务名（Agent 注册的名字）
        node_id: Agent 节点 ID
        worker_url: Worker WebSocket URL
        token: 认证 token
        local_port: 本地监听端口
    
    Returns:
        exit_code: 退出码
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('tcp-forward')
    
    print(f"🚀 启动 TCP 端口转发")
    print(f"   本地端口: {local_port}")
    print(f"   目标服务: {service_name}")
    print(f"   目标节点: {node_id}")
    print(f"   Worker: {worker_url}")
    print()
    print(f"📝 访问方式：")
    print(f"   连接到: localhost:{local_port}")
    print()
    print("Ctrl+C 停止")
    print("-" * 60)
    
    # 构建 WebSocket URL
    if not worker_url.startswith('ws'):
        worker_url = 'wss://' + worker_url.replace('https://', '').replace('http://', '')
    
    async def handle_client(client_reader, client_writer):
        """处理客户端连接"""
        client_addr = client_writer.get_extra_info('peername')
        logger.info(f"New connection from {client_addr}")
        
        ws = None
        ws_to_client_task = None
        
        try:
            # 连接到 Worker
            service_url = f"{worker_url}/tcp/{service_name}?node_id={node_id}&token={token}"
            ws = await websockets.connect(service_url)
            logger.info(f"Connected to {service_name}@{node_id} via Worker")
            
            async def read_from_ws():
                """从 WebSocket 读取数据，发送给客户端"""
                try:
                    while True:
                        data = await ws.recv()
                        
                        # 处理字符串或字节
                        if isinstance(data, str):
                            data = data.encode('utf-8')
                        
                        client_writer.write(data)
                        await client_writer.drain()
                except Exception as e:
                    logger.debug(f"WS read error: {e}")
            
            async def read_from_client():
                """从客户端读取数据，发送到 WebSocket"""
                try:
                    while True:
                        data = await client_reader.read(8192)
                        if not data:
                            break
                        
                        await ws.send(data)
                except Exception as e:
                    logger.debug(f"Client read error: {e}")
            
            # 启动双向转发
            ws_to_client_task = asyncio.create_task(read_from_ws())
            await read_from_client()
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            # 清理
            if ws_to_client_task:
                ws_to_client_task.cancel()
            if ws:
                try:
                    asyncio.create_task(ws.close())
                except Exception:
                    pass
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except Exception:
                pass
            logger.info(f"Connection closed: {client_addr}")
    
    try:
        # 启动本地 TCP 服务器
        server = await asyncio.start_server(
            handle_client,
            '127.0.0.1',
            local_port
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f"✅ TCP forward listening on {addr[0]}:{addr[1]}")
        
        async with server:
            await server.serve_forever()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 停止 TCP 端口转发")
        return 0
    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        return 1
