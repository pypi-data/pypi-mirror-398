"""
[Phase 2] WebSocket Forward Plugin
"""
import asyncio
import logging
from typing import Any, Optional
import websockets
from .base import Plugin

class WebSocketForwardPlugin(Plugin):
    """WebSocket 转发插件"""
    
    def __init__(self, agent, service_config: dict):
        super().__init__(agent, service_config)
        
        target = service_config.get('target', {})
        self.target_host = target.get('host', '127.0.0.1')
        self.target_port = target.get('port')
        
        if not self.target_port:
            raise ValueError(f"WebSocket forward service '{self.service_name}' missing target.port")
        
        self.target_url = f"ws://{self.target_host}:{self.target_port}"
        self.sessions = {}  # session_id -> ws
        self.logger.info(f"WebSocket Forward: {self.service_name} -> {self.target_url}")
    
    async def handle_message(self, message: dict, payload: Optional[Any]):
        """处理 WebSocket 消息"""
        session_id = message.get('session_id')
        category = message.get('category')
        action = message.get('action')
        
        if not session_id:
            self.logger.error("WebSocket message missing session_id")
            return
        
        if category == 'control':
            if action == 'init':
                await self._handle_connect(session_id, payload)
            elif action == 'close':
                await self._handle_close(session_id)
        elif category == 'data':
            await self._handle_message(session_id, payload)
    
    async def _handle_connect(self, session_id: str, init_data):
        """建立 WebSocket 连接"""
        try:
            # 解析 init_data (可能是 dict 或 JSON 字符串)
            if isinstance(init_data, str):
                import json
                init_data = json.loads(init_data)
            
            # 提取路径
            path = init_data.get('path', '/') if init_data else '/'
            url = self.target_url + path
            
            ws = await websockets.connect(url)
            self.sessions[session_id] = ws
            
            self.logger.info(f"WebSocket connected: {session_id}")
            
            # 发送 ready
            await self.send_control(session_id, 'ready')
            
            # 启动读取任务
            asyncio.create_task(self._read_loop(session_id, ws))
            
        except Exception as e:
            self.logger.error(f"WebSocket connect failed: {e}")
            await self.send_error(session_id, f"Connect failed: {e}")
    
    async def _handle_message(self, session_id: str, data: Any):
        """转发消息到 WebSocket"""
        if session_id not in self.sessions:
            self.logger.warning(f"Session not found: {session_id}")
            return
        
        ws = self.sessions[session_id]
        
        try:
            # 发送消息
            self.logger.info(f"Forwarding message to target: {type(data)} {len(str(data))} bytes")
            if isinstance(data, str):
                await ws.send(data)
            elif isinstance(data, bytes):
                await ws.send(data)
            elif isinstance(data, (list, bytearray)):
                await ws.send(bytes(data))
            else:
                await ws.send(str(data))
            
        except Exception as e:
            self.logger.error(f"WebSocket send error: {e}")
            await self._handle_close(session_id)
    
    async def _handle_close(self, session_id: str):
        """关闭 WebSocket 连接"""
        if session_id not in self.sessions:
            self.logger.debug(f"Session already closed: {session_id}")
            return
        
        ws = self.sessions[session_id]
        
        try:
            await ws.close()
        except:
            pass
        
        try:
            del self.sessions[session_id]
            self.logger.info(f"WebSocket closed: {session_id}")
        except KeyError:
            self.logger.debug(f"Session already removed: {session_id}")
    
    async def _read_loop(self, session_id: str, ws):
        """读取 WebSocket 消息并发送到 Worker"""
        try:
            async for message in ws:
                # 发送到 Worker
                await self.send_data(session_id, message)
            
        except Exception as e:
            self.logger.error(f"WebSocket read error: {e}")
        
        finally:
            # 通知关闭
            await self.send_control(session_id, 'close')
            await self._handle_close(session_id)
    
    async def cleanup(self):
        """清理所有连接"""
        for session_id in list(self.sessions.keys()):
            await self._handle_close(session_id)
