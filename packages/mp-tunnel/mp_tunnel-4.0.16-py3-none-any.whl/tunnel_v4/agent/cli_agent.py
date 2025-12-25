"""
Agent CLI 适配器

将 CLI 参数转换为 Agent 配置并运行
"""
import asyncio
import logging
import time
import sys
from typing import List, Dict, Optional
from .agent import Agent
from .ip_info import get_ip_info, format_ip_info


def parse_services(service_specs: List[str]) -> List[Dict]:
    """
    解析服务定义
    
    支持格式：
      @exec, @terminal, @proxy, @socks5  - Builtin 服务
      @all                                - 所有内置服务
      name:port[:protocol]                - Forward 服务
    
    Args:
        service_specs: 服务定义列表
    
    Returns:
        服务配置列表
    """
    services = []
    
    # 处理 @all - 展开为所有内置服务
    expanded_specs = []
    for spec in service_specs:
        if spec == '@all':
            expanded_specs.extend(['@exec', '@terminal', '@socks5'])
        else:
            expanded_specs.append(spec)
    
    for spec in expanded_specs:
        if spec.startswith('@'):
            # Builtin 服务
            service_name = spec[1:]  # 去掉 @
            
            if service_name not in ['exec', 'term', 'proxy', 'socks5']:
                raise ValueError(f"Unknown builtin service: @{service_name}")
            
            # term 保持为 term，不映射为 terminal
            # if service_name == 'term':
            #     service_name = 'terminal'
            
            services.append({
                'type': 'builtin',
                'name': service_name,
                'config': {}
            })
        
        else:
            # Forward 服务
            parts = spec.split(':')
            
            if len(parts) < 2:
                raise ValueError(f"Invalid forward service format: {spec}")
            
            name = parts[0]
            port = int(parts[1])
            protocol = parts[2] if len(parts) > 2 else 'http'
            
            if protocol not in ['http', 'tcp', 'ws', 'websocket']:
                raise ValueError(f"Unknown protocol: {protocol}")
            
            # websocket 简写为 ws
            if protocol == 'websocket':
                protocol = 'ws'
            
            # 映射协议到 transport
            transport_map = {
                'http': 'http',
                'tcp': 'tcp',
                'ws': 'websocket'
            }
            
            services.append({
                'type': 'forward',
                'name': name,
                'transport': transport_map[protocol],
                'target': {
                    'host': '127.0.0.1',
                    'port': port
                }
            })
    
    return services


def parse_tags(tag_args):
    """
    解析标签参数
    
    输入格式:
        ['us,aws,proxy', 'region=us-west', 'fast']
    
    输出格式:
        {
            'simpleTags': ['us', 'aws', 'proxy', 'fast'],
            'attrs': {'region': 'us-west'}
        }
    
    Args:
        tag_args: 标签参数列表（可能为 None 或 tuple）
        
    Returns:
        dict: 包含 simpleTags 和 attrs 的字典
    """
    simple_tags = []
    attrs = {}
    
    if not tag_args:
        return {'simpleTags': simple_tags, 'attrs': attrs}
    
    for tag_group in tag_args:
        if not tag_group:
            continue
            
        parts = tag_group.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            if '=' in part:
                # 属性标签: region=us-west
                key, value = part.split('=', 1)
                attrs[key.strip()] = value.strip()
            else:
                # 简单标签: us, aws, proxy
                simple_tags.append(part)
    
    return {
        'simpleTags': simple_tags,
        'attrs': attrs
    }


