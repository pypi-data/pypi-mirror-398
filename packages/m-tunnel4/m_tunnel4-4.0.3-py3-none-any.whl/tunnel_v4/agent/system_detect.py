"""
System Detection - 系统信息检测
"""
import platform
import socket
import subprocess
import os
import hashlib

def detect_system():
    """检测系统信息"""
    return {
        'os': platform.system().lower(),
        'arch': platform.machine(),
        'hostname': socket.gethostname(),
        'kernel': platform.release(),
        'uptime': _get_uptime(),
        'vm': _is_vm()
    }

def detect_network():
    """检测网络信息"""
    return {
        'interfaces': _get_interfaces(),
        'dns': _get_dns_servers()
    }

def detect_capabilities():
    """检测系统能力"""
    return {
        'root': os.geteuid() == 0 if hasattr(os, 'geteuid') else False,
        'docker': _has_command('docker'),
        'desktop': _has_desktop(),
        'chrome': _has_command('chrome') or _has_command('chromium'),
        'gpu': _detect_gpu(),
        'python': platform.python_version(),
        'node': _get_node_version()
    }

def detect_resources():
    """检测资源信息"""
    import psutil
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_cores': psutil.cpu_count(),
        'memory_total': mem.total // (1024 * 1024),
        'memory_free': mem.available // (1024 * 1024),
        'disk_total': disk.total // (1024 * 1024 * 1024),
        'disk_free': disk.free // (1024 * 1024 * 1024)
    }

def generate_fingerprint():
    """生成机器指纹用于动态 ID"""
    hostname = socket.gethostname()
    mac = _get_mac_address()
    username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
    
    fingerprint = f"{hostname}:{mac}:{username}"
    return fingerprint

def _get_uptime():
    """获取系统运行时间（秒）"""
    try:
        import psutil
        return int(psutil.boot_time())
    except:
        return 0

def _is_vm():
    """检测是否为虚拟机/容器"""
    # 检查容器环境
    if os.path.exists('/.dockerenv'):
        return True
    
    # 检查虚拟机
    try:
        output = subprocess.check_output(['systemd-detect-virt'], stderr=subprocess.DEVNULL, text=True)
        return output.strip() != 'none'
    except:
        pass
    
    return False

def _get_interfaces():
    """获取网络接口列表"""
    try:
        import psutil
        return list(psutil.net_if_addrs().keys())
    except:
        return []

def _get_dns_servers():
    """获取 DNS 服务器"""
    try:
        with open('/etc/resolv.conf', 'r') as f:
            lines = f.readlines()
            return [line.split()[1] for line in lines if line.startswith('nameserver')]
    except:
        return []

def _has_command(cmd):
    """检查命令是否存在"""
    try:
        subprocess.run([cmd, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def _has_desktop():
    """检测是否有桌面环境"""
    return os.getenv('DISPLAY') is not None or os.getenv('WAYLAND_DISPLAY') is not None

def _detect_gpu():
    """检测 GPU 类型"""
    try:
        output = subprocess.check_output(['lspci'], stderr=subprocess.DEVNULL, text=True)
        if 'nvidia' in output.lower():
            return 'nvidia'
        elif 'amd' in output.lower():
            return 'amd'
        elif 'intel' in output.lower():
            return 'intel'
    except:
        pass
    return None

def _get_node_version():
    """获取 Node.js 版本"""
    try:
        output = subprocess.check_output(['node', '--version'], stderr=subprocess.DEVNULL, text=True)
        return output.strip().lstrip('v')
    except:
        return None

def _get_mac_address():
    """获取 MAC 地址"""
    import uuid
    mac = uuid.getnode()
    return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
