"""
Agent - Agent 端消息路由和插件管理
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from .tunnel_connection import TunnelConnection
from .tunnel_client import TunnelClientManager

class Agent:
    def __init__(self, config: dict):
        """
        初始化 Agent
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.connection: Optional[TunnelConnection] = None
        self.plugins: Dict[str, Any] = {}
        self.running = False
        self.node_id = config.get('node_id', self._generate_node_id())
        # 移除心跳相关配置
        self.connection_monitor_task = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # 隧道客户端管理器
        self.tunnel_manager = TunnelClientManager()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('agent')
    
    async def start(self):
        """启动 Agent"""
        self.running = True
        self.logger.info('Starting agent...')
        
        try:
            # 连接 Worker
            await self.connect_to_worker()
            
            # 加载插件
            await self.load_plugins()
            
            # 注册服务
            await self.register_services()
            
            self.logger.info('Agent started successfully')
            
            # 主循环
            await self.message_loop()
            
        except KeyboardInterrupt:
            self.logger.info('Received interrupt signal')
        except Exception as e:
            self.logger.error(f'CRITICAL: Agent crashed with error: {e}', exc_info=True)
            import traceback
            self.logger.error(f'Full traceback: {traceback.format_exc()}')
            # 尝试保持运行一段时间以便查看日志
            await asyncio.sleep(2)
        finally:
            self.logger.info('Agent stopping...')
            await self.stop()
    
    async def connect_to_worker(self):
        """连接到 Worker"""
        try:
            import websockets
        except ImportError:
            raise RuntimeError('websockets library not found. Install it with: pip install websockets')
        
        worker_url = self.config['worker_url']
        self.logger.info(f'Connecting to {worker_url}')
        
        # 添加 /agent/connect 路径
        if not worker_url.endswith('/agent/connect'):
            if not worker_url.endswith('/'):
                worker_url += '/'
            worker_url += 'agent/connect'
        
        ws = await websockets.connect(worker_url)
        self.connection = TunnelConnection(ws)
        
        self.logger.info('Connected to worker')
    
    async def load_plugins(self):
        """加载插件"""
        services = self.config.get('services', [])
        
        for service_config in services:
            service_type = service_config['type']
            service_name = service_config['name']
            
            try:
                plugin = await self._load_plugin(service_type, service_config)
                self.plugins[service_name] = plugin
                await plugin.initialize()
                self.logger.info(f'Loaded plugin: {service_name} ({service_type})')
            except Exception as e:
                self.logger.error(f'Failed to load plugin {service_name}: {e}', exc_info=True)
    
    async def _load_plugin(self, service_type: str, service_config: dict):
        """
        动态加载插件
        
        Args:
            service_type: 服务类型 (forward, builtin)
            service_config: 服务配置
        
        Returns:
            Plugin 实例
        """
        if service_type == 'forward':
            transport = service_config.get('transport', 'http')
            
            if transport == 'http':
                from .plugins.http_forward import HTTPForwardPlugin
                return HTTPForwardPlugin(self, service_config)
            elif transport == 'tcp':
                from .plugins.tcp_forward import TCPForwardPlugin
                return TCPForwardPlugin(self, service_config)
            elif transport == 'websocket':
                from .plugins.websocket_forward import WebSocketForwardPlugin
                return WebSocketForwardPlugin(self, service_config)
            else:
                raise ValueError(f"Unknown transport: {transport}")
        
        elif service_type == 'builtin':
            # Phase 3: Builtin Services
            service_name = service_config['name']
            plugin_config = service_config.get('config', {})
            
            if service_name == 'exec':
                from .plugins.exec import ExecPlugin
                return ExecPlugin(self, service_config)
            elif service_name == 'socks5':
                from .plugins.socks5 import SOCKS5Plugin
                return SOCKS5Plugin(self, service_config)
            elif service_name == 'term':
                from .plugins.terminal import TerminalPlugin
                return TerminalPlugin(self, service_config)
            else:
                raise ValueError(f"Unknown builtin service: {service_name}")
        
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    async def register_services(self):
        """注册服务"""
        services = []
        
        for service_config in self.config.get('services', []):
            services.append({
                'name': service_config['name'],
                'type': service_config['type'],
                'transport': service_config.get('transport'),
                'target': service_config.get('target')
            })
        
        # 发送注册消息
        register_msg = {
            'type': 'register',
            'node_id': self.node_id,
            'services': services,
            'tags': self.config.get('tags', {}),
            'ip_info': self.config.get('ip_info', {})
        }
        
        await self.connection.send(register_msg)
        
        self.logger.info(f'Registered {len(services)} services')
        
        # 输出标签信息
        tags = self.config.get('tags', {})
        if tags:
            simple_tags = tags.get('simpleTags', [])
            if simple_tags:
                self.logger.info(f'Tags: {", ".join(simple_tags)}')
    
    async def message_loop(self):
        """消息循环"""
        message_count = 0
        last_status_time = asyncio.get_event_loop().time()
        
        while self.running:
            try:
                message, payload = await self.connection.receive()
                message_count += 1
                
                # 每60秒输出一次状态报告
                current_time = asyncio.get_event_loop().time()
                if current_time - last_status_time >= 60:
                    self.logger.debug(f'[AGENT:DIAG] Status: messages={message_count}, plugins={list(self.plugins.keys())}, connection_closed={self.connection.closed}')
                    last_status_time = current_time
                
                # 忽略心跳
                if message.get('type') == 'heartbeat':
                    continue
                
                # 检查注册确认
                if message.get('type') == 'register_ack':
                    self.logger.info(f'Registration confirmed, node_id: {message.get("node_id")}')
                    continue
                
                await self.handle_message(message, payload)
                
            except ConnectionError as e:
                self.logger.error(f'[AGENT:DIAG] Connection error in message_loop: {e}, messages_processed={message_count}')
                await self.reconnect()
            except Exception as e:
                self.logger.error(f'CRITICAL: Error in message loop: {e}', exc_info=True)
                import traceback
                self.logger.error(f'Message loop traceback: {traceback.format_exc()}')
                # 不要退出，尝试继续运行
                await asyncio.sleep(1)
    
    async def handle_message(self, message: dict, payload: Any):
        """
        处理 Worker 消息（核心路由）
        """
        try:
            msg_type = message.get('type')
            service = message.get('service')
            session_id = message.get('session_id')
            
            self.logger.info(f"Agent received message: type={msg_type}, service={service}, session_id={session_id}")
            
            # 处理控制消息（动态服务管理、exec 等）
            if msg_type == 'add_service':
                await self.handle_add_service(message)
                return
            elif msg_type == 'remove_service':
                await self.handle_remove_service(message)
                return
            elif msg_type == 'exec_command':
                await self.handle_exec_command(message)
                return
            elif msg_type == 'exec_command_async':
                await self.handle_exec_command_async(message)
                return
            elif msg_type == 'mapping_add':
                await self.handle_mapping_add(message)
                return
            elif msg_type == 'mapping_remove':
                await self.handle_mapping_remove(message)
                return
            
            # 处理业务消息（转发给 plugin）
            if not service:
                self.logger.error(f'Missing service field in message: {message}')
                return
            
            # 查找 plugin
            plugin = self.plugins.get(service)
            
            if not plugin:
                self.logger.error(f'No plugin for service: {service}')
                self.logger.error(f'Available plugins: {list(self.plugins.keys())}')
                
                # 发送错误响应
                await self.send_error(message, f'Service {service} not found')
                return
            
            self.logger.info(f"Forwarding to plugin: {service}")
            # 转发给 plugin
            await plugin.handle_message(message, payload)
            
        except Exception as e:
            self.logger.error(f'Error handling message: {e}', exc_info=True)
            await self.send_error(message, str(e))
    
    async def send_error(self, original_message: dict, error_message: str):
        """发送错误响应"""
        error_response = {
            'service': original_message.get('service'),
            'session_id': original_message.get('session_id'),
            'request_id': original_message.get('request_id'),
            'category': 'error',
            'action': 'error'
        }
        
        error_data = {
            'code': 'PLUGIN_ERROR',
            'message': error_message
        }
        
        await self.connection.send(error_response, error_data)
    
    async def reconnect(self):
        """重连 Worker"""
        retry_count = 0
        max_retries = 10
        
        self.logger.info(f'[AGENT:DIAG] Starting reconnect, current state: running={self.running}, plugins={list(self.plugins.keys())}')
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f'[AGENT:DIAG] Reconnecting... (attempt {retry_count + 1}/{max_retries})')
                
                # 关闭旧连接
                if self.connection:
                    self.logger.debug(f'[AGENT:DIAG] Closing old connection, closed={self.connection.closed}')
                    await self.connection.close()
                
                # 重新连接
                await self.connect_to_worker()
                await self.register_services()
                
                self.logger.info(f'[AGENT:DIAG] Reconnected successfully after {retry_count + 1} attempts')
                return
                
            except Exception as e:
                self.logger.error(f'[AGENT:DIAG] Reconnect attempt {retry_count + 1} failed: {e}')
                retry_count += 1
                
                # 指数退避
                delay = min(30, 2 ** retry_count)
                await asyncio.sleep(delay)
        
        self.logger.error('Max retries reached, giving up')
        self.running = False
    
    async def stop(self):
        """停止 Agent"""
        self.running = False
        self.logger.info('Stopping agent...')
        
        # 心跳任务已移除
        
        # 停止连接监控任务
        if self.connection_monitor_task:
            self.connection_monitor_task.cancel()
            try:
                await self.connection_monitor_task
            except (asyncio.CancelledError, RuntimeError):
                # 忽略取消错误和事件循环关闭错误
                pass
            self.logger.info('Connection monitor stopped')
        
        # 清理插件
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                self.logger.error(f'Error cleaning up plugin: {e}')
        
        # 停止所有隧道客户端
        try:
            await self.tunnel_manager.stop_all()
            self.logger.info('Tunnel clients stopped')
        except Exception as e:
            self.logger.error(f'Error stopping tunnel clients: {e}')
        
        # 关闭连接
        if self.connection:
            try:
                await self.connection.close()
            except (RuntimeError, ConnectionError, OSError) as e:
                # 忽略事件循环关闭或连接已断开的错误
                self.logger.debug(f'Connection close error (ignored): {e}')
    
    async def _connection_monitor(self):
        """连接监控 - 5分钟间隔，仅检测严重断连"""
        while self.running:
            try:
                # 300秒检查间隔，减少误判
                await asyncio.sleep(300)
                
                if not self.running:
                    break
                
                # 只检查连接对象是否存在
                if not self.connection:
                    self.logger.warning("Connection object is None")
                    await self._handle_connection_error("Connection object lost")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f'Connection monitor error: {e}')
                await asyncio.sleep(300)
    
    def _is_connection_alive(self):
        """检查连接是否活跃（本地检测，无网络消耗）"""
        try:
            if not self.connection:
                return False
            
            # 检查WebSocket连接状态 - TunnelConnection使用self.ws
            if hasattr(self.connection, 'ws'):
                ws = self.connection.ws
                if ws is None:
                    return False
                # 检查WebSocket状态
                if hasattr(ws, 'closed') and ws.closed:
                    return False
                # websockets库的状态检查
                if hasattr(ws, 'state'):
                    # websockets.protocol.State.OPEN = 1
                    if ws.state != 1:  # 不是OPEN状态
                        return False
            
            return True
        except Exception:
            return False
        except Exception:
            return False
    
    async def _handle_connection_error(self, error):
        """处理连接错误，自动重连"""
        if not self.running:
            return
        
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > self.max_reconnect_attempts:
            self.logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached, giving up")
            self.running = False
            return
        
        # 指数退避：1s, 2s, 4s, 8s, 16s, 32s, 60s (最大)
        delay = min(60, 2 ** (self.reconnect_attempts - 1))
        
        # DO休眠断开是正常现象，降低日志级别
        error_str = str(error).lower()
        if any(x in error_str for x in ['connection closed', 'websocket', 'hibernation']):
            self.logger.debug(f"Connection closed (likely DO hibernation): {error}")
            self.logger.info(f"Reconnecting #{self.reconnect_attempts} in {delay}s...")
        else:
            self.logger.warning(f"Connection error: {error}")
            self.logger.info(f"Attempting reconnect #{self.reconnect_attempts} in {delay}s...")
        
        try:
            await asyncio.sleep(delay)
            
            if not self.running:
                return
            
            # 执行重连
            await self.reconnect()
            
            # 重连成功，重置计数器
            self.reconnect_attempts = 0
            self.logger.info("Reconnection successful")
            
        except Exception as e:
            self.logger.error(f"Reconnect attempt #{self.reconnect_attempts} failed: {e}")
            # 继续尝试下一次重连
        
        self.logger.info('Agent stopped')
    
    def _generate_node_id(self) -> str:
        """生成节点 ID"""
        import socket
        hostname = socket.gethostname()
        return f'node-{hostname}'
    
    async def handle_add_service(self, message: dict):
        """处理动态添加服务请求"""
        request_id = message.get('request_id')
        service_name = message.get('service_name')
        port = message.get('port')
        protocol = message.get('protocol', 'http')
        builtin = message.get('builtin', False)
        
        try:
            # 检查服务是否已存在
            if service_name in self.plugins:
                await self.connection.send({
                    'type': 'response',
                    'request_id': request_id,
                    'success': False,
                    'error': 'Service already exists'
                })
                return
            
            # 构造服务配置
            service_config = {
                'name': service_name,
                'port': port,
                'protocol': protocol,
                'builtin': builtin
            }
            
            # 判断服务类型
            if builtin:
                # 内置服务（@exec, @socks5 等）
                if service_name.startswith('@'):
                    base_name = service_name[1:]  # 去掉 @ 前缀
                    service_config['type'] = 'builtin'
                    service_config['name'] = base_name  # _load_plugin 期望不带 @
                else:
                    service_config['type'] = 'builtin'
                    service_config['name'] = service_name
            else:
                # 端口转发服务
                service_config['type'] = 'forward'
                service_config['transport'] = protocol
                service_config['target'] = {
                    'host': '127.0.0.1',
                    'port': port
                }
            
            # 加载插件
            plugin = await self._load_plugin(service_config['type'], service_config)
            self.plugins[service_name] = plugin
            await plugin.initialize()
            
            self.logger.info(f'✓ Service added: {service_name}')
            
            # 发送成功响应
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': True,
                'service_name': service_name
            })
            
        except Exception as e:
            self.logger.error(f'Failed to add service {service_name}: {e}', exc_info=True)
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': False,
                'error': str(e)
            })
    
    async def handle_remove_service(self, message: dict):
        """处理动态删除服务请求"""
        request_id = message.get('request_id')
        service_name = message.get('service_name')
        
        try:
            # 检查服务是否存在
            if service_name not in self.plugins:
                await self.connection.send({
                    'type': 'response',
                    'request_id': request_id,
                    'success': False,
                    'error': 'Service not found'
                })
                return
            
            # 停止并删除插件
            plugin = self.plugins[service_name]
            await plugin.cleanup()
            del self.plugins[service_name]
            
            self.logger.info(f'✓ Service removed: {service_name}')
            
            # 发送成功响应
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': True,
                'service_name': service_name
            })
            
        except Exception as e:
            self.logger.error(f'Failed to remove service {service_name}: {e}', exc_info=True)
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': False,
                'error': str(e)
            })
    
    async def handle_exec_command(self, message: dict):
        """处理同步执行命令请求"""
        import subprocess
        import time
        
        request_id = message.get('request_id')
        command = message.get('command')
        
        try:
            self.logger.info(f'Executing: {command}')
            
            start_time = time.time()
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            duration = time.time() - start_time
            
            # 发送响应
            try:
                await self.connection.send({
                    'type': 'response',
                    'request_id': request_id,
                    'success': True,
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'duration': duration
                })
            except (OSError, ConnectionError, RuntimeError):
                # 忽略发送响应时的连接错误
                pass
            
            self.logger.info(f'Command completed: exit_code={result.returncode}, duration={duration:.2f}s')
            
        except subprocess.TimeoutExpired:
            self.logger.error('Command timeout')
            try:
                await self.connection.send({
                    'type': 'response',
                    'request_id': request_id,
                    'success': False,
                    'error': 'Command timeout'
                })
            except (OSError, ConnectionError, RuntimeError):
                # 忽略发送响应时的连接错误
                pass
        except Exception as e:
            self.logger.error(f'Command execution failed: {e}', exc_info=True)
            try:
                await self.connection.send({
                    'type': 'response',
                    'request_id': request_id,
                    'success': False,
                    'error': str(e)
                })
            except (OSError, ConnectionError, RuntimeError):
                # 忽略发送响应时的连接错误
                pass
    
    async def handle_exec_command_async(self, message: dict):
        """处理异步执行命令请求"""
        import subprocess
        
        task_id = message.get('task_id')
        command = message.get('command')
        
        try:
            self.logger.info(f'Executing async: {command} (task_id={task_id})')
            
            # 异步执行（不等待）
            async def run_command():
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    # 发送完成通知
                    await self.connection.send({
                        'type': 'task_completed',
                        'task_id': task_id,
                        'exit_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    })
                except Exception as e:
                    await self.connection.send({
                        'type': 'task_failed',
                        'task_id': task_id,
                        'error': str(e)
                    })
            
            # 启动后台任务
            asyncio.create_task(run_command())
            
        except Exception as e:
            self.logger.error(f'Failed to start async command: {e}', exc_info=True)

    async def handle_mapping_add(self, message: dict):
        """处理添加隧道映射请求"""
        request_id = message.get('request_id')
        tunnel_config = message.get('tunnel', {})
        proxy_config = message.get('proxy', {})
        
        try:
            self.logger.info(f'Adding tunnel mapping: {proxy_config.get("name")}')
            self.logger.info(f'Tunnel config: {tunnel_config}')
            self.logger.info(f'Proxy config: {proxy_config}')
            
            # 添加映射
            endpoint = await self.tunnel_manager.add_mapping(tunnel_config, proxy_config)
            
            # 发送成功响应
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': True,
                'endpoint': endpoint,
                'status': 'connected'
            })
            
            self.logger.info(f'Tunnel mapping added: {proxy_config.get("name")} -> {endpoint}')
            
        except Exception as e:
            self.logger.error(f'Failed to add tunnel mapping: {e}', exc_info=True)
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': False,
                'error': str(e)
            })

    async def handle_mapping_remove(self, message: dict):
        """处理移除隧道映射请求"""
        request_id = message.get('request_id')
        tunnel_id = message.get('tunnel_id')
        proxy_name = message.get('proxy_name')
        
        try:
            self.logger.info(f'Removing tunnel mapping: {proxy_name}')
            
            await self.tunnel_manager.remove_mapping(tunnel_id, proxy_name)
            
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': True
            })
            
            self.logger.info(f'Tunnel mapping removed: {proxy_name}')
            
        except Exception as e:
            self.logger.error(f'Failed to remove tunnel mapping: {e}', exc_info=True)
            await self.connection.send({
                'type': 'response',
                'request_id': request_id,
                'success': False,
                'error': str(e)
            })


async def main():
    """主函数"""
    # 示例配置
    config = {
        'worker_url': 'ws://localhost:8787/agent/connect',
        'node_id': 'test-node-1',
        'services': [
            {
                'name': 'test-service',
                'type': 'builtin'
            }
        ],
        'tags': {
            'env': 'dev',
            'region': 'local'
        }
    }
    
    agent = Agent(config)
    await agent.start()


if __name__ == '__main__':
    asyncio.run(main())
