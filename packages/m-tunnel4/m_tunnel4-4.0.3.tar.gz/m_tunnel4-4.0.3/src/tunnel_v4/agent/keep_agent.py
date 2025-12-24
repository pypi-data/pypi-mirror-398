import asyncio
import websockets
import json
from system_detect import detect_system, detect_capabilities, generate_fingerprint

async def keep_agent():
    worker_url = "ws://localhost:8787/agent/connect"
    
    async with websockets.connect(worker_url) as ws:
        fingerprint = generate_fingerprint()
        system = detect_system()
        caps = detect_capabilities()
        
        register_msg = {
            'type': 'register',
            'node_id': 'test-node-1',
            'services': ['exec', 'socks5'],
            'tags': {
                'simpleTags': ['production', 'us'],
                'attrs': {'region': 'us-west-2'}
            },
            'system': system,
            'capabilities': caps,
            'ip_info': {'country': 'US', 'isp': 'Amazon'}
        }
        
        await ws.send(json.dumps(register_msg))
        response = await ws.recv()
        data = json.loads(response)
        print(f"Registered: {data.get('node_id')}")
        
        # 保持连接
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
            except asyncio.TimeoutError:
                pass
            await asyncio.sleep(1)

asyncio.run(keep_agent())
