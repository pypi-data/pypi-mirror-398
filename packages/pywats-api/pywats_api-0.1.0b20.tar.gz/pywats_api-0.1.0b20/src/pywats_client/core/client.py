"""
Main WATS Client class

Orchestrates all client services including:
- Connection management
- Process synchronization
- Offline report queue
- Converter management
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from datetime import datetime

from .config import ClientConfig
from .instance_manager import InstanceLock
from ..services.connection import ConnectionService, ConnectionStatus
from ..services.process_sync import ProcessSyncService
from ..services.report_queue import ReportQueueService
from ..services.converter_manager import ConverterManager

logger = logging.getLogger(__name__)


class ClientStatus(Enum):
    """Overall client status"""
    STOPPED = "Stopped"
    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    ERROR = "Error"


class WATSClient:
    """
    Main pyWATS Client class.
    
    Manages all client services and provides a unified interface
    for controlling the client either programmatically or via GUI.
    
    Usage:
        config = ClientConfig.load("config.json")
        client = WATSClient(config)
        
        # Start all services
        await client.start()
        
        # Or run in blocking mode
        client.run()
    """
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self._status = ClientStatus.STOPPED
        self._lock: Optional[InstanceLock] = None
        
        # Services
        self._connection: Optional[ConnectionService] = None
        self._process_sync: Optional[ProcessSyncService] = None
        self._report_queue: Optional[ReportQueueService] = None
        self._converter_manager: Optional[ConverterManager] = None
        
        # Event loop for async operations
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        
        # Callbacks for status updates
        self._status_callbacks: List[Callable[[ClientStatus], None]] = []
        self._connection_callbacks: List[Callable[[ConnectionStatus], None]] = []
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging based on config"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Create formatter
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
        
        # Configure root logger for pywats_client
        client_logger = logging.getLogger('pywats_client')
        client_logger.setLevel(log_level)
        client_logger.addHandler(console_handler)
        client_logger.addHandler(file_handler)
    
    @property
    def status(self) -> ClientStatus:
        """Get current client status"""
        return self._status
    
    @status.setter
    def status(self, value: ClientStatus) -> None:
        """Set status and notify callbacks"""
        if self._status != value:
            self._status = value
            for callback in self._status_callbacks:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
    
    @property
    def connection_status(self) -> ConnectionStatus:
        """Get current connection status"""
        if self._connection:
            return self._connection.status
        return ConnectionStatus.DISCONNECTED
    
    @property
    def is_online(self) -> bool:
        """Check if client is connected to server"""
        return self.connection_status == ConnectionStatus.ONLINE
    
    def on_status_change(self, callback: Callable[[ClientStatus], None]) -> None:
        """Register callback for status changes"""
        self._status_callbacks.append(callback)
    
    def on_connection_change(self, callback: Callable[[ConnectionStatus], None]) -> None:
        """Register callback for connection status changes"""
        self._connection_callbacks.append(callback)
    
    async def start(self) -> bool:
        """
        Start all client services.
        
        Returns True if started successfully.
        """
        if self._status == ClientStatus.RUNNING:
            logger.warning("Client already running")
            return True
        
        self.status = ClientStatus.STARTING
        logger.info(f"Starting WATS Client (Instance: {self.config.instance_id})")
        
        try:
            # Acquire instance lock
            self._lock = InstanceLock(self.config.instance_id)
            if not self._lock.acquire(self.config.instance_name):
                raise RuntimeError(f"Instance {self.config.instance_id} is already running")
            
            # Initialize services
            self._connection = ConnectionService(
                service_address=self.config.service_address,
                api_token=self.config.api_token,
                proxy_config=self.config.proxy if self.config.proxy.enabled else None
            )
            self._connection.on_status_change(self._on_connection_status_change)
            
            # Initialize process sync service
            if self.config.process_sync_enabled:
                self._process_sync = ProcessSyncService(
                    connection=self._connection,
                    sync_interval=self.config.sync_interval_seconds
                )
            
            # Initialize report queue service
            if self.config.offline_queue_enabled:
                self._report_queue = ReportQueueService(
                    connection=self._connection,
                    reports_folder=self.config.get_reports_path(),
                    max_retries=self.config.max_retry_attempts,
                    retry_interval=self.config.retry_interval_seconds
                )
            
            # Initialize converter manager
            if self.config.converters_enabled and self.config.converters:
                self._converter_manager = ConverterManager(
                    converters=self.config.converters,
                    report_queue=self._report_queue
                )
            
            # Start connection service
            await self._connection.connect()
            
            # Start other services
            if self._process_sync:
                await self._process_sync.start()
            
            if self._report_queue:
                await self._report_queue.start()
            
            if self._converter_manager:
                await self._converter_manager.start()
            
            self._running = True
            self.status = ClientStatus.RUNNING
            logger.info("WATS Client started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start client: {e}")
            self.status = ClientStatus.ERROR
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop all client services"""
        if self._status == ClientStatus.STOPPED:
            return
        
        self.status = ClientStatus.STOPPING
        logger.info("Stopping WATS Client...")
        
        self._running = False
        
        # Stop services in reverse order
        if self._converter_manager:
            await self._converter_manager.stop()
            self._converter_manager = None
        
        if self._report_queue:
            await self._report_queue.stop()
            self._report_queue = None
        
        if self._process_sync:
            await self._process_sync.stop()
            self._process_sync = None
        
        if self._connection:
            await self._connection.disconnect()
            self._connection = None
        
        # Release instance lock
        if self._lock:
            self._lock.release()
            self._lock = None
        
        self.status = ClientStatus.STOPPED
        logger.info("WATS Client stopped")
    
    def _on_connection_status_change(self, status: ConnectionStatus) -> None:
        """Handle connection status changes"""
        for callback in self._connection_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in connection callback: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to WATS server"""
        if not self._connection:
            # Create temporary connection for testing
            conn = ConnectionService(
                service_address=self.config.service_address,
                api_token=self.config.api_token,
                proxy_config=self.config.proxy if self.config.proxy.enabled else None
            )
            try:
                return await conn.test_connection()
            finally:
                await conn.disconnect()
        
        return await self._connection.test_connection()
    
    def run(self) -> None:
        """
        Run the client in blocking mode.
        
        This is useful for running the client as a service without GUI.
        """
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Start the client
            self._loop.run_until_complete(self.start())
            
            # Run until stopped
            while self._running:
                self._loop.run_until_complete(asyncio.sleep(1))
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            if self._loop:
                self._loop.run_until_complete(self.stop())
                self._loop.close()
    
    # Service access methods
    
    def get_processes(self) -> List[Dict[str, Any]]:
        """Get cached process data"""
        if self._process_sync:
            return self._process_sync.get_processes()
        return []
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get report queue status"""
        if self._report_queue:
            return self._report_queue.get_status()
        return {"pending": 0, "failed": 0}
    
    def get_converter_status(self) -> List[Dict[str, Any]]:
        """Get converter status"""
        if self._converter_manager:
            return self._converter_manager.get_status()
        return []
    
    async def submit_report(self, report_data: Dict[str, Any]) -> bool:
        """
        Submit a report to WATS.
        
        If offline, the report will be queued for later submission.
        """
        if self._report_queue:
            return await self._report_queue.submit(report_data)
        return False
    
    def update_config(self, **kwargs) -> None:
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.config.save()
    
    async def refresh_converters(self) -> None:
        """Refresh/reload converters"""
        if self._converter_manager:
            await self._converter_manager.reload_converters()
