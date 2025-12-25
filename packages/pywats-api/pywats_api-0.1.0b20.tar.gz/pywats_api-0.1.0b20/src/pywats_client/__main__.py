"""
pyWATS Client Entry Point

Run the client with:
    python -m pywats_client          # GUI mode (default)
    python -m pywats_client --no-gui # Headless mode
    
Or use CLI commands:
    pywats-client config show        # Show configuration
    pywats-client config init        # Initialize config
    pywats-client status             # Show status
    pywats-client start --daemon     # Run as daemon
    pywats-client start --api        # Run with HTTP control API

Or use the installed command:
    pywats-client
"""

import sys
import asyncio
import argparse
from pathlib import Path


def _check_gui_available() -> bool:
    """Check if Qt GUI is available"""
    try:
        import PySide6
        return True
    except ImportError:
        return False


def _run_gui_mode(config):
    """Run in GUI mode"""
    if not _check_gui_available():
        print("Error: GUI mode requires PySide6")
        print("Install with: pip install pywats-api[client]")
        print("Or run in headless mode: pywats-client --no-gui")
        sys.exit(1)
    
    from .gui.app import run_gui
    run_gui(config)


def _run_headless_mode(config):
    """Run in simple headless mode (legacy)"""
    from .core.client import WATSClient
    
    async def run_headless():
        client = WATSClient(config)
        try:
            await client.start()
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await client.stop()
    
    asyncio.run(run_headless())


def main():
    """Main entry point"""
    # Check if this is a CLI subcommand
    # CLI commands: config, status, test-connection, converters, start, stop, version
    cli_commands = ["config", "status", "test-connection", "converters", "start", "stop"]
    
    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        # Route to CLI handler
        from .control.cli import cli_main
        sys.exit(cli_main())
    
    # Legacy argument parsing for backward compatibility
    parser = argparse.ArgumentParser(
        description="pyWATS Client - WATS Test Report Management",
        epilog="""
CLI Commands (use 'pywats-client <command> --help' for details):
  config       Configuration management
  status       Show service status
  start        Start the service (with --daemon or --api options)
  stop         Stop a running daemon
  converters   Converter management
"""
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in headless mode without GUI"
    )
    parser.add_argument(
        "--instance-name",
        type=str,
        help="Instance name for this client"
    )
    parser.add_argument(
        "--service-address",
        type=str,
        help="WATS service address"
    )
    parser.add_argument(
        "--api-token",
        type=str,
        help="API token for authentication"
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit"
    )
    # New headless service options
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon (implies --no-gui)"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Enable HTTP control API (implies --no-gui)"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8765,
        help="HTTP API port (default: 8765)"
    )
    parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="HTTP API host (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        from . import __version__
        print(f"pyWATS Client v{__version__}")
        sys.exit(0)
    
    # Load or create configuration
    from .core.config import ClientConfig
    
    if args.config:
        config_path = Path(args.config)
        config = ClientConfig.load_or_create(config_path)
    else:
        # Use default config location
        config_dir = Path.home() / ".pywats_client"
        config_path = config_dir / "config.json"
        config = ClientConfig.load_or_create(config_path)
    
    # Apply command line overrides
    if args.instance_name:
        config.instance_name = args.instance_name
    if args.service_address:
        config.service_address = args.service_address
    if args.api_token:
        config.api_token = args.api_token
    
    # Determine run mode
    use_headless = args.no_gui or args.daemon or args.api
    
    if use_headless:
        if args.daemon or args.api:
            # Full headless service with API support
            from .control.service import HeadlessService, ServiceConfig
            
            service_config = ServiceConfig(
                enable_api=args.api,
                api_host=args.api_host,
                api_port=args.api_port,
                daemon=args.daemon,
            )
            
            service = HeadlessService(config, service_config)
            service.run()
        else:
            # Simple headless mode (legacy)
            _run_headless_mode(config)
    else:
        # GUI mode
        _run_gui_mode(config)


if __name__ == "__main__":
    main()
