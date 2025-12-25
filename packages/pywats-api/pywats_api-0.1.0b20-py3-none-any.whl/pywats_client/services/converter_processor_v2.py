"""
Converter Processor V2

Updated processor that works with the new converter architecture:
- FileConverter, FolderConverter, ScheduledConverter base classes
- ValidationResult with confidence scoring
- ConverterResult with status enum
- ConverterContext for passing configuration

This version maintains backward compatibility with the old ConverterBase
while supporting the new architecture.
"""

import asyncio
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum

from ..converters.models import (
    ConverterSource,
    ConverterResult,
    ValidationResult,
    ConversionStatus,
    PostProcessAction,
    ConversionRecord,
)
from ..converters.context import ConverterContext
from ..converters.file_converter import FileConverter
from ..converters.folder_converter import FolderConverter
from ..converters.scheduled_converter import ScheduledConverter

# Type alias for any converter type
AnyConverter = Union[FileConverter, FolderConverter, ScheduledConverter]

logger = logging.getLogger(__name__)


class ProcessorStatistics:
    """Track conversion statistics"""
    
    def __init__(self) -> None:
        self.total_processed = 0
        self.successful = 0
        self.failed = 0
        self.suspended = 0
        self.skipped = 0
        self.last_activity: Optional[datetime] = None
    
    def record(self, status: ConversionStatus) -> None:
        self.total_processed += 1
        self.last_activity = datetime.now()
        
        if status == ConversionStatus.SUCCESS:
            self.successful += 1
        elif status == ConversionStatus.FAILED:
            self.failed += 1
        elif status == ConversionStatus.SUSPENDED:
            self.suspended += 1
        elif status == ConversionStatus.SKIPPED:
            self.skipped += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_processed": self.total_processed,
            "successful": self.successful,
            "failed": self.failed,
            "suspended": self.suspended,
            "skipped": self.skipped,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