async def run_agent(
    services: List[str],
    node_id: str,
    worker_url: str,
    config_file: Optional[str] = None,
    tags: Optional[Dict] = None,
    token: Optional[str] = None,
    heartbeat_interval: int = 600,
    debug: bool = False,
    log_file: Optional[str] = None,
    skip_confirm: bool = False
):
    """
    运行 Agent
    
    Args:
        services: 服务定义列表
        node_id: 节点 ID
        worker_url: Worker URL
        config_file: 配置文件路径（可选）
        tags: 节点标签（可选）
        token: 认证 Token（可选）
        skip_confirm: 跳过确认（可选）
    """
    # 配置日志
    log_level = logging.DEBUG if debug else logging.INFO
    
    # 设置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format=log_format
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file or debug:
        if not log_file:
            # 默认日志目录: /tmp/tunnel_logs/
            import os
            log_dir = '/tmp/tunnel_logs'
            os.makedirs(log_dir, exist_ok=True)
            log_file = f'{log_dir}/agent_{node_id}.log'
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 添加到根记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        print(f"📝 日志文件: {log_file}")
        if debug:
            print(f"🐛 调试模式: 启用")
    
    # 如果指定了配置文件，读取配置
    if config_file:
        import yaml
        with open(config_file, 'r') as f:
            file_config = yaml.safe_load(f)
        
        # 配置文件优先
        config = {
            'worker_url': file_config.get('worker_url', worker_url),
            'node_id': file_config.get('node_id', node_id),
            'services': file_config.get('services', []),
            'tags': file_config.get('tags', tags or {})
        }
    else:
        # 解析命令行服务定义
        try:
            service_configs = parse_services(services)
        except ValueError as e:
            print(f"❌ 服务定义错误: {e}")
            return
        
        if not service_configs:
            print("❌ 错误: 至少需要指定一个服务")
            print()
            print("示例:")
            print("  tunnel agent @exec")
            print("  tunnel agent @exec @terminal")
            print("  tunnel agent myapi:5000:http")
            print("  tunnel agent mysql:3306:tcp")
            return
        
        config = {
            'worker_url': worker_url,
            'node_id': node_id,
            'services': service_configs,
            'tags': tags or {},
            'token': token,
            'heartbeat_interval': heartbeat_interval
        }
    
    # 收集 IP 信息
    print("🔍 正在收集节点信息...")
    ip_info = get_ip_info()
    config['ip_info'] = ip_info
    
    # 打印启动信息
    print()
    print("=" * 60)
    print("Tunnel System - Agent Mode")
    print("=" * 60)
    print()
    print(f"节点 ID:    {config['node_id']}")
    print(f"Worker:     {config['worker_url']}")
    if ip_info.get('ip'):
        print(f"IP 信息:    {format_ip_info(ip_info)}")
    if config['tags']:
        simple_tags = config['tags'].get('simpleTags', [])
        attrs = config['tags'].get('attrs', {})
        if simple_tags:
            print(f"标签:       {', '.join(simple_tags)}")
        if attrs:
            attr_str = ', '.join([f'{k}={v}' for k, v in attrs.items()])
            print(f"属性:       {attr_str}")
    if token:
        print(f"认证:       启用")
    print(f"服务数:     {len(config['services'])}")
    print()
    print("服务列表:")
    for svc in config['services']:
        if svc['type'] == 'builtin':
            print(f"  - @{svc['name']}")
        else:
            proto = {
                'http': 'http',
                'tcp': 'tcp',
                'websocket': 'ws'
            }.get(svc['transport'], svc['transport'])
            print(f"  - {svc['name']} ({svc['target']}, {proto})")
    print()
    print("Ctrl+C 停止")
    print("=" * 60)
    print()
    
    # 启动 Agent
    agent = Agent(config)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\n\n✓ 收到停止信号，正在关闭...")
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        pass


def run_agent_daemon(
    services: tuple,
    node_id: str,
    worker_url: str,
    config_file: Optional[str] = None,
    tags: Optional[Dict] = None,
    token: Optional[str] = None,
    skip_confirm: bool = False
):
    """
    后台运行 Agent + 自动重启
    
    默认生产模式，Agent 崩溃后自动重启
    """
    restart_count = 0
    restart_delay = 5  # 重启延迟（秒）
    
    print("🚀 Agent 守护模式启动（后台运行 + 自动重启）")
    print(f"   - 按 Ctrl+C 退出")
    print(f"   - 崩溃后 {restart_delay} 秒自动重启")
    print()
    
    while True:
        try:
            # 运行 Agent
            asyncio.run(run_agent(
                services=services,
                node_id=node_id,
                worker_url=worker_url,
                config_file=config_file,
                tags=tags,
                token=token,
                skip_confirm=skip_confirm
            ))
            
            # 正常退出（用户主动停止）
            break
            
        except KeyboardInterrupt:
            # 用户 Ctrl+C
            print("\n\n⚠️  Agent 已停止")
            break
            
        except Exception as e:
            restart_count += 1
            print(f"\n\n❌ Agent 崩溃 (第 {restart_count} 次): {e}", file=sys.stderr)
            print(f"⏱️  {restart_delay} 秒后自动重启...\n", file=sys.stderr)
            
            try:
                time.sleep(restart_delay)
            except KeyboardInterrupt:
                print("\n⚠️  重启已取消")
                break
