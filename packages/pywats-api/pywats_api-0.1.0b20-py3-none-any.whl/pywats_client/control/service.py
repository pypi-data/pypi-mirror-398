"""
Headless Service Runner for pyWATS Client

Provides daemon/service mode for running pyWATS Client without GUI
on servers, embedded systems (Raspberry Pi), and headless environments.

Features:
- Daemon mode with PID file management
- Signal handling for graceful shutdown
- Optional HTTP control API
- Watchdog for service restart on failure
- systemd integration support

Usage:
    # Run in foreground
    python -m pywats_client.control.service
    
    # Run as daemon
    python -m pywats_client.control.service --daemon
    
    # With HTTP API
    python -m pywats_client.control.service --api --api-port 8765
"""

import asyncio
import logging
import os
import signal
import sys
import atexit
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..core.config import ClientConfig

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for headless service"""
    # API settings
    enable_api: bool = False
    api_host: str = "127.0.0.1"
    api_port: int = 8765
    api_key: Optional[str] = None
    
    # Daemon settings
    daemon: bool = False
    pid_file: Optional[str] = None
    
    # Service behavior
    restart_on_failure: bool = True
    restart_delay: int = 5  # seconds
    max_restarts: int = 5
    
    # Watchdog
    watchdog_interval: int = 30  # seconds
    
    # Logging
    log_to_file: bool = True
    log_file: str = "pywats_service.log"


class HeadlessService:
    """
    Headless service runner for pyWATS Client.
    
    Manages the pyWATSApplication lifecycle without any GUI dependencies.
    Can run as a foreground process or daemon.
    
    Usage:
        from pywats_client.core.config import ClientConfig
        from pywats_client.control.service import HeadlessService, ServiceConfig
        
        config = ClientConfig.load("config.json")
        service_config = ServiceConfig(enable_api=True)
        
        service = HeadlessService(config, service_config)
        service.run()
    """
    
    def __init__(self, client_config: "ClientConfig", service_config: Optional[ServiceConfig] = None):
        """
        Initialize headless service.
        
        Args:
            client_config: Client configuration
            service_config: Service runtime configuration
        """
        self.client_config = client_config
        self.service_config = service_config or ServiceConfig()
        
        self._app = None
        self._api_server = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._restart_count = 0
        self._log_file = None  # For daemon mode log file handle
        
        # Setup signal handlers
        self._setup_signals()
    
    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        if sys.platform != "win32":
            # Unix signals
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGHUP, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating shutdown...")
        self._running = False
        
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
    
    def _setup_logging(self) -> None:
        """Configure logging for headless operation"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler (useful even in daemon mode for systemd journal)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        handlers = [console_handler]
        
        # File handler if enabled
        if self.service_config.log_to_file:
            log_path = Path(self.client_config.data_path) / self.service_config.log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.client_config.log_level.upper(), logging.INFO),
            handlers=handlers
        )
    
    def _daemonize(self) -> None:
        """
        Daemonize the process (Unix only).
        
        Uses double-fork method for proper daemon behavior.
        """
        if sys.platform == "win32":
            logger.warning("Daemon mode not supported on Windows, running in foreground")
            return
        
        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            logger.error(f"First fork failed: {e}")
            sys.exit(1)
        
        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            logger.error(f"Second fork failed: {e}")
            sys.exit(1)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())
        
        # Redirect stdout/stderr to log file
        if self.service_config.log_to_file:
            log_path = Path(self.client_config.data_path) / self.service_config.log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_file = open(log_path, 'a+')
            os.dup2(self._log_file.fileno(), sys.stdout.fileno())
            os.dup2(self._log_file.fileno(), sys.stderr.fileno())
        
        # Write PID file
        self._write_pid_file()
        
        # Register cleanup
        atexit.register(self._cleanup_pid_file)
    
    def _write_pid_file(self) -> None:
        """Write PID to file"""
        pid_file = self._get_pid_file_path()
        if pid_file:
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"PID file written: {pid_file}")
    
    def _cleanup_pid_file(self) -> None:
        """Remove PID file on exit"""
        pid_file = self._get_pid_file_path()
        if pid_file and pid_file.exists():
            pid_file.unlink()
            logger.info("PID file removed")
    
    def _get_pid_file_path(self) -> Optional[Path]:
        """Get PID file path"""
        if self.service_config.pid_file:
            return Path(self.service_config.pid_file)
        if self.service_config.daemon:
            return Path(self.client_config.data_path) / "pywats_client.pid"
        return None
    
    def _start_api_server(self) -> None:
        """Start HTTP control API if enabled"""
        if not self.service_config.enable_api:
            return
        
        from .http_api import ControlAPIServer, APIConfig
        
        api_config = APIConfig(
            host=self.service_config.api_host,
            port=self.service_config.api_port,
            api_key=self.service_config.api_key,
        )
        
        self._api_server = ControlAPIServer(
            self.client_config,
            api_config,
            self._app
        )
        self._api_server.start(blocking=False)
        logger.info(f"Control API started on http://{api_config.host}:{api_config.port}")
    
    def _stop_api_server(self) -> None:
        """Stop HTTP control API"""
        if self._api_server:
            self._api_server.stop()
            self._api_server = None
    
    async def _run_app(self) -> None:
        """Run the main application loop"""
        from ..app import pyWATSApplication, ApplicationStatus
        
        self._app = pyWATSApplication(self.client_config)
        
        # Update API server with app reference
        if self._api_server:
            self._api_server.set_app(self._app)
        
        try:
            logger.info("Starting pyWATS Application...")
            await self._app.start()
            logger.info("pyWATS Application started successfully")
            
            # Main loop - wait for shutdown signal
            while self._running:
                await asyncio.sleep(1)
                
                # Watchdog check
                if self._app.status == ApplicationStatus.ERROR:
                    logger.warning("Application in error state")
                    if self.service_config.restart_on_failure:
                        if self._restart_count < self.service_config.max_restarts:
                            logger.info(f"Attempting restart ({self._restart_count + 1}/{self.service_config.max_restarts})...")
                            await asyncio.sleep(self.service_config.restart_delay)
                            await self._app.restart()
                            self._restart_count += 1
                        else:
                            logger.error("Max restarts exceeded, stopping service")
                            self._running = False
                    else:
                        self._running = False
                else:
                    # Reset restart count on successful operation
                    self._restart_count = 0
                    
        except Exception as e:
            logger.exception(f"Application error: {e}")
        finally:
            logger.info("Stopping pyWATS Application...")
            if self._app:
                await self._app.stop()
            logger.info("pyWATS Application stopped")
    
    def run(self) -> None:
        """
        Run the headless service.
        
        This is the main entry point. Handles:
        - Daemonization (if configured)
        - Logging setup
        - API server startup
        - Main application loop
        - Graceful shutdown
        """
        # Daemonize if requested
        if self.service_config.daemon:
            self._daemonize()
        
        # Setup logging
        self._setup_logging()
        
        logger.info("=" * 60)
        logger.info("pyWATS Client Headless Service Starting")
        logger.info("=" * 60)
        logger.info(f"Instance: {self.client_config.instance_name}")
        logger.info(f"Server: {self.client_config.service_address or '(not configured)'}")
        logger.info(f"Station: {self.client_config.station_name or '(not configured)'}")
        logger.info(f"Daemon mode: {self.service_config.daemon}")
        logger.info(f"API enabled: {self.service_config.enable_api}")
        
        self._running = True
        
        # Start API server
        self._start_api_server()
        
        # Run event loop
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._run_app())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.exception(f"Service error: {e}")
        finally:
            # Cleanup
            self._stop_api_server()
            self._cleanup_pid_file()
            
            if self._loop:
                self._loop.close()
            
            logger.info("pyWATS Client Headless Service Stopped")
    
    @staticmethod
    def stop_daemon(pid_file: Optional[str] = None) -> None:
        """
        Stop a running daemon by PID file.
        
        Args:
            pid_file: Path to PID file. If None, uses default location.
        """
        if pid_file is None:
            pid_file = Path.home() / ".pywats_client" / "pywats_client.pid"
        else:
            pid_file = Path(pid_file)
        
        if not pid_file.exists():
            print(f"PID file not found: {pid_file}")
            return
        
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            
            print(f"Stopping daemon (PID {pid})...")
            os.kill(pid, signal.SIGTERM)
            print("Stop signal sent")
            
        except ProcessLookupError:
            print(f"Process {pid} not found, removing stale PID file")
            pid_file.unlink()
        except Exception as e:
            print(f"Error stopping daemon: {e}")
    
    @staticmethod
    def get_status(pid_file: Optional[str] = None) -> dict:
        """
        Get status of daemon by PID file.
        
        Args:
            pid_file: Path to PID file. If None, uses default location.
            
        Returns:
            Status dictionary with 'running', 'pid', etc.
        """
        if pid_file is None:
            pid_file = Path.home() / ".pywats_client" / "pywats_client.pid"
        else:
            pid_file = Path(pid_file)
        
        status = {
            "running": False,
            "pid": None,
            "pid_file": str(pid_file),
        }
        
        if not pid_file.exists():
            return status
        
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            
            status["pid"] = pid
            
            # Check if process is running
            try:
                os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
                status["running"] = True
            except ProcessLookupError:
                # Process not running, stale PID file
                pass
            except PermissionError:
                # Process exists but we can't signal it (different user)
                status["running"] = True
                
        except Exception:
            pass
        
        return status


