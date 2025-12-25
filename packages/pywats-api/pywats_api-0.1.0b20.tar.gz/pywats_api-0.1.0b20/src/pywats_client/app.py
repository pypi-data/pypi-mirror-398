"""
pyWATS Service Application - Base Application Without GUI

This is the core application that can run as a service or daemon.
It handles:
- Server connection management
- Process/data synchronization
- Offline report queuing
- File monitoring and conversion
- Serial number reservation (persistent offline)
- Settings persistence

The GUI is optional and runs on top of this application.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from datetime import datetime
from contextlib import asynccontextmanager

from pywats import pyWATS
from pywats.core.exceptions import NotFoundError, PyWATSError

from .core.config import ClientConfig
from .core.instance_manager import InstanceLock
from .services.connection import ConnectionService, ConnectionStatus
from .services.process_sync import ProcessSyncService
from .services.report_queue import ReportQueueService
from .services.converter_manager import ConverterManager

logger = logging.getLogger(__name__)


class ApplicationStatus(Enum):
    """Overall application status"""
    STOPPED = "Stopped"
    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    ERROR = "Error"


class ApplicationError(Exception):
    """Base application error"""
    pass


class ServiceError(ApplicationError):
    """Error from a service"""
    pass


class pyWATSApplication:
    """
    Base pyWATS Service Application (no GUI).
    
    Manages all client services and provides a unified interface
    for controlling the application either programmatically or via GUI.
    
    Features:
    - Service lifecycle management (start, stop, restart)
    - Connection monitoring and auto-reconnection
    - Persistent settings and configuration
    - Offline report queue management
    - Serial number reservation (persistent)
    - File monitoring for auto-conversion
    - Error handling with detailed error codes
    
    Usage:
        config = ClientConfig.load("config.json")
        app = pyWATSApplication(config)
        
        # Add status callbacks
        app.on_status_changed(lambda status: print(f"Status: {status}"))
        
        # Start all services
        await app.start()
        
        # Or run in blocking mode
        app.run()
    """
    
    def __init__(self, config: ClientConfig):
        """
        Initialize the application.
        
        Args:
            config: ClientConfig instance
            
        Raises:
            ApplicationError: If initialization fails
        """
        self.config = config
        self._status = ApplicationStatus.STOPPED
        self._lock: Optional[InstanceLock] = None
        self._wats_client: Optional[pyWATS] = None
        
        # Services
        self._connection: Optional[ConnectionService] = None
        self._process_sync: Optional[ProcessSyncService] = None
        self._report_queue: Optional[ReportQueueService] = None
        self._converter_manager: Optional[ConverterManager] = None
        
        # Async runtime
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Callbacks
        self._status_callbacks: List[Callable[[ApplicationStatus], None]] = []
        self._error_callbacks: List[Callable[[ApplicationError], None]] = []
        
        # Setup logging
        self._setup_logging()
        logger.info(f"pyWATS Application initialized (v1.0.0)")
        
        # Initialize WATS client if we have credentials from login
        if config.service_address and config.api_token:
            self._wats_client = pyWATS(
                base_url=config.service_address,
                token=config.api_token
            )
            logger.info("WATS client initialized from credentials")
    
    def _setup_logging(self) -> None:
        """Configure logging based on config"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # File handler
        log_path = self.config.get_reports_path().parent / self.config.log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Configure loggers
        for logger_name in ['pywats_client', 'pywats', 'pywats_client.services']:
            app_logger = logging.getLogger(logger_name)
            app_logger.setLevel(log_level)
            app_logger.addHandler(console_handler)
            app_logger.addHandler(file_handler)
    
    # =========================================================================
    # Status Management
    # =========================================================================
    
    @property
    def status(self) -> ApplicationStatus:
        """Get current application status"""
        return self._status
    
    def _set_status(self, status: ApplicationStatus) -> None:
        """Set status and notify callbacks"""
        if self._status != status:
            old_status = self._status
            self._status = status
            logger.info(f"Application status changed: {old_status.value} -> {status.value}")
            for callback in self._status_callbacks:
                try:
                    callback(status)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
    
    def on_status_changed(self, callback: Callable[[ApplicationStatus], None]) -> None:
        """
        Register callback for status changes.
        
        Args:
            callback: Function to call with new status
        """
        self._status_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[ApplicationError], None]) -> None:
        """
        Register callback for errors.
        
        Args:
            callback: Function to call with error
        """
        self._error_callbacks.append(callback)
    
    def _handle_error(self, error: ApplicationError) -> None:
        """Handle application error"""
        logger.error(f"Application error: {error}")
        self._set_status(ApplicationStatus.ERROR)
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    # =========================================================================
    # Service Lifecycle
    # =========================================================================
    
    async def start(self) -> None:
        """
        Start all services asynchronously.
        
        Raises:
            ServiceError: If service startup fails
        """
        if self._status != ApplicationStatus.STOPPED:
            raise ApplicationError(f"Cannot start application in {self._status.value} state")
        
        self._set_status(ApplicationStatus.STARTING)
        
        try:
            # Check instance lock
            self._lock = InstanceLock(self.config.instance_id)
            if not self._lock.acquire():
                raise ServiceError("Another instance of pyWATS Client is already running")
            
            logger.info("Instance lock acquired")
            
            # Initialize WATS client
            self._wats_client = pyWATS(
                base_url=self.config.server_url,
                token=self.config.api_token
            )
            
            # Initialize services
            logger.info("Initializing services...")
            self._connection = ConnectionService(
                service_address=self.config.server_url,
                api_token=self.config.api_token,
                proxy_config=self.config.proxy,
                check_interval=self.config.connection_check_interval
            )
            
            self._process_sync = ProcessSyncService(
                wats_client=self._wats_client,
                data_path=self.config.get_data_path()
            )
            
            self._report_queue = ReportQueueService(
                wats_client=self._wats_client,
                queue_path=self.config.get_queue_path()
            )
            
            self._converter_manager = ConverterManager(
                converters_path=self.config.get_converters_path()
            )
            
            # Start services
            logger.info("Starting services...")
            await self._connection.start()
            await self._process_sync.start()
            await self._report_queue.start()
            
            logger.info("All services started successfully")
            self._set_status(ApplicationStatus.RUNNING)
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            self._set_status(ApplicationStatus.ERROR)
            raise ServiceError(f"Service startup failed: {e}") from e
    
    async def stop(self) -> None:
        """
        Stop all services gracefully.
        
        Raises:
            ServiceError: If service shutdown fails
        """
        if self._status == ApplicationStatus.STOPPED:
            return
        
        self._set_status(ApplicationStatus.STOPPING)
        self._running = False
        
        try:
            logger.info("Stopping services...")
            
            # Stop services in reverse order
            if self._converter_manager:
                await self._converter_manager.stop()
            
            if self._report_queue:
                await self._report_queue.stop()
            
            if self._process_sync:
                await self._process_sync.stop()
            
            if self._connection:
                await self._connection.stop()
            
            # Cancel remaining tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Release instance lock
            if self._lock:
                self._lock.release()
                logger.info("Instance lock released")
            
            logger.info("All services stopped")
            self._set_status(ApplicationStatus.STOPPED)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise ServiceError(f"Service shutdown failed: {e}") from e
    
    async def restart(self) -> None:
        """
        Restart all services.
        
        Raises:
            ServiceError: If restart fails
        """
        logger.info("Restarting services...")
        await self.stop()
        await self.start()
    
    def run(self) -> None:
        """
        Run the application in blocking mode.
        
        This is a convenience method for simple scripts.
        For production use, use start/stop with an event loop manager.
        """
        self._running = True
        
        # Create or get event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self._loop = loop
        
        try:
            # Start application
            loop.run_until_complete(self.start())
            
            # Keep running until interrupted
            while self._running:
                loop.run_until_complete(asyncio.sleep(1))
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            self._handle_error(ApplicationError(str(e)))
        
        finally:
            # Cleanup
            try:
                loop.run_until_complete(self.stop())
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    # =========================================================================
    # Service Access
    # =========================================================================
    
    @property
    def wats_client(self) -> Optional[pyWATS]:
        """Get WATS API client"""
        return self._wats_client
    
    @property
    def connection(self) -> Optional[ConnectionService]:
        """Get connection service"""
        return self._connection
    
    @property
    def process_sync(self) -> Optional[ProcessSyncService]:
        """Get process synchronization service"""
        return self._process_sync
    
    @property
    def report_queue(self) -> Optional[ReportQueueService]:
        """Get offline report queue service"""
        return self._report_queue
    
    @property
    def converter_manager(self) -> Optional[ConverterManager]:
        """Get converter manager"""
        return self._converter_manager
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def is_online(self) -> bool:
        """Check if currently connected to server"""
        return (
            self._connection is not None and
            self._connection.status == ConnectionStatus.ONLINE
        )
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get offline report queue status"""
        if self._report_queue is None:
            return {}
        return {
            "pending_reports": len(self._report_queue.queue),
            "pending_files": len(self._report_queue.pending_files),
        }
    
    def get_connection_status(self) -> Optional[str]:
        """Get human-readable connection status"""
        if self._connection:
            return self._connection.status.value
        return None
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        if self._connection:
            return self._connection.last_error
        return None
