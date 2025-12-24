"""
IP 信息收集模块
"""
import requests
import socket
import logging

logger = logging.getLogger(__name__)


def get_ip_info(timeout=5):
    """
    获取节点 IP 和地理信息
    
    优先使用 ipinfo.io 获取完整信息，失败时降级到本地 IP
    
    Returns:
        dict: IP 信息
            {
                'ip': str,
                'country': str,
                'region': str,
                'city': str,
                'latitude': float,
                'longitude': float,
                'isp': str,
                'asn': str
            }
    """
    try:
        # 方式 1: 使用 ipinfo.io (免费，无需 API key)
        logger.debug('Fetching IP info from ipinfo.io...')
        resp = requests.get('https://ipinfo.io/json', timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        
        # 解析位置信息
        loc = data.get('loc', '0,0').split(',')
        latitude = float(loc[0]) if len(loc) > 0 else 0.0
        longitude = float(loc[1]) if len(loc) > 1 else 0.0
        
        # 解析 ISP 信息
        org = data.get('org', '')
        asn = org.split(' ')[0] if org else ''
        isp = ' '.join(org.split(' ')[1:]) if org and ' ' in org else org
        
        ip_info = {
            'ip': data.get('ip'),
            'country': data.get('country'),
            'region': data.get('region'),
            'city': data.get('city'),
            'latitude': latitude,
            'longitude': longitude,
            'isp': isp,
            'asn': asn
        }
        
        logger.info(f'IP info collected: {ip_info["ip"]} ({ip_info["country"]}, {ip_info["isp"]})')
        return ip_info
        
    except requests.exceptions.Timeout:
        logger.warning(f'IP info request timeout after {timeout}s, using fallback')
    except requests.exceptions.RequestException as e:
        logger.warning(f'Failed to fetch IP info from ipinfo.io: {e}')
    except Exception as e:
        logger.warning(f'Error parsing IP info: {e}')
    
    # 降级：只获取本地 IP
    return _get_fallback_ip_info()


def _get_fallback_ip_info():
    """
    降级方案：获取本地 IP
    
    Returns:
        dict: 基础 IP 信息
    """
    try:
        # 获取本地 IP（通过连接外部地址）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        logger.info(f'Using local IP: {local_ip}')
        
        return {
            'ip': local_ip,
            'country': None,
            'region': None,
            'city': None,
            'latitude': None,
            'longitude': None,
            'isp': None,
            'asn': None
        }
    except Exception as e:
        logger.warning(f'Failed to get local IP: {e}')
        return {
            'ip': 'unknown',
            'country': None,
            'region': None,
            'city': None,
            'latitude': None,
            'longitude': None,
            'isp': None,
            'asn': None
        }


def format_ip_info(ip_info):
    """
    格式化 IP 信息用于日志显示
    
    Args:
        ip_info: IP 信息字典
        
    Returns:
        str: 格式化的字符串
    """
    parts = [ip_info.get('ip', 'unknown')]
    
    if ip_info.get('country'):
        parts.append(ip_info['country'])
    
    if ip_info.get('city'):
        parts.append(ip_info['city'])
    
    if ip_info.get('isp'):
        parts.append(ip_info['isp'])
    
    return ' / '.join(parts)
