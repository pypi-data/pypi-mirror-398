"""
Core module initialization
"""

from .config import ClientConfig, get_default_config_path
from .client import WATSClient
from .instance_manager import InstanceManager

__all__ = [
    "ClientConfig",
    "get_default_config_path",
    "WATSClient",
    "InstanceManager",
]
