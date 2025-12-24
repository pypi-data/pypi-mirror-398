"""
配置管理
"""
import os
import yaml
import sys


CONFIG_FILE = os.path.expanduser('~/.tunnel/config.yaml')


def ensure_config_dir():
    """确保配置目录存在"""
    config_dir = os.path.dirname(CONFIG_FILE)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


def load_config():
    """加载配置"""
    if not os.path.exists(CONFIG_FILE):
        return {}
    
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f) or {}


def save_config(config):
    """保存配置"""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def set_config(key, value):
    """设置配置项"""
    try:
        config = load_config()
        
        # 转换 key 中的 - 为 _
        key = key.replace('-', '_')
        
        config[key] = value
        save_config(config)
        
        print(f'✓ Config updated: {key} = {value}')
        print(f'  Config file: {CONFIG_FILE}')
        
        return 0
    except Exception as e:
        print(f'✗ Error: {e}', file=sys.stderr)
        return 1


def show_config():
    """显示配置"""
    try:
        config = load_config()
        
        if not config:
            print('Configuration: (empty)')
            print(f'  Config file: {CONFIG_FILE}')
            return 0
        
        print('Configuration:')
        for key, value in config.items():
            print(f'  {key}: {value}')
        print(f'\n  Config file: {CONFIG_FILE}')
        
        return 0
    except Exception as e:
        print(f'✗ Error: {e}', file=sys.stderr)
        return 1


def get_config(key, default=None):
    """获取配置项"""
    config = load_config()
    return config.get(key.replace('-', '_'), default)
