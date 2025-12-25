"""
Example: Complete pyWATS Service Application

This example shows how to use the refactored pyWATS Client architecture
to build a complete service application with:
- Base app layer (no GUI)
- Settings persistence
- Serial number management
- File monitoring
- Graceful shutdown
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from pywats_client import (
    pyWATSApplication,
    ApplicationStatus,
    ApplicationError,
    SettingsManager,
    ApplicationSettings,
    MonitorFolder,
    SerialNumberManager,
    FileMonitor,
    MonitorRule,
    FileEventType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceApplication:
    """
    Complete service application combining all pyWATS Client components.
    
    This can run as:
    - A Windows Service
    - A systemd service
    - A standalone daemon
    - A foreground console application
    """
    
    def __init__(self, config_dir: Path = None):
        """
        Initialize service application.
        
        Args:
            config_dir: Directory for configuration files
        """
        self.config_dir = config_dir or Path.cwd() / "pywats_config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.app: Optional[pyWATSApplication] = None
        self.settings_mgr = SettingsManager(config_dir=self.config_dir)
        self.serial_mgr = SerialNumberManager(
            storage_path=self.config_dir / "serials.json"
        )
        self.file_monitor = FileMonitor(check_interval=2)
        
        # Load settings
        self.settings = self.settings_mgr.load()
        
        # State
        self._running = False
        self._last_sync_time = None
    
    async def initialize(self) -> None:
        """Initialize the application"""
        logger.info("Initializing service application...")
        
        try:
            # Validate settings
            valid, errors = self.settings_mgr.validate(self.settings)
            if not valid:
                logger.error(f"Settings validation failed: {errors}")
                raise ApplicationError(f"Invalid settings: {errors}")
            
            # Create base application
            from pywats_client.core.config import ClientConfig
            config = ClientConfig(
                instance_id=self.settings.server_url,
                server_url=self.settings.server_url,
                api_token=self.settings.api_token,
            )
            
            self.app = pyWATSApplication(config)
            
            # Setup application callbacks
            self.app.on_status_changed(self._on_app_status_changed)
            self.app.on_error(self._on_app_error)
            
            # Setup file monitoring from settings
            self._setup_file_monitoring()
            
            logger.info("Service application initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    def _setup_file_monitoring(self) -> None:
        """Setup file monitoring from settings"""
        logger.info("Setting up file monitoring...")
        
        for folder_config in self.settings.monitor_folders:
            if not isinstance(folder_config, dict):
                # It's already a MonitorFolder object
                folder_config = {
                    'path': str(folder_config.path),
                    'converter_type': folder_config.converter_type,
                    'recursive': folder_config.recursive,
                    'enabled': folder_config.enabled,
                    'auto_upload': folder_config.auto_upload,
                    'delete_after_convert': folder_config.delete_after_convert,
                }
            
            rule = MonitorRule(
                path=folder_config['path'],
                converter_type=folder_config.get('converter_type', ''),
                recursive=folder_config.get('recursive', False),
                delete_after_convert=folder_config.get('delete_after_convert', False),
                auto_upload=folder_config.get('auto_upload', True),
                enabled=folder_config.get('enabled', True),
            )
            
            self.file_monitor.add_rule(rule)
            logger.info(f"Added monitoring rule for {rule.path}")
    
    async def start(self) -> None:
        """Start the service"""
        if self._running:
            logger.warning("Service already running")
            return
        
        logger.info("Starting service application...")
        self._running = True
        
        try:
            # Initialize if not done
            if self.app is None:
                await self.initialize()
            
            # Start base application
            await self.app.start()
            
            # Start file monitoring
            await self.file_monitor.start()
            self.file_monitor.on_file_event(self._on_file_event)
            
            # Start sync task
            asyncio.create_task(self._sync_loop())
            
            logger.info("Service application started")
        
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop the service gracefully"""
        if not self._running:
            return
        
        logger.info("Stopping service application...")
        self._running = False
        
        try:
            # Stop file monitoring
            await self.file_monitor.stop()
            
            # Stop base application
            if self.app:
                await self.app.stop()
            
            logger.info("Service application stopped")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise
    
    def run(self) -> None:
        """Run the service (blocking)"""
        logger.info("Running service application...")
        
        try:
            asyncio.run(self._run_loop())
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            logger.info("Service application shutdown complete")
    
    async def _run_loop(self) -> None:
        """Main event loop"""
        await self.start()
        
        try:
            while self._running:
                await asyncio.sleep(1)
        finally:
            await self.stop()
    
    async def _sync_loop(self) -> None:
        """Background sync task"""
        while self._running:
            try:
                await asyncio.sleep(self.settings.auto_upload_interval)
                
                if not self._running:
                    break
                
                # Check connection status
                if self.app and self.app.is_online():
                    await self._sync_with_server()
            
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
    
    async def _sync_with_server(self) -> None:
        """Sync data with server when online"""
        logger.debug("Syncing with server...")
        
        try:
            # 1. Sync used serials if available
            used_serials = self.serial_mgr.get_used_serials()
            if used_serials:
                logger.info(f"Syncing {len(used_serials)} used serials...")
                # TODO: Send to server API
                # await self.app.wats_client.serials.mark_used(used_serials)
                # self.serial_mgr.clear_used_serials()
            
            # 2. Replenish serial pool if depleted
            if self.serial_mgr.is_depleted(threshold=5):
                logger.info("Replenishing serial number pool...")
                # TODO: Request serials from server
                # new_serials = await self.app.wats_client.serials.reserve(
                #     count=self.settings.reserve_count
                # )
                # self.serial_mgr.add_reserved([s.number for s in new_serials])
        
        except Exception as e:
            logger.error(f"Failed to sync with server: {e}")
    
    async def _on_file_event(self, event: dict) -> None:
        """Handle file events from monitor"""
        if event['type'] != FileEventType.CREATED:
            return
        
        file_path = event['path']
        converter_type = event['converter_type']
        
        logger.info(f"Processing file: {file_path.name} (converter: {converter_type})")
        
        try:
            if not self.app or not self.app.converter_manager:
                logger.warning("Converter manager not available")
                return
            
            # Convert file
            result = await self.app.converter_manager.convert(
                str(file_path),
                converter_type=converter_type
            )
            
            if result.success:
                logger.info(f"Successfully converted {file_path.name}")
                
                # Queue report for upload
                if event.get('auto_upload', True):
                    self.app.report_queue.queue.append(result.report)
                    logger.info(f"Queued report for upload")
                
                # Delete file if configured
                if event.get('delete_after_convert', False):
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted source file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete file: {e}")
            
            else:
                logger.error(f"Conversion failed: {result.error}")
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
    
    def _on_app_status_changed(self, status: ApplicationStatus) -> None:
        """Handle application status changes"""
        logger.info(f"Application status: {status.value}")
        
        if status == ApplicationStatus.RUNNING:
            logger.info("Service is online and ready")
        elif status == ApplicationStatus.ERROR:
            logger.error("Service encountered an error")
    
    def _on_app_error(self, error: ApplicationError) -> None:
        """Handle application errors"""
        logger.error(f"Application error: {error}")
    
    # =========================================================================
    # Management Methods
    # =========================================================================
    
    def add_monitor_folder(self, path: str, converter_type: str = "") -> bool:
        """
        Add a folder to monitor.
        
        Args:
            path: Folder path
            converter_type: Type of converter to use
            
        Returns:
            True if successful
        """
        logger.info(f"Adding monitor folder: {path}")
        
        folder = MonitorFolder(
            path=path,
            converter_type=converter_type,
            auto_upload=True,
        )
        
        if self.settings_mgr.add_monitor_folder(folder):
            # Reload settings
            self.settings = self.settings_mgr.load()
            return True
        
        return False
    
    def remove_monitor_folder(self, path: str) -> bool:
        """Remove a monitored folder"""
        logger.info(f"Removing monitor folder: {path}")
        
        if self.settings_mgr.remove_monitor_folder(path):
            # Reload settings
            self.settings = self.settings_mgr.load()
            return True
        
        return False
    
    def get_status(self) -> dict:
        """Get complete service status"""
        return {
            "running": self._running,
            "application": {
                "status": self.app.status.value if self.app else "Uninitialized",
                "online": self.app.is_online() if self.app else False,
                "queue": self.app.get_queue_status() if self.app else {},
            },
            "file_monitor": self.file_monitor.get_status(),
            "serials": self.serial_mgr.get_statistics(),
            "recommendations": self.serial_mgr.get_recommendations(),
        }
    
    def get_queue_status(self) -> dict:
        """Get offline queue status"""
        if not self.app:
            return {}
        return self.app.get_queue_status()
    
    def get_connection_status(self) -> Optional[str]:
        """Get connection status"""
        if not self.app:
            return None
        return self.app.get_connection_status()


# ============================================================================
# Entry Points
# ============================================================================

async def main_async():
    """Main async entry point"""
    service = ServiceApplication(config_dir=Path("./pywats_service"))
    await service.start()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await service.stop()


def main():
    """Main entry point"""
    service = ServiceApplication(config_dir=Path("./pywats_service"))
    service.run()


if __name__ == "__main__":
    main()
