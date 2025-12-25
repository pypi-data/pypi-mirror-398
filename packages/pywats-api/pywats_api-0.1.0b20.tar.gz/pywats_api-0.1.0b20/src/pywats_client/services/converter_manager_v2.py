"""
Converter Manager V2

Updated manager that works with the new converter architecture:
- FileConverter: File-triggered conversions
- FolderConverter: Folder-ready conversions  
- ScheduledConverter: Timer/cron-based conversions

Features:
- Dynamic converter loading from Python modules
- File system watching with watchdog
- Folder readiness monitoring
- Scheduled task execution
- Integration with ConverterProcessorV2
"""

import asyncio
import logging
import importlib.util
import inspect
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Type, Callable, TYPE_CHECKING
from datetime import datetime, timedelta

# Watchdog types for type checking only
if TYPE_CHECKING:
    from watchdog.observers import Observer as ObserverType
    from watchdog.events import FileSystemEventHandler as FSEventHandler

# Runtime watchdog import
HAS_WATCHDOG = False
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, DirCreatedEvent
    HAS_WATCHDOG = True
except ImportError:
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore

from ..converters.models import ConverterSource, ConverterResult, ConversionStatus
from ..converters.context import ConverterContext
from ..converters.file_converter import FileConverter
from ..converters.folder_converter import FolderConverter
from ..converters.scheduled_converter import ScheduledConverter
from .converter_processor_v2 import ConverterProcessorV2

if TYPE_CHECKING:
    from ..core.config import ConverterConfig
    from .report_queue import ReportQueueService

logger = logging.getLogger(__name__)

# Type alias for any converter type
AnyConverter = Union[FileConverter, FolderConverter, ScheduledConverter]


class FileEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler for file-based converters.
    
    Triggers conversion when files are created in the watch folder.
    """
    
    def __init__(
        self,
        converter: FileConverter,
        config: 'ConverterConfig',
        processor: ConverterProcessorV2,
        loop: asyncio.AbstractEventLoop
    ):
        self.converter = converter
        self.config = config
        self.processor = processor
        self.loop = loop
        self._processing: set = set()
        self._debounce_delay = 0.5  # seconds
    
    def on_created(self, event: Any) -> None:
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
        
        # Schedule async processing
        asyncio.run_coroutine_threadsafe(
            self._process_file(file_path),
            self.loop
        )
    
    def _matches_patterns(self, file_path: Path) -> bool:
        """Check if file matches configured patterns"""
        for pattern in self.config.file_patterns:
            if file_path.match(pattern):
                return True
        return False
    
    async def _process_file(self, file_path: Path) -> None:
        """Process a file through the converter"""
        try:
            # Wait for file to be fully written
            await asyncio.sleep(self._debounce_delay)
            
            # Check file still exists (might have been moved)
            if not file_path.exists():
                return
            
            # Process through processor
            await self.processor.process_file(
                file_path=file_path,
                converter_name=self.config.name,
                extra_arguments=self.config.arguments
            )
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
        finally:
            self._processing.discard(str(file_path))


class FolderEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler for folder-based converters.
    
    Monitors for folder readiness based on marker files or other criteria.
    """
    
    def __init__(
        self,
        converter: FolderConverter,
        config: 'ConverterConfig',
        processor: ConverterProcessorV2,
        context: ConverterContext,
        loop: asyncio.AbstractEventLoop
    ):
        self.converter = converter
        self.config = config
        self.processor = processor
        self.context = context
        self.loop = loop
        self._processing: set = set()
        self._known_folders: set = set()
    
    def on_created(self, event: Any) -> None:
        """Handle file/folder creation events"""
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode('utf-8')
        path = Path(str(src_path))
        
        # If a directory was created, track it
        if event.is_directory:
            self._known_folders.add(str(path))
            return
        
        # If a file was created, check if its parent folder is ready
        folder = path.parent
        
        # Check if this is in a tracked folder
        if str(folder) not in self._known_folders:
            # Maybe it's a new folder we haven't seen yet
            if folder != Path(self.config.watch_folder):
                self._known_folders.add(str(folder))
        
        # Check if folder is now ready
        asyncio.run_coroutine_threadsafe(
            self._check_folder_ready(folder),
            self.loop
        )
    
    async def _check_folder_ready(self, folder_path: Path) -> None:
        """Check if folder is ready and process if so"""
        if str(folder_path) in self._processing:
            return
        
        # Check if folder matches patterns
        if not self._matches_patterns(folder_path):
            return
        
        # Check if converter considers folder ready
        if not self.converter.is_folder_ready(folder_path, self.context):
            return
        
        self._processing.add(str(folder_path))
        
        try:
            await self.processor.process_folder(
                folder_path=folder_path,
                converter_name=self.config.name,
                extra_arguments=self.config.arguments
            )
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {e}")
        finally:
            self._processing.discard(str(folder_path))
            self._known_folders.discard(str(folder_path))
    
    def _matches_patterns(self, folder_path: Path) -> bool:
        """Check if folder matches configured patterns"""
        for pattern in self.config.folder_patterns:
            if folder_path.match(pattern) or pattern == "*":
                return True
        return False


