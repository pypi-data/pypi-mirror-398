"""
Agent V3 - 支持动态 ID 和 detect
"""
import asyncio
import logging
import subprocess
import sys
from typing import Dict, Any, Optional
from .tunnel_connection import TunnelConnection
from .system_detect import (
    detect_system, detect_network, detect_capabilities, 
    detect_resources, generate_fingerprint
)

# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stderr
)

class Agent:
    def __init__(self, config: dict):
        self.config = config
        self.connection: Optional[TunnelConnection] = None
        self.plugins: Dict[str, Any] = {}
        self.running = False
        
        # 动态 ID 支持
        self.node_id = config.get('node_id')
        if not self.node_id:
            self.fingerprint = generate_fingerprint()
        else:
            self.fingerprint = None
        
        self.logger = logging.getLogger('agent')
    
    async def start(self):
        self.running = True
        await self.connect_to_worker()
        await self.load_plugins()
        await self.register()
        await self.message_loop()
    
    async def connect_to_worker(self):
        import websockets
        worker_url = self.config['worker_url']
        
        worker_url = worker_url.replace('http://', 'ws://').replace('https://', 'wss://')
        if not worker_url.endswith('/agent/connect'):
            worker_url = worker_url.rstrip('/') + '/agent/connect'
        
        ws = await websockets.connect(worker_url)
        self.connection = TunnelConnection(ws)
        self.logger.info(f'Connected to {worker_url}')
    
    async def load_plugins(self):
        """加载服务插件（exec, term, socks5 等）"""
        services = self.config.get('services', [])
        
        for service_config in services:
            service_type = service_config['type']
            service_name = service_config['name']
            
            try:
                plugin = await self._load_plugin(service_type, service_config)
                self.plugins[service_name] = plugin
                await plugin.initialize()
            except Exception as e:
                self.logger.error(f'Failed to load plugin {service_name}: {e}')
    
    async def _load_plugin(self, service_type: str, service_config: dict):
        if service_type == 'builtin':
            service_name = service_config['name']
            
            if service_name == 'exec':
                from .plugins.exec import ExecPlugin
                return ExecPlugin(self, service_config)
            elif service_name == 'socks5':
                from .plugins.socks5 import SOCKS5Plugin
                return SOCKS5Plugin(self, service_config)
            elif service_name == 'term':
                from .plugins.terminal import TerminalPlugin
                return TerminalPlugin(self, service_config)
        
        raise ValueError(f"Unknown service: {service_type}")
    
    async def register(self):
        """注册到 Worker（Core 功能）"""
        services = [{'name': s['name'], 'type': s['type']} 
                   for s in self.config.get('services', [])]
        
        system_info = detect_system()
        capabilities = detect_capabilities()
        
        register_msg = {
            'type': 'register',
            'services': services,
            'system': system_info,
            'capabilities': capabilities,
            'tags': {
                'simpleTags': self.config.get('tags', []),
                'attrs': self.config.get('attrs', {})
            }
        }
        
        if self.node_id:
            register_msg['node_id'] = self.node_id
        else:
            register_msg['fingerprint'] = self.fingerprint
        
        await self.connection.send(register_msg)
        
        response, _ = await self.connection.receive()
        if response.get('type') == 'register_ack':
            self.node_id = response['node_id']
            self.logger.info(f'Registered as {self.node_id}')
    
    async def message_loop(self):
        while self.running:
            try:
                message, payload = await self.connection.receive()
                await self.handle_message(message, payload)
            except Exception as e:
                self.logger.error(f'Message loop error: {e}')
                break
    
    async def handle_message(self, message, payload):
        msg_type = message.get('type')
        
        if msg_type == 'request':
            await self.handle_request(message, payload)
        elif msg_type == 'ping':
            await self.connection.send({'type': 'pong'})
    
    async def handle_request(self, message, payload):
        action = message.get('action')
        session_id = message.get('session_id')
        
        try:
            # detect 是 Core 功能，直接处理
            if action == 'detect':
                data = await self._handle_detect(message)
                await self.connection.send({
                    'type': 'response',
                    'session_id': session_id,
                    'data': data
                })
                return
            
            # 其他服务走 Plugin
            service = message.get('service')
            plugin = self.plugins.get(service)
            
            if not plugin:
                raise Exception(f'Service not found: {service}')
            
            result = await plugin.handle_request(message, payload)
            
            await self.connection.send({
                'type': 'response',
                'session_id': session_id,
                'data': result
            })
        
        except Exception as e:
            await self.connection.send({
                'type': 'response',
                'session_id': session_id,
                'error': str(e)
            })
    
    async def _handle_detect(self, request: dict) -> dict:
        """处理 detect 请求（Core 功能）"""
        data = {
            'system': detect_system(),
            'network': detect_network(),
            'capabilities': detect_capabilities(),
            'resources': detect_resources()
        }
        
        # 自定义检测命令
        if 'custom' in request:
            data['custom'] = {}
            for item in request['custom']:
                name = item['name']
                command = item['command']
                try:
                    result = subprocess.check_output(
                        command, shell=True,
                        stderr=subprocess.DEVNULL,
                        text=True, timeout=5
                    ).strip()
                    data['custom'][name] = result
                except Exception as e:
                    data['custom'][name] = f"error: {str(e)}"
        
        return data
    
    async def stop(self):
        self.running = False
        if self.connection:
            await self.connection.close()
