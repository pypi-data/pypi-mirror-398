"""
File Monitor for pyWATS Client

Monitors specified folders for new files and triggers conversion/upload.
Supports multiple monitoring rules with different converters and auto-upload settings.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class FileEventType(Enum):
    """Type of file system event"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class MonitorRule:
    """Configuration for monitoring a folder"""
    
    def __init__(
        self,
        path: str,
        converter_type: str = "",
        recursive: bool = False,
        delete_after_convert: bool = False,
        auto_upload: bool = True,
        enabled: bool = True,
        file_pattern: str = "*"
    ):
        """
        Initialize monitor rule.
        
        Args:
            path: Folder path to monitor
            converter_type: Type of converter to use for files
            recursive: Whether to monitor subdirectories
            delete_after_convert: Delete file after successful conversion
            auto_upload: Automatically upload converted reports
            enabled: Whether monitoring is enabled
            file_pattern: File pattern to match (e.g., "*.csv")
        """
        self.path = Path(path)
        self.converter_type = converter_type
        self.recursive = recursive
        self.delete_after_convert = delete_after_convert
        self.auto_upload = auto_upload
        self.enabled = enabled
        self.file_pattern = file_pattern
        self._last_modified: Dict[str, float] = {}
    
    def matches(self, file_path: Path) -> bool:
        """Check if file matches this rule"""
        if not self.enabled:
            return False
        
        # Check pattern
        if not file_path.match(self.file_pattern):
            return False
        
        # Check path
        try:
            file_path.relative_to(self.path)
            return True
        except ValueError:
            return False
    
    def should_process(self, file_path: Path, debounce_ms: int = 500) -> bool:
        """
        Check if file should be processed (debounce).
        
        Args:
            file_path: Path to file
            debounce_ms: Debounce time in milliseconds
            
        Returns:
            True if file should be processed
        """
        current_time = time.time()
        last_modified = self._last_modified.get(str(file_path), 0)
        
        # Check debounce
        if (current_time - last_modified) * 1000 < debounce_ms:
            return False
        
        self._last_modified[str(file_path)] = current_time
        return True


class FileMonitor:
    """
    Monitors specified folders for file events.
    
    Features:
    - Multiple monitoring rules per folder
    - Recursive directory monitoring
    - Debouncing to avoid processing partial writes
    - Callback notifications
    - Async operation
    
    Usage:
        monitor = FileMonitor()
        
        # Add monitoring rule
        rule = MonitorRule(
            path="./uploads",
            converter_type="csv",
            auto_upload=True,
            delete_after_convert=True
        )
        monitor.add_rule(rule)
        
        # Handle file events
        monitor.on_file_event(lambda event: handle_file(event))
        
        # Start monitoring
        await monitor.start()
    """
    
    def __init__(self, check_interval: int = 2):
        """
        Initialize file monitor.
        
        Args:
            check_interval: How often to check folders (seconds)
        """
        self.check_interval = check_interval
        self._rules: List[MonitorRule] = []
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._running = False
        self._monitored_files: Dict[str, float] = {}
        self._task: Optional[asyncio.Task] = None
    
    def add_rule(self, rule: MonitorRule) -> None:
        """
        Add a monitoring rule.
        
        Args:
            rule: MonitorRule instance
        """
        self._rules.append(rule)
        logger.info(
            f"Added monitor rule: {rule.path} "
            f"(converter: {rule.converter_type}, recursive: {rule.recursive})"
        )
    
    def remove_rule(self, path: str) -> bool:
        """
        Remove a monitoring rule.
        
        Args:
            path: Path of rule to remove
            
        Returns:
            True if rule was found and removed
        """
        for i, rule in enumerate(self._rules):
            if str(rule.path) == path:
                self._rules.pop(i)
                logger.info(f"Removed monitor rule: {path}")
                return True
        
        return False
    
    def on_file_event(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for file events.
        
        Args:
            callback: Function to call with event data:
                {
                    "type": FileEventType,
                    "path": Path,
                    "rule": MonitorRule,
                    "timestamp": datetime
                }
        """
        self._callbacks.append(callback)
    
    async def start(self) -> None:
        """Start monitoring"""
        if self._running:
            logger.warning("Monitor already running")
            return
        
        if not self._rules:
            logger.warning("No monitoring rules configured")
            return
        
        self._running = True
        logger.info("Starting file monitor")
        
        # Start monitoring task
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self) -> None:
        """Stop monitoring"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("File monitor stopped")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        logger.info(
            f"Monitor loop started (checking every {self.check_interval}s)"
        )
        
        while self._running:
            try:
                for rule in self._rules:
                    if rule.enabled:
                        await self._check_folder(rule)
                
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_folder(self, rule: MonitorRule) -> None:
        """
        Check a folder for new or modified files.
        
        Args:
            rule: MonitorRule to check
        """
        try:
            if not rule.path.exists():
                logger.debug(f"Monitor path does not exist: {rule.path}")
                return
            
            # Get files to check
            pattern = "**/*" if rule.recursive else "*"
            files = list(rule.path.glob(pattern))
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Check if file matches rule
                if not rule.matches(file_path):
                    continue
                
                # Get file modification time
                try:
                    file_mtime = file_path.stat().st_mtime
                except (OSError, FileNotFoundError):
                    continue
                
                # Track files
                file_key = str(file_path)
                last_mtime = self._monitored_files.get(file_key)
                
                if last_mtime is None or file_mtime != last_mtime:
                    # File is new or modified
                    self._monitored_files[file_key] = file_mtime
                    
                    # Check debounce
                    if rule.should_process(file_path):
                        await self._emit_event(
                            FileEventType.CREATED if last_mtime is None else FileEventType.MODIFIED,
                            file_path,
                            rule
                        )
            
            # Check for deleted files
            deleted_keys = [
                key for key in self._monitored_files
                if key.startswith(str(rule.path))
                and not Path(key).exists()
            ]
            
            for key in deleted_keys:
                del self._monitored_files[key]
                await self._emit_event(
                    FileEventType.DELETED,
                    Path(key),
                    rule
                )
        
        except Exception as e:
            logger.error(f"Error checking folder {rule.path}: {e}")
    
    async def _emit_event(
        self,
        event_type: FileEventType,
        file_path: Path,
        rule: MonitorRule
    ) -> None:
        """
        Emit a file event to callbacks.
        
        Args:
            event_type: Type of event
            file_path: Path to file
            rule: MonitorRule that triggered this
        """
        event = {
            "type": event_type,
            "path": file_path,
            "rule": rule,
            "timestamp": datetime.now(),
            "converter_type": rule.converter_type,
            "auto_upload": rule.auto_upload,
            "delete_after_convert": rule.delete_after_convert,
        }
        
        logger.debug(
            f"File event: {event_type.value} {file_path.name} "
            f"(converter: {rule.converter_type})"
        )
        
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in file event callback: {e}")
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get list of current monitoring rules"""
        return [
            {
                "path": str(rule.path),
                "converter_type": rule.converter_type,
                "recursive": rule.recursive,
                "enabled": rule.enabled,
                "delete_after_convert": rule.delete_after_convert,
                "auto_upload": rule.auto_upload,
                "file_pattern": rule.file_pattern,
            }
            for rule in self._rules
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status"""
        return {
            "running": self._running,
            "rules_count": len(self._rules),
            "monitored_files_count": len(self._monitored_files),
            "check_interval": self.check_interval,
            "rules": self.get_rules(),
        }
