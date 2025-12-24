import asyncio
import websockets
import json
from system_detect import detect_system, detect_capabilities, generate_fingerprint

async def run():
    worker_url = "wss://tunnel-v3-dev.snake8cmask.workers.dev/agent/connect"
    
    print(f"Connecting to {worker_url}")
    
    async with websockets.connect(worker_url) as ws:
        # 注册
        fingerprint = generate_fingerprint()
        await ws.send(json.dumps({
            'type': 'register',
            'fingerprint': fingerprint,
            'services': ['exec'],
            'tags': {'simpleTags': ['production', 'test'], 'attrs': {}},
            'system': detect_system(),
            'capabilities': detect_capabilities()
        }))
        
        resp = await ws.recv()
        data = json.loads(resp)
        node_id = data.get('node_id')
        print(f"✓ Registered: {node_id}")
        
        # 保持连接
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(msg)
                print(f"Received: {data.get('type')}")
                
                # 处理请求
                if data.get('type') == 'request':
                    if data.get('action') == 'exec':
                        import subprocess
                        result = subprocess.run(
                            data.get('command', 'echo ok'),
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        await ws.send(json.dumps({
                            'type': 'response',
                            'session_id': data.get('session_id'),
                            'data': {
                                'stdout': result.stdout,
                                'stderr': result.stderr,
                                'returncode': result.returncode
                            }
                        }))
            except asyncio.TimeoutError:
                pass
            await asyncio.sleep(0.1)

asyncio.run(run())