class ScheduledConverterRunner:
    """
    Runs scheduled converters on their configured intervals.
    """
    
    def __init__(
        self,
        converter: ScheduledConverter,
        config: 'ConverterConfig',
        context: ConverterContext,
        report_callback: Optional[Callable] = None
    ):
        self.converter = converter
        self.config = config
        self.context = context
        self.report_callback = report_callback
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the scheduled runner"""
        if self._running:
            return
        
        self._running = True
        
        # Run on startup if configured
        if self.converter.run_on_startup:
            await self._run_once()
        
        # Start the loop
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self) -> None:
        """Stop the scheduled runner"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _run_loop(self) -> None:
        """Main scheduling loop"""
        while self._running:
            try:
                # Calculate next run time
                interval = self.converter.schedule_interval
                
                if interval:
                    # Simple interval-based scheduling
                    await asyncio.sleep(interval.total_seconds())
                else:
                    # Cron-based scheduling
                    next_run = self.converter.calculate_next_run()
                    if next_run:
                        wait_seconds = (next_run - datetime.now()).total_seconds()
                        if wait_seconds > 0:
                            await asyncio.sleep(wait_seconds)
                    else:
                        # No valid schedule, wait a minute and check again
                        await asyncio.sleep(60)
                        continue
                
                if self._running:
                    await self._run_once()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduled converter loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _run_once(self) -> None:
        """Run the converter once"""
        logger.info(f"Running scheduled converter: {self.converter.name}")
        
        try:
            # Update state
            self.converter._is_running = True
            self.converter._last_run = datetime.now()
            
            # Call lifecycle hook
            self.converter.on_run_start(self.context)
            
            # Run the converter
            results = await self.converter.run(self.context)
            
            # Call lifecycle hook
            self.converter.on_run_complete(results, self.context)
            
            # Process results
            for result in results:
                if result.status == ConversionStatus.SUCCESS and result.report:
                    if self.report_callback:
                        await self.report_callback(result.report)
                    logger.info(f"Scheduled conversion successful")
                elif result.status == ConversionStatus.FAILED:
                    logger.error(f"Scheduled conversion failed: {result.error}")
            
            logger.info(
                f"Scheduled converter completed: {len(results)} results, "
                f"{sum(1 for r in results if r.status == ConversionStatus.SUCCESS)} successful"
            )
            
        except Exception as e:
            logger.error(f"Error running scheduled converter: {e}", exc_info=True)
            self.converter.on_run_error(e, self.context)
        
        finally:
            self.converter._is_running = False
            self.converter._next_run = self.converter.calculate_next_run()


