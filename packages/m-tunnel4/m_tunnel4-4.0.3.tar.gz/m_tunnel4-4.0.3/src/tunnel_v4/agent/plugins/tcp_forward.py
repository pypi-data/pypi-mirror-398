"""
[Phase 2] TCP Forward Plugin
"""
import asyncio
import logging
from typing import Any, Optional
from .base import Plugin

class TCPForwardPlugin(Plugin):
    """TCP 转发插件"""
    
    def __init__(self, agent, service_config: dict):
        super().__init__(agent, service_config)
        
        target = service_config.get('target', {})
        self.target_host = target.get('host', '127.0.0.1')
        self.target_port = target.get('port')
        
        if not self.target_port:
            raise ValueError(f"TCP forward service '{self.service_name}' missing target.port")
        
        self.sessions = {}  # session_id -> (reader, writer)
        self.logger.info(f"TCP Forward: {self.service_name} -> {self.target_host}:{self.target_port}")
    
    async def handle_message(self, message: dict, payload: Optional[Any]):
        """处理 TCP 消息"""
        session_id = message.get('session_id')
        category = message.get('category')
        action = message.get('action')
        
        if not session_id:
            self.logger.error("TCP message missing session_id")
            return
        
        if category == 'control':
            if action == 'init':
                await self._handle_connect(session_id)
            elif action == 'close':
                await self._handle_close(session_id)
        elif category == 'data':
            await self._handle_data(session_id, payload)
    
    async def _handle_connect(self, session_id: str):
        """建立 TCP 连接"""
        try:
            reader, writer = await asyncio.open_connection(
                self.target_host, 
                self.target_port
            )
            
            self.sessions[session_id] = (reader, writer)
            self.logger.info(f"TCP connected: {session_id}")
            
            # 发送 ready
            await self.send_control(session_id, 'ready')
            
            # 启动读取任务
            asyncio.create_task(self._read_loop(session_id, reader))
            
        except Exception as e:
            self.logger.error(f"TCP connect failed: {e}")
            await self.send_error(session_id, f"Connect failed: {e}")
    
    async def _handle_data(self, session_id: str, data: Any):
        """转发数据到 TCP"""
        if session_id not in self.sessions:
            return
        
        _, writer = self.sessions[session_id]
        
        try:
            # 转换为 bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif not isinstance(data, bytes):
                data = bytes(data) if isinstance(data, (list, bytearray)) else str(data).encode()
            
            writer.write(data)
            await writer.drain()
            
        except Exception as e:
            self.logger.error(f"TCP write error: {e}")
            await self._handle_close(session_id)
    
    async def _handle_close(self, session_id: str):
        """关闭 TCP 连接"""
        if session_id not in self.sessions:
            return
        
        _, writer = self.sessions[session_id]
        
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
        
        del self.sessions[session_id]
        self.logger.info(f"TCP closed: {session_id}")
    
    async def _read_loop(self, session_id: str, reader):
        """读取 TCP 数据并发送到 Worker"""
        try:
            while session_id in self.sessions:
                data = await reader.read(8192)
                
                if not data:
                    # EOF
                    break
                
                # 发送到 Worker
                await self.send_data(session_id, data)
            
        except Exception as e:
            self.logger.error(f"TCP read error: {e}")
        
        finally:
            # 通知关闭
            await self.send_control(session_id, 'close')
            await self._handle_close(session_id)
    
    async def cleanup(self):
        """清理所有连接"""
        for session_id in list(self.sessions.keys()):
            await self._handle_close(session_id)
