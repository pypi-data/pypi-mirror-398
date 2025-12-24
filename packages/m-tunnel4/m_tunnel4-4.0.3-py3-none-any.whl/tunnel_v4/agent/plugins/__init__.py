"""
Plugins for Tunnel System Agent
"""
from .base import Plugin
from .exec import ExecPlugin
from .socks5 import SOCKS5Plugin

__all__ = ['Plugin', 'ExecPlugin', 'SOCKS5Plugin']
