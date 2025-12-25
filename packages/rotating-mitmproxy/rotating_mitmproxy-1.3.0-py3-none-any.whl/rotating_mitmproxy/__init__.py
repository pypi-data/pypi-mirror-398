"""
Rotating mitmproxy - Smart proxy rotator with intelligent health monitoring.

A production-ready proxy rotation solution built on top of mitmproxy that provides:
- Intelligent proxy selection strategies
- Automatic health monitoring and failover
- Real-time statistics and monitoring
- High-performance proxy rotation

Example:
    Basic usage:
    
    >>> from rotating_mitmproxy import ProxyRotator
    >>> rotator = ProxyRotator(['proxy1.com:8080', 'proxy2.com:8080'])
    >>> # Use with mitmproxy addon system
    
    Command line usage:
    
    $ rotating-mitmproxy --proxy-list proxies.txt --port 8080
"""

from .thread_safe_rotator import ThreadSafeProxyRotator as ProxyRotator
from .config import Config
from .strategies import (
    SelectionStrategy,
    RoundRobinStrategy,
    RandomStrategy,
    FastestStrategy,
    SmartStrategy,
)
from .monitoring import MonitoringAddon, create_monitoring_addon
from .logging_addon import LoggingAddon, create_logging_addon

__version__ = "1.3.0"
__author__ = "importal"
__email__ = "xychen@msn.com"

__all__ = [
    "ProxyRotator",
    "Config",
    "SelectionStrategy",
    "RoundRobinStrategy",
    "RandomStrategy",
    "FastestStrategy",
    "SmartStrategy",
    "MonitoringAddon",
    "create_monitoring_addon",
    "LoggingAddon",
    "create_logging_addon",
]

