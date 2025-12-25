"""
pyWATS Client Control Module

Provides headless control interfaces for running pyWATS Client
on systems without Qt/GUI support (e.g., Raspberry Pi, servers).

Control Interfaces:
- CLI: Command-line interface for configuration and control
- HTTP API: Simple REST API for remote management
- Service: Daemon/service mode runner

Usage:
    # CLI commands
    pywats-client config show
    pywats-client config set server_url https://wats.example.com
    pywats-client status
    pywats-client start --daemon
    
    # HTTP API (optional)
    pywats-client start --api --api-port 8765
"""

from .cli import cli_main, ConfigCLI
from .service import HeadlessService, ServiceConfig

__all__ = [
    "cli_main",
    "ConfigCLI",
    "HeadlessService",
    "ServiceConfig",
]