# Entry point for direct execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="pyWATS Client Headless Service")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    parser.add_argument("--api", action="store_true", help="Enable HTTP control API")
    parser.add_argument("--api-port", type=int, default=8765, help="API port")
    parser.add_argument("--api-host", default="127.0.0.1", help="API host")
    parser.add_argument("--pid-file", help="PID file path")
    parser.add_argument("--stop", action="store_true", help="Stop running daemon")
    parser.add_argument("--status", action="store_true", help="Show daemon status")
    
    args = parser.parse_args()
    
    # Handle stop/status commands
    if args.stop:
        HeadlessService.stop_daemon(args.pid_file)
        sys.exit(0)
    
    if args.status:
        status = HeadlessService.get_status(args.pid_file)
        print(f"Running: {status['running']}")
        if status['pid']:
            print(f"PID: {status['pid']}")
        print(f"PID file: {status['pid_file']}")
        sys.exit(0)
    
    # Load configuration
    from ..core.config import ClientConfig
    
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = Path.home() / ".pywats_client" / "config.json"
    
    client_config = ClientConfig.load_or_create(config_path)
    
    # Create service config
    service_config = ServiceConfig(
        enable_api=args.api,
        api_host=args.api_host,
        api_port=args.api_port,
        daemon=args.daemon,
        pid_file=args.pid_file,
    )
    
    # Run service
    service = HeadlessService(client_config, service_config)
    service.run()