class ConverterManagerV2:
    """
    Manages multiple converters of all types.
    
    Features:
    - Load converters from Python modules
    - Watch folders for incoming files (FileConverter)
    - Monitor folder readiness (FolderConverter)
    - Run scheduled converters (ScheduledConverter)
    - Submit results to report queue
    - Statistics and monitoring
    """
    
    def __init__(
        self,
        converter_configs: List['ConverterConfig'],
        api_client: Any = None,
        report_queue: Optional['ReportQueueService'] = None,
        base_context: Optional[ConverterContext] = None
    ):
        self.converter_configs = converter_configs
        self.api_client = api_client
        self.report_queue = report_queue
        self.base_context = base_context or ConverterContext()
        
        # Loaded converters
        self._converters: Dict[str, AnyConverter] = {}
        self._processors: Dict[str, ConverterProcessorV2] = {}
        
        # File system observers (for file/folder converters)
        self._observers: List[Any] = []
        
        # Scheduled runners
        self._scheduled_runners: List[ScheduledConverterRunner] = []
        
        # State
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def start(self) -> None:
        """Start all converters and watchers"""
        if self._running:
            return
        
        if not HAS_WATCHDOG:
            logger.warning(
                "watchdog package not installed. "
                "File/folder converters will not work. "
                "Install with: pip install watchdog"
            )
        
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        logger.info("Starting converter manager V2")
        
        for config in self.converter_configs:
            if not config.enabled:
                logger.debug(f"Converter '{config.name}' is disabled, skipping")
                continue
            
            try:
                # Load converter
                converter = self._load_converter(config)
                if not converter:
                    continue
                
                self._converters[config.name] = converter
                
                # Create context for this converter
                context = self._create_context(config)
                
                # Setup based on converter type
                if isinstance(converter, ScheduledConverter):
                    await self._setup_scheduled_converter(converter, config, context)
                elif isinstance(converter, FolderConverter):
                    self._setup_folder_watcher(converter, config, context)
                elif isinstance(converter, FileConverter):
                    self._setup_file_watcher(converter, config, context)
                
                # Call on_load lifecycle hook
                converter.on_load(context)
                
                logger.info(
                    f"Converter '{config.name}' ({config.converter_type}) started"
                )
                
            except Exception as e:
                logger.error(f"Failed to start converter '{config.name}': {e}", exc_info=True)
    
    async def stop(self) -> None:
        """Stop all converters and watchers"""
        self._running = False
        
        # Stop scheduled runners
        for runner in self._scheduled_runners:
            await runner.stop()
        self._scheduled_runners.clear()
        
        # Stop file system observers
        for observer in self._observers:
            observer.stop()
            observer.join(timeout=5)
        self._observers.clear()
        
        # Call on_unload for all converters
        for converter in self._converters.values():
            try:
                converter.on_unload()
            except Exception as e:
                logger.error(f"Error in converter on_unload: {e}")
        
        self._converters.clear()
        self._processors.clear()
        
        logger.info("Converter manager V2 stopped")
    
    def _load_converter(self, config: 'ConverterConfig') -> Optional[AnyConverter]:
        """
        Load a converter from a Python module.
        
        The module should define a class that inherits from
        FileConverter, FolderConverter, or ScheduledConverter.
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
            
            # Find the appropriate converter class based on config type
            target_base: Type[AnyConverter]
            if config.converter_type == "scheduled":
                target_base = ScheduledConverter
            elif config.converter_type == "folder":
                target_base = FolderConverter
            else:
                target_base = FileConverter
            
            converter_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, target_base) and 
                    obj is not target_base and
                    obj is not FileConverter and
                    obj is not FolderConverter and
                    obj is not ScheduledConverter):
                    converter_class = obj
                    break
            
            if not converter_class:
                logger.error(
                    f"No {target_base.__name__} subclass found in {module_path}"
                )
                return None
            
            # Instantiate the converter - cast to proper type
            instance = converter_class()
            if isinstance(instance, (FileConverter, FolderConverter, ScheduledConverter)):
                return instance
            return None
            
        except Exception as e:
            logger.error(f"Failed to load converter from {config.module_path}: {e}")
            return None
    
    def _create_context(self, config: 'ConverterConfig') -> ConverterContext:
        """Create a context for a converter config"""
        return ConverterContext(
            api_client=self.api_client,
            drop_folder=Path(config.watch_folder) if config.watch_folder else None,
            done_folder=Path(config.done_folder) if config.done_folder else None,
            error_folder=Path(config.error_folder) if config.error_folder else None,
            pending_folder=Path(config.pending_folder) if config.pending_folder else None,
            station_name=self.base_context.station_name,
            alarm_threshold=config.alarm_threshold,
            reject_threshold=config.reject_threshold,
            max_retries=config.max_retries,
            retry_delay_seconds=config.retry_delay_seconds,
            arguments=config.arguments,
        )
    
    def _setup_file_watcher(
        self,
        converter: FileConverter,
        config: 'ConverterConfig',
        context: ConverterContext
    ) -> None:
        """Setup file system watcher for a file converter"""
        if not HAS_WATCHDOG:
            return
        
        if self._loop is None:
            logger.error("Event loop not available, cannot start file watcher")
            return
        
        watch_path = Path(config.watch_folder)
        if not watch_path.exists():
            watch_path.mkdir(parents=True, exist_ok=True)
        
        # Create processor for this converter
        processor = ConverterProcessorV2(
            api_client=self.api_client,
            converters={config.name: converter},
            context=context,
            max_retry_attempts=config.max_retries,
            retry_delay_seconds=config.retry_delay_seconds,
        )
        self._processors[config.name] = processor
        
        # Create and start observer
        handler = FileEventHandler(
            converter=converter,
            config=config,
            processor=processor,
            loop=self._loop
        )
        
        observer = Observer()
        observer.schedule(handler, str(watch_path), recursive=False)
        observer.start()
        
        self._observers.append(observer)
        
        logger.info(f"File watcher started for '{config.name}' on {watch_path}")
    
    def _setup_folder_watcher(
        self,
        converter: FolderConverter,
        config: 'ConverterConfig',
        context: ConverterContext
    ) -> None:
        """Setup file system watcher for a folder converter"""
        if not HAS_WATCHDOG:
            return
        
        if self._loop is None:
            logger.error("Event loop not available, cannot start folder watcher")
            return
        
        watch_path = Path(config.watch_folder)
        if not watch_path.exists():
            watch_path.mkdir(parents=True, exist_ok=True)
        
        # Create processor for this converter
        processor = ConverterProcessorV2(
            api_client=self.api_client,
            converters={config.name: converter},
            context=context,
            max_retry_attempts=config.max_retries,
            retry_delay_seconds=config.retry_delay_seconds,
        )
        self._processors[config.name] = processor
        
        # Create and start observer
        handler = FolderEventHandler(
            converter=converter,
            config=config,
            processor=processor,
            context=context,
            loop=self._loop
        )
        
        observer = Observer()
        observer.schedule(handler, str(watch_path), recursive=True)
        observer.start()
        
        self._observers.append(observer)
        
        logger.info(f"Folder watcher started for '{config.name}' on {watch_path}")
    
    async def _setup_scheduled_converter(
        self,
        converter: ScheduledConverter,
        config: 'ConverterConfig',
        context: ConverterContext
    ) -> None:
        """Setup and start a scheduled converter"""
        # Set schedule from config if not set on converter
        if config.schedule_interval_seconds and not converter.schedule_interval:
            # Override would require a different approach since it's a property
            pass
        
        runner = ScheduledConverterRunner(
            converter=converter,
            config=config,
            context=context,
            report_callback=self._submit_report
        )
        
        await runner.start()
        self._scheduled_runners.append(runner)
        
        logger.info(
            f"Scheduled converter started: '{config.name}' "
            f"({converter.get_schedule_description()})"
        )
    
    async def _submit_report(self, report: Dict[str, Any]) -> None:
        """Submit a report to the report queue"""
        if self.report_queue:
            await self.report_queue.submit(report)
        else:
            logger.info(f"Report ready (no queue configured): {report.get('type', 'unknown')}")
    
    # =========================================================================
    # Manual Processing
    # =========================================================================
    
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
            return ConverterResult.failed_result(
                error=f"Converter '{converter_name}' not found"
            )
        
        converter = self._converters[converter_name]
        
        if not isinstance(converter, FileConverter):
            return ConverterResult.failed_result(
                error=f"Converter '{converter_name}' is not a FileConverter"
            )
        
        processor = self._processors.get(converter_name)
        if not processor:
            # Create a temporary processor
            config = next(
                (c for c in self.converter_configs if c.name == converter_name),
                None
            )
            if not config:
                return ConverterResult.failed_result(
                    error=f"Config for converter '{converter_name}' not found"
                )
            
            context = self._create_context(config)
            processor = ConverterProcessorV2(
                api_client=self.api_client,
                converters={converter_name: converter},
                context=context,
            )
        
        return await processor.process_file(file_path, converter_name)
    
    async def process_folder_manually(
        self,
        converter_name: str,
        folder_path: Path
    ) -> ConverterResult:
        """
        Manually process a folder through a specific converter.
        """
        if converter_name not in self._converters:
            return ConverterResult.failed_result(
                error=f"Converter '{converter_name}' not found"
            )
        
        converter = self._converters[converter_name]
        
        if not isinstance(converter, FolderConverter):
            return ConverterResult.failed_result(
                error=f"Converter '{converter_name}' is not a FolderConverter"
            )
        
        processor = self._processors.get(converter_name)
        if not processor:
            config = next(
                (c for c in self.converter_configs if c.name == converter_name),
                None
            )
            if not config:
                return ConverterResult.failed_result(
                    error=f"Config for converter '{converter_name}' not found"
                )
            
            context = self._create_context(config)
            processor = ConverterProcessorV2(
                api_client=self.api_client,
                converters={converter_name: converter},
                context=context,
            )
        
        return await processor.process_folder(folder_path, converter_name)
    
    async def run_scheduled_converter_now(self, converter_name: str) -> List[ConverterResult]:
        """
        Manually run a scheduled converter immediately.
        """
        if converter_name not in self._converters:
            return [ConverterResult.failed_result(
                error=f"Converter '{converter_name}' not found"
            )]
        
        converter = self._converters[converter_name]
        
        if not isinstance(converter, ScheduledConverter):
            return [ConverterResult.failed_result(
                error=f"Converter '{converter_name}' is not a ScheduledConverter"
            )]
        
        config = next(
            (c for c in self.converter_configs if c.name == converter_name),
            None
        )
        if not config:
            return [ConverterResult.failed_result(
                error=f"Config for converter '{converter_name}' not found"
            )]
        
        context = self._create_context(config)
        
        try:
            return await converter.run(context)
        except Exception as e:
            return [ConverterResult.failed_result(error=str(e))]
    
    # =========================================================================
    # Status and Monitoring
    # =========================================================================
    
    def get_status(self) -> List[Dict[str, Any]]:
        """Get status of all converters"""
        status = []
        
        for config in self.converter_configs:
            converter = self._converters.get(config.name)
            processor = self._processors.get(config.name)
            
            converter_status = {
                'name': config.name,
                'type': config.converter_type,
                'enabled': config.enabled,
                'loaded': config.name in self._converters,
                'watch_folder': config.watch_folder,
                'file_patterns': config.file_patterns,
                'folder_patterns': config.folder_patterns,
            }
            
            if converter:
                converter_status['version'] = converter.version
                converter_status['description'] = converter.description
                
                if isinstance(converter, ScheduledConverter):
                    converter_status['schedule'] = converter.get_schedule_description()
                    converter_status['last_run'] = (
                        converter.last_run.isoformat() 
                        if converter.last_run else None
                    )
                    converter_status['next_run'] = (
                        converter.next_run.isoformat() 
                        if converter.next_run else None
                    )
                    converter_status['is_running'] = converter.is_running
            
            if processor:
                converter_status['statistics'] = processor.get_statistics()
            
            status.append(converter_status)
        
        return status
    
    def get_converter_arguments(self, converter_name: str) -> Dict[str, Any]:
        """Get the arguments schema for a converter"""
        converter = self._converters.get(converter_name)
        if not converter:
            return {}
        
        schema = converter.arguments_schema
        return {
            name: {
                'type': defn.arg_type.value,
                'default': defn.default,
                'required': defn.required,
                'description': defn.description,
                'choices': defn.choices,
            }
            for name, defn in schema.items()
        }
    
    async def reload_converters(self) -> None:
        """Reload all converters (stop and restart)"""
        logger.info("Reloading converters...")
        await self.stop()
        await self.start()
