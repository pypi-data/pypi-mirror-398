"""
Converter Manager Service

Manages file-to-report converters that watch folders for incoming files.
"""

import asyncio
import logging
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

if TYPE_CHECKING:
    from ..core.config import ConverterConfig
    from .report_queue import ReportQueueService

from ..converters.base import ConverterBase, ConverterResult

logger = logging.getLogger(__name__)


class ConverterFileHandler(FileSystemEventHandler):
    """
    Watchdog event handler for converter watch folders.
    """
    
    def __init__(
        self,
        converter: ConverterBase,
        config: 'ConverterConfig',
        callback
    ):
        self.converter = converter
        self.config = config
        self.callback = callback
        self._processing = set()
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode('utf-8')
        file_path = Path(str(src_path))
        
        # Check if file matches patterns
        if not self._matches_patterns(file_path):
            return
        
        # Avoid duplicate processing
        if str(file_path) in self._processing:
            return
        
        self._processing.add(str(file_path))
        
        # Call the async callback
        asyncio.create_task(self._process_file(file_path))
    
    def _matches_patterns(self, file_path: Path) -> bool:
        """Check if file matches configured patterns"""
        for pattern in self.config.file_patterns:
            if file_path.match(pattern):
                return True
        return False
    
    async def _process_file(self, file_path: Path):
        """Process a file through the converter"""
        try:
            # Wait a moment for file to be fully written
            await asyncio.sleep(0.5)
            
            await self.callback(self.converter, self.config, file_path)
        finally:
            self._processing.discard(str(file_path))


class ConverterManager:
    """
    Manages multiple file converters.
    
    Features:
    - Load converters from Python modules
    - Watch folders for incoming files
    - Process files through converters
    - Submit results to report queue
    """
    
    def __init__(
        self,
        converters: List['ConverterConfig'],
        report_queue: Optional['ReportQueueService'] = None
    ):
        self.converter_configs = converters
        self.report_queue = report_queue
        
        self._converters: Dict[str, ConverterBase] = {}
        self._observers: list = []
        self._running = False
    
    async def start(self) -> None:
        """Start all converters and file watchers"""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting converter manager")
        
        for config in self.converter_configs:
            if not config.enabled:
                continue
            
            try:
                # Load converter
                converter = self._load_converter(config)
                if not converter:
                    continue
                
                self._converters[config.name] = converter
                
                # Setup file watcher
                self._setup_watcher(converter, config)
                
                logger.info(f"Converter '{config.name}' started, watching: {config.watch_folder}")
                
            except Exception as e:
                logger.error(f"Failed to start converter '{config.name}': {e}")
    
    async def stop(self) -> None:
        """Stop all converters and file watchers"""
        self._running = False
        
        # Stop all observers
        for observer in self._observers:
            observer.stop()
            observer.join(timeout=5)
        
        self._observers.clear()
        self._converters.clear()
        
        logger.info("Converter manager stopped")
    
    def _load_converter(self, config: 'ConverterConfig') -> Optional[ConverterBase]:
        """
        Load a converter from a Python module.
        
        The module should define a class that inherits from ConverterBase.
        """
        try:
            module_path = Path(config.module_path)
            
            if not module_path.exists():
                logger.error(f"Converter module not found: {module_path}")
                return None
            
            # Load the module
            spec = importlib.util.spec_from_file_location(
                f"converter_{config.name}",
                module_path
            )
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load spec for converter: {module_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the converter class
            converter_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, ConverterBase) and 
                    obj is not ConverterBase):
                    converter_class = obj
                    break
            
            if not converter_class:
                logger.error(f"No ConverterBase subclass found in {module_path}")
                return None
            
            # Instantiate with arguments
            return converter_class(**config.arguments)
            
        except Exception as e:
            logger.error(f"Failed to load converter from {config.module_path}: {e}")
            return None
    
    def _setup_watcher(self, converter: ConverterBase, config: 'ConverterConfig') -> None:
        """Setup file system watcher for a converter"""
        watch_path = Path(config.watch_folder)
        
        if not watch_path.exists():
            watch_path.mkdir(parents=True, exist_ok=True)
        
        handler = ConverterFileHandler(
            converter=converter,
            config=config,
            callback=self._process_file
        )
        
        observer = Observer()
        observer.schedule(handler, str(watch_path), recursive=False)
        observer.start()
        
        self._observers.append(observer)
    
    async def _process_file(
        self,
        converter: ConverterBase,
        config: 'ConverterConfig',
        file_path: Path
    ) -> None:
        """Process a file through a converter"""
        logger.info(f"Processing file: {file_path} with converter: {config.name}")
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                result = converter.convert(f, file_path.name)
            
            if result.success and result.report:
                logger.info(f"Conversion successful for {file_path}")
                
                # Submit to report queue
                if self.report_queue:
                    await self.report_queue.submit(result.report)
                
                # Handle the source file based on converter settings
                if converter.delete_on_success:
                    file_path.unlink()
                elif converter.processed_folder:
                    dest = Path(converter.processed_folder) / file_path.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    file_path.rename(dest)
            else:
                logger.error(f"Conversion failed for {file_path}: {result.error}")
                
                # Move to error folder if configured
                if converter.error_folder:
                    dest = Path(converter.error_folder) / file_path.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    file_path.rename(dest)
                    
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def get_status(self) -> List[Dict[str, Any]]:
        """Get status of all converters"""
        status = []
        
        for config in self.converter_configs:
            converter_status = {
                'name': config.name,
                'enabled': config.enabled,
                'watch_folder': config.watch_folder,
                'loaded': config.name in self._converters,
                'file_patterns': config.file_patterns,
            }
            status.append(converter_status)
        
        return status
    
    async def process_file_manually(
        self,
        converter_name: str,
        file_path: Path
    ) -> ConverterResult:
        """
        Manually process a file through a specific converter.
        
        Useful for testing or reprocessing files.
        """
        if converter_name not in self._converters:
            return ConverterResult(
                success=False,
                error=f"Converter '{converter_name}' not found"
            )
        
        converter = self._converters[converter_name]
        config = next(
            (c for c in self.converter_configs if c.name == converter_name),
            None
        )
        
        if not config:
            return ConverterResult(
                success=False,
                error=f"Config for converter '{converter_name}' not found"
            )
        
        try:
            with open(file_path, 'rb') as f:
                return converter.convert(f, file_path.name)
        except Exception as e:
            return ConverterResult(success=False, error=str(e))
    
    async def reload_converters(self) -> None:
        """Reload all converters (stop and restart)"""
        logger.info("Reloading converters...")
        await self.stop()
        await self.start()