class ConverterProcessorV2:
    """
    Processes files/folders through converters with full workflow support.
    
    Features:
    - Support for FileConverter, FolderConverter base classes
    - Validation with confidence scoring and thresholds
    - Conversion with ConverterContext
    - Post-processing actions (Move, Zip, Delete, Keep)
    - Suspended conversion retry logic with pending folder
    - Error folder management with detailed logging
    - Success/failure callbacks
    - Statistics tracking
    
    Usage:
        processor = ConverterProcessorV2(
            api_client=wats_client,
            converters={"csv": csv_converter},
            context=ConverterContext(
                drop_folder=Path("./uploads"),
                done_folder=Path("./uploads/Done"),
                error_folder=Path("./uploads/Error"),
            )
        )
        
        # Process a file
        result = await processor.process_file(
            file_path=Path("./uploads/test.csv"),
            converter_name="csv"
        )
        
        # Handle result
        if result.status == ConversionStatus.SUCCESS:
            print(f"Converted: {result.report}")
    """
    
    def __init__(
        self,
        api_client: Any,
        converters: Dict[str, AnyConverter],
        context: ConverterContext,
        max_retry_attempts: int = 3,
        retry_delay_seconds: int = 60,
    ):
        """
        Initialize converter processor.
        
        Args:
            api_client: pyWATS API client instance
            converters: Dictionary of converter_name -> converter_instance
            context: Base converter context (cloned per conversion)
            max_retry_attempts: Maximum retry attempts for suspended conversions
            retry_delay_seconds: Delay between retry attempts (seconds)
        """
        self.api_client = api_client
        self.converters = converters
        self.base_context = context
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        
        # Ensure folders exist
        context.ensure_folders_exist()
        
        # Conversion tracking
        self._conversion_records: Dict[str, ConversionRecord] = {}
        self._statistics = ProcessorStatistics()
        
        # Callbacks
        self._success_callbacks: List[Callable[[ConverterSource, ConverterResult], None]] = []
        self._failure_callbacks: List[Callable[[ConverterSource, ConverterResult], None]] = []
        self._validation_callbacks: List[Callable[[ConverterSource, ValidationResult], None]] = []
    
    # =========================================================================
    # Callback Registration
    # =========================================================================
    
    def on_success(self, callback: Callable[[ConverterSource, ConverterResult], None]) -> None:
        """Register callback for successful conversions"""
        self._success_callbacks.append(callback)
    
    def on_failure(self, callback: Callable[[ConverterSource, ConverterResult], None]) -> None:
        """Register callback for failed conversions"""
        self._failure_callbacks.append(callback)
    
    def on_validation(self, callback: Callable[[ConverterSource, ValidationResult], None]) -> None:
        """Register callback for validation results (including low confidence)"""
        self._validation_callbacks.append(callback)
    
    # =========================================================================
    # File Processing
    # =========================================================================
    
    async def process_file(
        self,
        file_path: Path,
        converter_name: str,
        extra_arguments: Optional[Dict[str, Any]] = None
    ) -> ConverterResult:
        """
        Process a file through a FileConverter.
        
        Args:
            file_path: Path to file to convert
            converter_name: Name of converter to use
            extra_arguments: Additional arguments to merge with context
        
        Returns:
            ConverterResult with status and data
        """
        if not file_path.exists():
            return ConverterResult.failed_result(
                error=f"File not found: {file_path}"
            )
        
        # Get converter
        converter = self.converters.get(converter_name)
        if not converter:
            return ConverterResult.failed_result(
                error=f"Converter not found: {converter_name}"
            )
        
        if not isinstance(converter, FileConverter):
            return ConverterResult.failed_result(
                error=f"Converter '{converter_name}' is not a FileConverter"
            )
        
        # Create source
        source = ConverterSource.from_file(file_path)
        
        # Create context for this conversion
        context = self._create_context(extra_arguments)
        
        # Get or create conversion record
        record_key = str(file_path)
        record = self._conversion_records.get(record_key)
        if record is None:
            record = ConversionRecord(
                source_path=file_path,
                converter_name=converter_name
            )
            self._conversion_records[record_key] = record
        
        logger.info(
            f"Processing file: {file_path.name} "
            f"(converter: {converter_name}, attempt: {record.attempts + 1})"
        )
        
        try:
            # Step 1: Validate file
            validation = converter.validate(source, context)
            record.last_confidence = validation.confidence
            
            # Notify validation callbacks
            self._notify_validation(source, validation)
            
            # Check if converter can handle this file
            if not validation.can_convert:
                logger.info(f"File rejected by validation: {validation.message}")
                result = ConverterResult.skipped_result(validation.message)
                self._statistics.record(ConversionStatus.SKIPPED)
                return result
            
            # Check confidence thresholds
            should_alarm, should_reject = validation.check_thresholds(
                context.alarm_threshold,
                context.reject_threshold
            )
            
            if should_reject:
                logger.warning(
                    f"File rejected due to low confidence ({validation.confidence:.2f}): "
                    f"{file_path.name}"
                )
                result = ConverterResult.skipped_result(
                    f"Confidence {validation.confidence:.2f} below reject threshold "
                    f"{context.reject_threshold}"
                )
                self._statistics.record(ConversionStatus.SKIPPED)
                return result
            
            if should_alarm:
                logger.warning(
                    f"Low confidence ({validation.confidence:.2f}) for {file_path.name}, "
                    f"proceeding with warning"
                )
            
            # Check if ready (for suspend/retry scenarios)
            if not validation.ready:
                logger.info(
                    f"File not ready: {validation.message} "
                    f"(missing: {', '.join(validation.missing_dependencies)})"
                )
                result = ConverterResult.suspended_result(
                    reason=validation.message,
                    retry_after=validation.retry_after or timedelta(seconds=self.retry_delay_seconds)
                )
                record.record_attempt(result.status, suspend_reason=validation.message)
                await self._handle_suspended(source, result, record)
                return result
            
            # Step 2: Convert file
            result = converter.convert(source, context)
            record.record_attempt(result.status, error=result.error)
            
            # Step 3: Handle result
            if result.status == ConversionStatus.SUCCESS:
                await self._handle_success(source, result, converter, context)
            
            elif result.status == ConversionStatus.FAILED:
                await self._handle_failure(source, result, converter, context)
            
            elif result.status == ConversionStatus.SUSPENDED:
                await self._handle_suspended(source, result, record)
            
            elif result.status == ConversionStatus.SKIPPED:
                logger.info(f"File skipped: {result.error}")
            
            self._statistics.record(result.status)
            return result
        
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            result = ConverterResult.failed_result(
                error=f"Processing error: {str(e)}"
            )
            record.record_attempt(ConversionStatus.FAILED, error=str(e))
            await self._handle_failure(source, result, converter, context)
            self._statistics.record(ConversionStatus.FAILED)
            return result
    
    # =========================================================================
    # Folder Processing
    # =========================================================================
    
    async def process_folder(
        self,
        folder_path: Path,
        converter_name: str,
        extra_arguments: Optional[Dict[str, Any]] = None
    ) -> ConverterResult:
        """
        Process a folder through a FolderConverter.
        
        Args:
            folder_path: Path to folder to convert
            converter_name: Name of converter to use
            extra_arguments: Additional arguments to merge with context
        
        Returns:
            ConverterResult with status and data
        """
        if not folder_path.exists():
            return ConverterResult.failed_result(
                error=f"Folder not found: {folder_path}"
            )
        
        if not folder_path.is_dir():
            return ConverterResult.failed_result(
                error=f"Path is not a folder: {folder_path}"
            )
        
        # Get converter
        converter = self.converters.get(converter_name)
        if not converter:
            return ConverterResult.failed_result(
                error=f"Converter not found: {converter_name}"
            )
        
        if not isinstance(converter, FolderConverter):
            return ConverterResult.failed_result(
                error=f"Converter '{converter_name}' is not a FolderConverter"
            )
        
        # Create context for this conversion
        context = self._create_context(extra_arguments)
        
        # Check if folder is ready
        if not converter.is_folder_ready(folder_path, context):
            logger.debug(f"Folder not ready: {folder_path}")
            return ConverterResult.skipped_result("Folder not ready")
        
        # Create source
        source = ConverterSource.from_folder(folder_path)
        
        # Get or create conversion record
        record_key = str(folder_path)
        record = self._conversion_records.get(record_key)
        if record is None:
            record = ConversionRecord(
                source_path=folder_path,
                converter_name=converter_name
            )
            self._conversion_records[record_key] = record
        
        logger.info(
            f"Processing folder: {folder_path.name} "
            f"(converter: {converter_name}, files: {len(source.files)})"
        )
        
        try:
            # Step 1: Validate folder
            validation = converter.validate(source, context)
            record.last_confidence = validation.confidence
            
            # Notify validation callbacks
            self._notify_validation(source, validation)
            
            if not validation.can_convert:
                logger.info(f"Folder rejected by validation: {validation.message}")
                result = ConverterResult.skipped_result(validation.message)
                self._statistics.record(ConversionStatus.SKIPPED)
                return result
            
            # Check confidence thresholds
            should_alarm, should_reject = validation.check_thresholds(
                context.alarm_threshold,
                context.reject_threshold
            )
            
            if should_reject:
                logger.warning(
                    f"Folder rejected due to low confidence ({validation.confidence:.2f})"
                )
                result = ConverterResult.skipped_result(
                    f"Confidence {validation.confidence:.2f} below reject threshold"
                )
                self._statistics.record(ConversionStatus.SKIPPED)
                return result
            
            # Step 2: Convert folder
            result = converter.convert(source, context)
            record.record_attempt(result.status, error=result.error)
            
            # Step 3: Handle result
            if result.status == ConversionStatus.SUCCESS:
                await self._handle_folder_success(source, result, converter, context)
            
            elif result.status == ConversionStatus.FAILED:
                await self._handle_folder_failure(source, result, converter, context)
            
            elif result.status == ConversionStatus.SUSPENDED:
                await self._handle_suspended(source, result, record)
            
            self._statistics.record(result.status)
            return result
        
        except Exception as e:
            logger.error(f"Error processing folder: {e}", exc_info=True)
            result = ConverterResult.failed_result(
                error=f"Processing error: {str(e)}"
            )
            record.record_attempt(ConversionStatus.FAILED, error=str(e))
            await self._handle_folder_failure(source, result, converter, context)
            self._statistics.record(ConversionStatus.FAILED)
            return result
    
    # =========================================================================
    # Success/Failure Handlers
    # =========================================================================
    
    async def _handle_success(
        self,
        source: ConverterSource,
        result: ConverterResult,
        converter: FileConverter,
        context: ConverterContext
    ) -> None:
        """Handle successful file conversion"""
        logger.info(f"Conversion successful: {source.primary_name}")
        
        # Call converter's on_success callback
        try:
            converter.on_success(source, result, context)
        except Exception as e:
            logger.error(f"Error in converter on_success: {e}")
        
        # Apply post-processing action
        if source.path:
            await self._apply_post_action(source.path, result.post_action, context, success=True)
        
        # Submit report to API if available
        if result.report and context.api_client and not context.dry_run:
            try:
                # This would integrate with report submission
                logger.info(f"Report ready for submission: {source.primary_name}")
            except Exception as e:
                logger.error(f"Error submitting report: {e}")
        
        # Notify success callbacks
        for callback in self._success_callbacks:
            try:
                callback(source, result)
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
        
        # Remove from tracking
        if source.path:
            self._conversion_records.pop(str(source.path), None)
    
    async def _handle_failure(
        self,
        source: ConverterSource,
        result: ConverterResult,
        converter: FileConverter,
        context: ConverterContext
    ) -> None:
        """Handle failed file conversion"""
        logger.error(f"Conversion failed: {source.primary_name} - {result.error}")
        
        # Call converter's on_failure callback
        try:
            converter.on_failure(source, result, context)
        except Exception as e:
            logger.error(f"Error in converter on_failure: {e}")
        
        # Move to error folder
        if source.path:
            await self._move_to_error(source.path, result.error, context)
        
        # Notify failure callbacks
        for callback in self._failure_callbacks:
            try:
                callback(source, result)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}")
        
        # Remove from tracking
        if source.path:
            self._conversion_records.pop(str(source.path), None)
    
    async def _handle_folder_success(
        self,
        source: ConverterSource,
        result: ConverterResult,
        converter: FolderConverter,
        context: ConverterContext
    ) -> None:
        """Handle successful folder conversion"""
        logger.info(f"Folder conversion successful: {source.primary_name}")
        
        # Call converter's on_success callback
        try:
            converter.on_success(source, result, context)
        except Exception as e:
            logger.error(f"Error in converter on_success: {e}")
        
        # Move entire folder if configured
        if source.path and converter.preserve_folder_structure:
            await self._move_folder(source.path, context.done_folder, context)
        
        # Notify success callbacks
        for callback in self._success_callbacks:
            try:
                callback(source, result)
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
        
        # Remove from tracking
        if source.path:
            self._conversion_records.pop(str(source.path), None)
    
    async def _handle_folder_failure(
        self,
        source: ConverterSource,
        result: ConverterResult,
        converter: FolderConverter,
        context: ConverterContext
    ) -> None:
        """Handle failed folder conversion"""
        logger.error(f"Folder conversion failed: {source.primary_name} - {result.error}")
        
        # Call converter's on_failure callback
        try:
            converter.on_failure(source, result, context)
        except Exception as e:
            logger.error(f"Error in converter on_failure: {e}")
        
        # Move folder to error
        if source.path:
            await self._move_folder(source.path, context.error_folder, context)
        
        # Notify failure callbacks
        for callback in self._failure_callbacks:
            try:
                callback(source, result)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}")
        
        # Remove from tracking
        if source.path:
            self._conversion_records.pop(str(source.path), None)
    
    async def _handle_suspended(
        self,
        source: ConverterSource,
        result: ConverterResult,
        record: ConversionRecord
    ) -> None:
        """Handle suspended conversion"""
        logger.info(
            f"Conversion suspended: {source.primary_name} - {result.suspend_reason} "
            f"(attempt {record.attempts}/{self.max_retry_attempts})"
        )
        
        # Check if we should retry
        if record.should_retry(self.max_retry_attempts):
            # Move to pending folder
            if source.path:
                await self._move_to_pending(
                    source.path, 
                    result.suspend_reason, 
                    self.base_context
                )
                logger.info(f"Moved to pending folder for retry: {source.primary_name}")
        else:
            # Max attempts reached, treat as failure
            logger.warning(
                f"Max retry attempts reached for {source.primary_name}, "
                f"moving to error folder"
            )
            if source.path:
                await self._move_to_error(
                    source.path,
                    f"Max retry attempts ({self.max_retry_attempts}) reached. "
                    f"Last reason: {result.suspend_reason}",
                    self.base_context
                )
            self._conversion_records.pop(str(source.path) if source.path else "", None)
    
    # =========================================================================
    # Post-Processing Actions
    # =========================================================================
    
    async def _apply_post_action(
        self,
        file_path: Path,
        action: PostProcessAction,
        context: ConverterContext,
        success: bool = True
    ) -> None:
        """Apply post-processing action to file"""
        target_folder = context.done_folder if success else context.error_folder
        
        if not target_folder:
            logger.warning("No target folder configured for post-action")
            return
        
        try:
            if action == PostProcessAction.DELETE:
                logger.info(f"Deleting file: {file_path.name}")
                file_path.unlink()
            
            elif action == PostProcessAction.MOVE:
                logger.info(f"Moving file to {target_folder.name}: {file_path.name}")
                target_path = target_folder / file_path.name
                target_path = self._unique_path(target_path)
                shutil.move(str(file_path), str(target_path))
            
            elif action == PostProcessAction.ZIP:
                logger.info(f"Zipping file to {target_folder.name}: {file_path.name}")
                zip_name = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = target_folder / zip_name
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_path, file_path.name)
                
                file_path.unlink()
            
            elif action == PostProcessAction.KEEP:
                logger.info(f"Keeping file in place: {file_path.name}")
        
        except Exception as e:
            logger.error(f"Error applying post-action {action.value}: {e}")
    
    async def _move_to_error(
        self, 
        file_path: Path, 
        error: Optional[str],
        context: ConverterContext
    ) -> None:
        """Move file to error folder with error info"""
        if not context.error_folder:
            logger.warning("No error folder configured")
            return
        
        try:
            target_path = self._unique_path(context.error_folder / file_path.name)
            shutil.move(str(file_path), str(target_path))
            
            # Write error info
            error_file = target_path.with_suffix(target_path.suffix + '.error.txt')
            with open(error_file, 'w') as f:
                f.write(f"Conversion failed: {error}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            
            logger.info(f"Moved to error folder: {target_path.name}")
        
        except Exception as e:
            logger.error(f"Error moving file to error folder: {e}")
    
    async def _move_to_pending(
        self, 
        file_path: Path, 
        reason: Optional[str],
        context: ConverterContext
    ) -> None:
        """Move file to pending folder for retry"""
        if not context.pending_folder:
            logger.warning("No pending folder configured")
            return
        
        try:
            target_path = self._unique_path(context.pending_folder / file_path.name)
            shutil.move(str(file_path), str(target_path))
            
            # Write suspend info
            suspend_file = target_path.with_suffix(target_path.suffix + '.pending.txt')
            with open(suspend_file, 'w') as f:
                f.write(f"Conversion suspended: {reason}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            
            logger.info(f"Moved to pending folder: {target_path.name}")
        
        except Exception as e:
            logger.error(f"Error moving file to pending folder: {e}")
    
    async def _move_folder(
        self,
        folder_path: Path,
        target_parent: Optional[Path],
        context: ConverterContext
    ) -> None:
        """Move entire folder to target location"""
        if not target_parent:
            logger.warning("No target folder configured")
            return
        
        try:
            target_path = self._unique_path(target_parent / folder_path.name)
            shutil.move(str(folder_path), str(target_path))
            logger.info(f"Moved folder to: {target_path}")
        except Exception as e:
            logger.error(f"Error moving folder: {e}")
    
    # =========================================================================
    # Retry Logic
    # =========================================================================
    
    async def retry_pending_files(
        self,
        converter_name: str,
        extra_arguments: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Retry pending conversions.
        
        Args:
            converter_name: Name of converter
            extra_arguments: Extra arguments for converter
        
        Returns:
            Number of files retried
        """
        context = self.base_context
        if not context.pending_folder:
            logger.warning("No pending folder configured")
            return 0
        
        logger.info(f"Retrying pending files for converter: {converter_name}")
        
        retried = 0
        
        for pending_file in context.pending_folder.glob("*"):
            if pending_file.suffix in [".txt", ".error", ".pending"]:
                continue
            
            if pending_file.is_dir():
                continue
            
            # Move back to drop folder
            if context.drop_folder:
                drop_path = context.drop_folder / pending_file.name
                
                try:
                    shutil.move(str(pending_file), str(drop_path))
                    
                    # Delete pending info file
                    pending_info = pending_file.with_suffix(pending_file.suffix + '.pending.txt')
                    if pending_info.exists():
                        pending_info.unlink()
                    
                    # Process file
                    await self.process_file(drop_path, converter_name, extra_arguments)
                    retried += 1
                
                except Exception as e:
                    logger.error(f"Error retrying pending file {pending_file.name}: {e}")
        
        logger.info(f"Retried {retried} pending files")
        return retried
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _create_context(
        self, 
        extra_arguments: Optional[Dict[str, Any]] = None
    ) -> ConverterContext:
        """Create a context for this conversion"""
        if extra_arguments:
            return self.base_context.copy_with(
                arguments={**self.base_context.arguments, **extra_arguments}
            )
        return self.base_context
    
    def _unique_path(self, path: Path) -> Path:
        """Get a unique path by adding timestamp if exists"""
        if not path.exists():
            return path
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return path.parent / f"{path.stem}_{timestamp}{path.suffix}"
    
    def _notify_validation(
        self, 
        source: ConverterSource, 
        validation: ValidationResult
    ) -> None:
        """Notify validation callbacks"""
        for callback in self._validation_callbacks:
            try:
                callback(source, validation)
            except Exception as e:
                logger.error(f"Error in validation callback: {e}")
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        context = self.base_context
        
        pending_count = 0
        error_count = 0
        done_count = 0
        
        if context.pending_folder and context.pending_folder.exists():
            pending_count = len([
                f for f in context.pending_folder.glob("*.pending.txt")
            ])
        
        if context.error_folder and context.error_folder.exists():
            error_count = len([
                f for f in context.error_folder.glob("*.error.txt")
            ])
        
        if context.done_folder and context.done_folder.exists():
            done_count = len([
                f for f in context.done_folder.glob("*")
                if f.is_file() and not f.suffix == ".txt"
            ])
        
        return {
            "active_conversions": len(self._conversion_records),
            "pending_files": pending_count,
            "error_files": error_count,
            "done_files": done_count,
            **self._statistics.to_dict(),
        }
