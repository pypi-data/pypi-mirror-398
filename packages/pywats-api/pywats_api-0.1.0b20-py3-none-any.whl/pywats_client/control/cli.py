"""
Command-Line Interface for pyWATS Client

Provides CLI commands for headless configuration and control.

Usage:
    # Show current configuration
    pywats-client config show
    
    # Set configuration values
    pywats-client config set server_url https://wats.example.com
    pywats-client config set api_token YOUR_TOKEN
    pywats-client config set station_name MY_STATION
    
    # Get specific config value
    pywats-client config get server_url
    
    # Show service status
    pywats-client status
    
    # Test connection
    pywats-client test-connection
    
    # Manage converters
    pywats-client converters list
    pywats-client converters enable my_converter
    pywats-client converters disable my_converter
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import fields


class ConfigCLI:
    """CLI interface for configuration management"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize CLI with config path.
        
        Args:
            config_path: Path to config file. Defaults to ~/.pywats_client/config.json
        """
        if config_path is None:
            config_path = Path.home() / ".pywats_client" / "config.json"
        self.config_path = config_path
        self._config = None
    
    @property
    def config(self):
        """Lazy load configuration"""
        if self._config is None:
            from ..core.config import ClientConfig
            self._config = ClientConfig.load_or_create(self.config_path)
        return self._config
    
    def show_config(self, format: str = "table") -> None:
        """Display current configuration"""
        from ..core.config import ClientConfig
        
        config_dict = self.config.to_dict()
        
        if format == "json":
            print(json.dumps(config_dict, indent=2, default=str))
        elif format == "env":
            # Output as environment variables
            for key, value in config_dict.items():
                if not isinstance(value, (dict, list)):
                    env_key = f"PYWATS_{key.upper()}"
                    print(f'{env_key}="{value}"')
        else:
            # Table format
            print("\n" + "=" * 60)
            print("pyWATS Client Configuration")
            print("=" * 60)
            print(f"Config file: {self.config_path}")
            print("-" * 60)
            
            # Group settings
            groups = {
                "Instance": ["instance_id", "instance_name"],
                "Server": ["service_address", "api_token", "username"],
                "Station": ["station_name", "location", "purpose", "station_description"],
                "Paths": ["data_path", "reports_path", "queue_path"],
                "Converters": ["converters_enabled", "watch_folders"],
                "Logging": ["log_level", "log_file"],
            }
            
            for group_name, keys in groups.items():
                print(f"\n[{group_name}]")
                for key in keys:
                    if key in config_dict:
                        value = config_dict[key]
                        # Mask sensitive values
                        if key in ["api_token", "proxy_password"] and value:
                            display_value = value[:4] + "****" + value[-4:] if len(str(value)) > 8 else "****"
                        else:
                            display_value = value
                        print(f"  {key}: {display_value}")
            
            print("\n" + "=" * 60)
    
    def get_value(self, key: str) -> Any:
        """Get a specific configuration value"""
        config_dict = self.config.to_dict()
        if key in config_dict:
            return config_dict[key]
        else:
            # Try nested access with dot notation
            parts = key.split(".")
            value = config_dict
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    raise KeyError(f"Unknown configuration key: {key}")
            return value
    
    def set_value(self, key: str, value: str) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested values)
            value: Value to set (will be type-converted automatically)
        """
        # Type conversion based on current value type
        current = self.get_value(key) if self._key_exists(key) else None
        
        if current is not None:
            if isinstance(current, bool):
                value = value.lower() in ("true", "1", "yes", "on")
            elif isinstance(current, int):
                value = int(value)
            elif isinstance(current, float):
                value = float(value)
            elif isinstance(current, list):
                # Parse as JSON array or comma-separated
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    value = [v.strip() for v in value.split(",")]
        
        # Set the value
        setattr(self.config, key, value)
        self.config.save(self.config_path)
        print(f"✓ Set {key} = {value}")
    
    def _key_exists(self, key: str) -> bool:
        """Check if a config key exists"""
        try:
            self.get_value(key)
            return True
        except KeyError:
            return False
    
    def test_connection(self) -> bool:
        """Test connection to WATS server"""
        print("\nTesting connection to WATS server...")
        print(f"  Server: {self.config.service_address}")
        
        if not self.config.service_address:
            print("  ✗ No server address configured")
            return False
        
        if not self.config.api_token:
            print("  ✗ No API token configured")
            return False
        
        try:
            from pywats import pyWATS
            client = pyWATS(
                base_url=self.config.service_address,
                token=self.config.api_token
            )
            print("  ✓ Client initialized successfully")
            
            # Try a simple API call (pyWATS API is synchronous)
            try:
                version = client.app.get_version()
                print(f"  ✓ API connection successful (server version: {version})")
                return True
            except Exception as e:
                print(f"  ✗ API call failed: {e}")
                return False
                
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            return False
    
    def show_status(self) -> Dict[str, Any]:
        """Show current service status"""
        status = {
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "server_configured": bool(self.config.service_address),
            "token_configured": bool(self.config.api_token),
            "station_name": self.config.station_name or "(not set)",
            "instance_name": self.config.instance_name,
        }
        
        print("\n" + "=" * 50)
        print("pyWATS Client Status")
        print("=" * 50)
        
        for key, value in status.items():
            icon = "✓" if value not in [False, "(not set)", ""] else "✗"
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            print(f"  {icon} {key.replace('_', ' ').title()}: {value}")
        
        print("=" * 50)
        return status
    
    def list_converters(self) -> List[Dict[str, Any]]:
        """List available converters"""
        converters_dir = self.config.data_path / "converters"
        
        print("\n" + "=" * 50)
        print("Available Converters")
        print("=" * 50)
        
        if not converters_dir.exists():
            print("  (No converters directory found)")
            return []
        
        converters = []
        # Get list of enabled converters from config
        enabled_list = [c.name for c in self.config.converters if c.enabled]
        
        for py_file in converters_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            converter_name = py_file.stem
            enabled = converter_name in enabled_list
            
            converters.append({
                "name": converter_name,
                "path": str(py_file),
                "enabled": enabled,
            })
            
            icon = "✓" if enabled else "○"
            print(f"  {icon} {converter_name}")
            print(f"      Path: {py_file}")
        
        if not converters:
            print("  (No converters found)")
        
        print("=" * 50)
        return converters
    
    def enable_converter(self, name: str) -> None:
        """Enable a converter by name"""
        # Check if converter exists in config
        for conv in self.config.converters:
            if conv.name == name:
                conv.enabled = True
                self.config.save(self.config_path)
                print(f"✓ Enabled converter: {name}")
                return
        
        # Converter not in config, add it
        converters_dir = self.config.data_path / "converters"
        converter_path = converters_dir / f"{name}.py"
        
        if not converter_path.exists():
            print(f"✗ Converter not found: {name}")
            print(f"  Expected at: {converter_path}")
            return
        
        from ..core.config import ConverterConfig
        new_conv = ConverterConfig(
            name=name,
            module_path=str(converter_path),
            watch_folder=str(self.config.data_path / "watch" / name),
            enabled=True,
        )
        self.config.converters.append(new_conv)
        self.config.save(self.config_path)
        print(f"✓ Added and enabled converter: {name}")
    
    def disable_converter(self, name: str) -> None:
        """Disable a converter by name"""
        for conv in self.config.converters:
            if conv.name == name:
                conv.enabled = False
                self.config.save(self.config_path)
                print(f"✓ Disabled converter: {name}")
                return
        
        print(f"✗ Converter not found in config: {name}")
    
    def init_config(self, 
                    server_url: Optional[str] = None,
                    api_token: Optional[str] = None,
                    station_name: Optional[str] = None,
                    interactive: bool = True) -> None:
        """
        Initialize configuration interactively or with provided values.
        
        Args:
            server_url: WATS server URL
            api_token: API token
            station_name: Station name
            interactive: Prompt for missing values
        """
        print("\n" + "=" * 50)
        print("pyWATS Client Setup")
        print("=" * 50)
        
        # Server URL
        if server_url:
            self.config.service_address = server_url
        elif interactive and not self.config.service_address:
            url = input("WATS Server URL [https://wats.example.com]: ").strip()
            if url:
                self.config.service_address = url
        
        # API Token
        if api_token:
            self.config.api_token = api_token
        elif interactive and not self.config.api_token:
            import getpass
            token = getpass.getpass("API Token: ").strip()
            if token:
                self.config.api_token = token
        
        # Station Name
        if station_name:
            self.config.station_name = station_name
        elif interactive and not self.config.station_name:
            import socket
            default_station = socket.gethostname()
            name = input(f"Station Name [{default_station}]: ").strip()
            self.config.station_name = name or default_station
        
        # Save configuration
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.save(self.config_path)
        print(f"\n✓ Configuration saved to {self.config_path}")
        
        # Test connection
        if interactive:
            test = input("\nTest connection now? [Y/n]: ").strip().lower()
            if test != 'n':
                self.test_connection()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for CLI"""
    parser = argparse.ArgumentParser(
        prog="pywats-client",
        description="pyWATS Client - Headless Control Interface"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Config commands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_action")
    
    # config show
    show_parser = config_subparsers.add_parser("show", help="Show current configuration")
    show_parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "env"],
        default="table",
        help="Output format"
    )
    
    # config get
    get_parser = config_subparsers.add_parser("get", help="Get a configuration value")
    get_parser.add_argument("key", help="Configuration key")
    
    # config set
    set_parser = config_subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", help="Configuration key")
    set_parser.add_argument("value", help="Value to set")
    
    # config init
    init_parser = config_subparsers.add_parser("init", help="Initialize configuration")
    init_parser.add_argument("--server-url", help="WATS server URL")
    init_parser.add_argument("--api-token", help="API token")
    init_parser.add_argument("--station-name", help="Station name")
    init_parser.add_argument("--non-interactive", action="store_true",
                            help="Don't prompt for input")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show service status")
    
    # Test connection command
    test_parser = subparsers.add_parser("test-connection", help="Test server connection")
    
    # Converters commands
    conv_parser = subparsers.add_parser("converters", help="Converter management")
    conv_subparsers = conv_parser.add_subparsers(dest="conv_action")
    
    conv_subparsers.add_parser("list", help="List available converters")
    
    enable_parser = conv_subparsers.add_parser("enable", help="Enable a converter")
    enable_parser.add_argument("name", help="Converter name")
    
    disable_parser = conv_subparsers.add_parser("disable", help="Disable a converter")
    disable_parser.add_argument("name", help="Converter name")
    
    # Start command (headless service)
    start_parser = subparsers.add_parser("start", help="Start the service")
    start_parser.add_argument("--daemon", "-d", action="store_true",
                             help="Run as daemon/background process")
    start_parser.add_argument("--api", action="store_true",
                             help="Enable HTTP control API")
    start_parser.add_argument("--api-port", type=int, default=8765,
                             help="HTTP API port (default: 8765)")
    start_parser.add_argument("--api-host", default="127.0.0.1",
                             help="HTTP API host (default: 127.0.0.1)")
    start_parser.add_argument("--pid-file", type=str,
                             help="Path to PID file for daemon mode")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the service")
    stop_parser.add_argument("--pid-file", type=str,
                            help="Path to PID file")
    
    # Version command
    subparsers.add_parser("version", help="Show version")
    
    return parser


def cli_main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for CLI.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    # Determine config path
    config_path = None
    if parsed.config:
        config_path = Path(parsed.config)
    
    cli = ConfigCLI(config_path)
    
    try:
        if parsed.command == "config":
            if parsed.config_action == "show":
                cli.show_config(format=parsed.format)
            elif parsed.config_action == "get":
                value = cli.get_value(parsed.key)
                print(value)
            elif parsed.config_action == "set":
                cli.set_value(parsed.key, parsed.value)
            elif parsed.config_action == "init":
                cli.init_config(
                    server_url=parsed.server_url,
                    api_token=parsed.api_token,
                    station_name=parsed.station_name,
                    interactive=not parsed.non_interactive
                )
            else:
                parser.parse_args(["config", "--help"])
                
        elif parsed.command == "status":
            cli.show_status()
            
        elif parsed.command == "test-connection":
            success = cli.test_connection()
            return 0 if success else 1
            
        elif parsed.command == "converters":
            if parsed.conv_action == "list":
                cli.list_converters()
            elif parsed.conv_action == "enable":
                cli.enable_converter(parsed.name)
            elif parsed.conv_action == "disable":
                cli.disable_converter(parsed.name)
            else:
                parser.parse_args(["converters", "--help"])
                
        elif parsed.command == "start":
            from .service import HeadlessService, ServiceConfig
            
            service_config = ServiceConfig(
                enable_api=parsed.api,
                api_host=parsed.api_host,
                api_port=parsed.api_port,
                daemon=parsed.daemon,
                pid_file=parsed.pid_file,
            )
            
            service = HeadlessService(cli.config, service_config)
            service.run()
            
        elif parsed.command == "stop":
            from .service import HeadlessService
            HeadlessService.stop_daemon(parsed.pid_file)
            
        elif parsed.command == "version":
            from .. import __version__
            print(f"pyWATS Client v{__version__}")
            
        else:
            parser.print_help()
            
        return 0
        
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
