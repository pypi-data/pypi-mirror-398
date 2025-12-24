"""
Improved Terminal Client - 远程终端客户端

提供类似 SSH 的交互式终端体验，支持自动重连和动态窗口大小调整
"""
import asyncio
import websockets
import sys
import tty
import termios
import os
import signal
import struct
import fcntl
import logging
import warnings
import ssl
import json

# 抑制SSL相关警告和错误
warnings.filterwarnings("ignore", category=DeprecationWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logging.getLogger('asyncio').setLevel(logging.CRITICAL)


async def run_terminal_client(
    node_id: str,
    worker_url: str,
    token: str
) -> int:
    """
    运行远程终端客户端
    
    Args:
        node_id: Agent 节点 ID
        worker_url: Worker WebSocket URL
        token: 认证 token
    
    Returns:
        exit_code: 退出码
    """
    print(f"🔌 连接到远程终端: {node_id}")
    print("   (输入 ~~exit 退出远程终端，或 Ctrl+D 三次退出客户端)")
    
    # 构建 WebSocket URL
    if not worker_url.startswith('ws'):
        worker_url = 'wss://' + worker_url.replace('https://', '').replace('http://', '')
    
    # 获取终端大小
    stdin_fd = sys.stdin.fileno()
    
    def get_terminal_size():
        try:
            winsize = fcntl.ioctl(stdin_fd, termios.TIOCGWINSZ, b'\x00' * 8)
            rows, cols = struct.unpack('HH', winsize[:4])
            return rows, cols
        except Exception:
            return 24, 80
    
    def build_service_url():
        rows, cols = get_terminal_size()
        return f"{worker_url}/ws/term?node={node_id}&token={token}&rows={rows}&cols={cols}"
    
    # 保存原始终端设置
    is_tty = os.isatty(stdin_fd)
    if is_tty:
        old_settings = termios.tcgetattr(stdin_fd)
    else:
        old_settings = None
        print("⚠️  非 TTY 环境，部分功能受限")
    
    # 重连参数
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries + 1):
        try:
            service_url = build_service_url()
            
            if attempt > 0:
                print(f"🔄 重连尝试 {attempt}/{max_retries}...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 10)  # 指数退避，最大10秒
            else:
                print("🔄 正在连接...")
            
            # 连接到 Worker
            ws = await asyncio.wait_for(
                websockets.connect(service_url), 
                timeout=10.0
            )
            print("✅ 已连接\n")
            
            # 退出检测和窗口大小变化检测
            exit_flag = asyncio.Event()
            ctrl_d_count = [0]
            current_size = [get_terminal_size()]
            
            # 窗口大小变化处理
            def handle_resize(signum, frame):
                new_size = get_terminal_size()
                if new_size != current_size[0]:
                    current_size[0] = new_size
                    rows, cols = new_size
                    # 发送窗口大小变化消息
                    resize_msg = json.dumps({
                        "type": "resize",
                        "rows": rows,
                        "cols": cols
                    })
                    asyncio.create_task(send_resize_message(ws, resize_msg))
                    print(f"\r🔄 窗口大小已调整: {cols}x{rows}", end="\r")
            
            async def send_resize_message(websocket, message):
                try:
                    # 发送特殊的resize消息（以\x01开头标识为控制消息）
                    await websocket.send(b'\x01' + message.encode('utf-8'))
                except Exception as e:
                    print(f"发送窗口大小变化失败: {e}")
            
            # 注册窗口大小变化信号处理
            if is_tty:
                signal.signal(signal.SIGWINCH, handle_resize)
            
            async def read_from_stdin():
                """从标准输入读取并发送到 WebSocket"""
                loop = asyncio.get_event_loop()
                
                # 设置 stdin 为非阻塞模式
                old_flags = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
                fcntl.fcntl(stdin_fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)
                
                try:
                    while not exit_flag.is_set():
                        try:
                            data = await loop.run_in_executor(None, sys.stdin.buffer.read, 1024)
                            
                            if data:
                                # 检测 Ctrl+D (ASCII 4)
                                if b'\x04' in data:
                                    ctrl_d_count[0] += data.count(b'\x04')
                                    if ctrl_d_count[0] >= 3:
                                        print("\n👋 检测到 3 次 Ctrl+D，正在退出...")
                                        exit_flag.set()
                                        break
                                else:
                                    ctrl_d_count[0] = 0
                                
                                # 发送数据到 WebSocket
                                await ws.send(data)
                                
                        except BlockingIOError:
                            await asyncio.sleep(0.01)
                        except Exception as e:
                            print(f"读取输入错误: {e}")
                            break
                            
                finally:
                    # 恢复 stdin 的阻塞模式
                    fcntl.fcntl(stdin_fd, fcntl.F_SETFL, old_flags)
            
            async def read_from_websocket():
                """从 WebSocket 读取并输出到终端"""
                try:
                    while not exit_flag.is_set():
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            
                            if isinstance(message, bytes):
                                sys.stdout.buffer.write(message)
                            else:
                                sys.stdout.write(message)
                            sys.stdout.flush()
                            
                        except asyncio.TimeoutError:
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            print("\n🔗 连接已断开")
                            break
                        except Exception as e:
                            print(f"\n❌ 接收数据错误: {e}")
                            break
                            
                except Exception as e:
                    print(f"WebSocket 读取错误: {e}")
                finally:
                    exit_flag.set()
            
            # 并发运行输入输出任务
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(read_from_stdin()),
                    asyncio.create_task(read_from_websocket())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 清理任务
            exit_flag.set()
            for task in pending:
                task.cancel()
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(*pending, return_exceptions=True),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            # 关闭 WebSocket
            try:
                await asyncio.wait_for(ws.close(), timeout=0.5)
            except Exception:
                pass
            
            return 0
            
        except (websockets.exceptions.ConnectionClosed, 
                websockets.exceptions.InvalidURI,
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError) as e:
            if attempt < max_retries:
                print(f"❌ 连接失败: {e}")
                print(f"⏳ {retry_delay}秒后重试...")
                continue
            else:
                print(f"❌ 连接失败，已达到最大重试次数: {e}")
                return 1
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            if attempt < max_retries:
                continue
            return 1
        finally:
            # 恢复终端设置和信号处理
            if old_settings:
                try:
                    termios.tcsetattr(stdin_fd, termios.TCSANOW, old_settings)
                except Exception:
                    pass
            if is_tty:
                signal.signal(signal.SIGWINCH, signal.SIG_DFL)
    
    print("\n👋 终端已断开")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: python cli_terminal_improved.py <node_id> <worker_url> <token>")
        sys.exit(1)
    
    node_id = sys.argv[1]
    worker_url = sys.argv[2]
    token = sys.argv[3]
    
    try:
        exit_code = asyncio.run(run_terminal_client(node_id, worker_url, token))
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
