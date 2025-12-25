"""
Converter Processor Service

Handles the complete file conversion workflow:
- Monitor drop folders for new files
- Validate files with converters
- Convert qualified files
- Post-process based on PPA settings (Move, Zip, Delete)
- Queue reports for submission
- Handle suspended conversions
"""

import asyncio
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum

from ..converters.base import (
    ConverterBase,
    ConverterResult,
    ConversionStatus,
    PostProcessAction,
    FileInfo,
    ConverterArguments,
)

logger = logging.getLogger(__name__)


class ConversionRecord:
    """
    Record of a conversion attempt.
    
    Tracks conversion history for retry logic and reporting.
    """
    
    def __init__(
        self,
        file_path: Path,
        converter_name: str,
        timestamp: Optional[datetime] = None
    ):
        self.file_path = file_path
        self.converter_name = converter_name
        self.timestamp = timestamp or datetime.now()
        self.attempts = 0
        self.last_attempt: Optional[datetime] = None
        self.last_status: Optional[ConversionStatus] = None
        self.last_error: Optional[str] = None
        self.suspend_reason: Optional[str] = None
    
    def record_attempt(
        self,
        status: ConversionStatus,
        error: Optional[str] = None,
        suspend_reason: Optional[str] = None
    ) -> None:
        """Record a conversion attempt"""
        self.attempts += 1
        self.last_attempt = datetime.now()
        self.last_status = status
        self.last_error = error
        self.suspend_reason = suspend_reason
    
    def should_retry(self, max_attempts: int = 3) -> bool:
        """Check if file should be retried"""
        if self.last_status != ConversionStatus.SUSPENDED:
            return False
        return self.attempts < max_attempts


class ConverterProcessor:
    """
    Processes files through converters with full workflow support.
    
    Features:
    - File validation before conversion
    - Conversion with converter arguments
    - Post-processing actions (Move, Zip, Delete, Keep)
    - Suspended conversion retry logic
    - Error folder management
    - Success callbacks
    - Comprehensive logging
    
    Usage:
        processor = ConverterProcessor(
            api_client=wats_client,
            converters={"csv": csv_converter},
            drop_folder=Path("./uploads"),
            done_folder=Path("./uploads/Done"),
            error_folder=Path("./uploads/Error")
        )
        
        # Process a file
        result = await processor.process_file(
            file_path=Path("./uploads/test.csv"),
            converter_name="csv",
            user_settings={"delimiter": ","}
        )
        
        # Handle result
        if result.status == ConversionStatus.SUCCESS:
            print(f"Converted: {result.report}")
    """
    
    def __init__(
        self,
        api_client: Any,
        converters: Dict[str, ConverterBase],
        drop_folder: Path,
        done_folder: Optional[Path] = None,
        error_folder: Optional[Path] = None,
        suspended_folder: Optional[Path] = None,
        max_retry_attempts: int = 3,
        retry_delay: int = 60  # seconds
    ):
        """
        Initialize converter processor.
        
        Args:
            api_client: pyWATS API client instance
            converters: Dictionary of converter_name -> converter_instance
            drop_folder: Folder being monitored
            done_folder: Folder for successfully processed files (default: drop_folder/Done)
            error_folder: Folder for failed conversions (default: drop_folder/Error)
            suspended_folder: Folder for suspended files (default: drop_folder/Suspended)
            max_retry_attempts: Maximum retry attempts for suspended conversions
            retry_delay: Delay between retry attempts (seconds)
        """
        self.api_client = api_client
        self.converters = converters
        self.drop_folder = drop_folder
        self.done_folder = done_folder or (drop_folder / "Done")
        self.error_folder = error_folder or (drop_folder / "Error")
        self.suspended_folder = suspended_folder or (drop_folder / "Suspended")
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
        
        # Create folders if they don't exist
        self.done_folder.mkdir(parents=True, exist_ok=True)
        self.error_folder.mkdir(parents=True, exist_ok=True)
        self.suspended_folder.mkdir(parents=True, exist_ok=True)
        
        # Conversion tracking
        self._conversion_records: Dict[str, ConversionRecord] = {}
        self._success_callbacks: List[Callable[[Path, ConverterResult], None]] = []
        self._failure_callbacks: List[Callable[[Path, ConverterResult], None]] = []
    
    def on_success(self, callback: Callable[[Path, ConverterResult], None]) -> None:
        """Register callback for successful conversions"""
        self._success_callbacks.append(callback)
    
    def on_failure(self, callback: Callable[[Path, ConverterResult], None]) -> None:
        """Register callback for failed conversions"""
        self._failure_callbacks.append(callback)
    
    async def process_file(
        self,
        file_path: Path,
        converter_name: str,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> ConverterResult:
        """
        Process a file through a converter.
        
        Args:
            file_path: Path to file to convert
            converter_name: Name of converter to use
            user_settings: User-configured settings for converter
        
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
        
        # Create file info
        file_info = FileInfo(file_path)
        
        # Get or create conversion record
        record_key = str(file_path)
        record = self._conversion_records.get(
            record_key,
            ConversionRecord(file_path, converter_name)
        )
        self._conversion_records[record_key] = record
        
        logger.info(
            f"Processing file: {file_path.name} "
            f"(converter: {converter_name}, attempt: {record.attempts + 1})"
        )
        
        try:
            # Step 1: Validate file
            valid, reason = converter.validate_file(file_info)
            if not valid:
                logger.warning(f"File validation failed: {reason}")
                result = ConverterResult.skipped_result(reason)
                record.record_attempt(ConversionStatus.SKIPPED, error=reason)
                return result
            
            # Step 2: Prepare converter arguments
            args = ConverterArguments(
                api_client=self.api_client,
                file_info=file_info,
                drop_folder=self.drop_folder,
                done_folder=self.done_folder,
                error_folder=self.error_folder,
                user_settings=user_settings or {}
            )
            
            # Step 3: Convert file
            result = converter.convert_file(file_path, args)
            
            # Step 4: Record attempt
            record.record_attempt(
                result.status,
                error=result.error,
                suspend_reason=result.suspend_reason
            )
            
            # Step 5: Handle result
            if result.status == ConversionStatus.SUCCESS:
                await self._handle_success(file_path, result, converter, args)
            
            elif result.status == ConversionStatus.FAILED:
                await self._handle_failure(file_path, result, converter, args)
            
            elif result.status == ConversionStatus.SUSPENDED:
                await self._handle_suspended(file_path, result, record)
            
            elif result.status == ConversionStatus.SKIPPED:
                logger.info(f"File skipped: {result.error}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            result = ConverterResult.failed_result(
                error=f"Processing error: {str(e)}"
            )
            record.record_attempt(ConversionStatus.FAILED, error=str(e))
            await self._handle_failure(file_path, result, converter, args)
            return result
    
    async def _handle_success(
        self,
        file_path: Path,
        result: ConverterResult,
        converter: ConverterBase,
        args: ConverterArguments
    ) -> None:
        """Handle successful conversion"""
        logger.info(f"Conversion successful: {file_path.name}")
        
        # Call converter's on_success
        try:
            converter.on_success(file_path, result, args)
        except Exception as e:
            logger.error(f"Error in converter on_success: {e}")
        
        # Apply post-processing action
        await self._apply_post_action(file_path, result.post_action, success=True)
        
        # Notify success callbacks
        for callback in self._success_callbacks:
            try:
                callback(file_path, result)
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
        
        # Remove from tracking
        self._conversion_records.pop(str(file_path), None)
    
    async def _handle_failure(
        self,
        file_path: Path,
        result: ConverterResult,
        converter: ConverterBase,
        args: ConverterArguments
    ) -> None:
        """Handle failed conversion"""
        logger.error(f"Conversion failed: {file_path.name} - {result.error}")
        
        # Call converter's on_failure
        try:
            converter.on_failure(file_path, result, args)
        except Exception as e:
            logger.error(f"Error in converter on_failure: {e}")
        
        # Move to error folder
        await self._move_to_error(file_path, result.error)
        
        # Notify failure callbacks
        for callback in self._failure_callbacks:
            try:
                callback(file_path, result)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}")
        
        # Remove from tracking
        self._conversion_records.pop(str(file_path), None)
    
    async def _handle_suspended(
        self,
        file_path: Path,
        result: ConverterResult,
        record: ConversionRecord
    ) -> None:
        """Handle suspended conversion"""
        logger.info(
            f"Conversion suspended: {file_path.name} - {result.suspend_reason} "
            f"(attempt {record.attempts}/{self.max_retry_attempts})"
        )
        
        # Check if we should retry
        if record.should_retry(self.max_retry_attempts):
            # Move to suspended folder
            await self._move_to_suspended(file_path, result.suspend_reason)
            logger.info(f"File moved to suspended folder for retry: {file_path.name}")
        
        else:
            # Max attempts reached, treat as failure
            logger.warning(
                f"Max retry attempts reached for {file_path.name}, "
                f"moving to error folder"
            )
            await self._move_to_error(
                file_path,
                f"Max retry attempts ({self.max_retry_attempts}) reached. "
                f"Last reason: {result.suspend_reason}"
            )
            self._conversion_records.pop(str(file_path), None)
    
    async def _apply_post_action(
        self,
        file_path: Path,
        action: PostProcessAction,
        success: bool = True
    ) -> None:
        """
        Apply post-processing action to file.
        
        Args:
            file_path: Path to file
            action: Post-processing action
            success: Whether conversion was successful
        """
        target_folder = self.done_folder if success else self.error_folder
        
        try:
            if action == PostProcessAction.DELETE:
                logger.info(f"Deleting file: {file_path.name}")
                file_path.unlink()
            
            elif action == PostProcessAction.MOVE:
                logger.info(f"Moving file to {target_folder.name}: {file_path.name}")
                target_path = target_folder / file_path.name
                shutil.move(str(file_path), str(target_path))
            
            elif action == PostProcessAction.ZIP:
                logger.info(f"Zipping and moving file to {target_folder.name}: {file_path.name}")
                zip_name = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = target_folder / zip_name
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_path, file_path.name)
                
                # Delete original
                file_path.unlink()
            
            elif action == PostProcessAction.KEEP:
                logger.info(f"Keeping file in place: {file_path.name}")
                # Do nothing
        
        except Exception as e:
            logger.error(f"Error applying post-action {action.value}: {e}")
    
    async def _move_to_error(self, file_path: Path, error: Optional[str]) -> None:
        """Move file to error folder with error info"""
        try:
            target_path = self.error_folder / file_path.name
            
            # If file exists, add timestamp
            if target_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                target_path = self.error_folder / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            shutil.move(str(file_path), str(target_path))
            
            # Write error info
            error_file = target_path.with_suffix(target_path.suffix + '.error.txt')
            with open(error_file, 'w') as f:
                f.write(f"Conversion failed: {error}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            
            logger.info(f"Moved to error folder: {target_path.name}")
        
        except Exception as e:
            logger.error(f"Error moving file to error folder: {e}")
    
    async def _move_to_suspended(self, file_path: Path, reason: Optional[str]) -> None:
        """Move file to suspended folder for retry"""
        try:
            target_path = self.suspended_folder / file_path.name
            
            # If file exists, add timestamp
            if target_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                target_path = self.suspended_folder / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            shutil.move(str(file_path), str(target_path))
            
            # Write suspend info
            suspend_file = target_path.with_suffix(target_path.suffix + '.suspend.txt')
            with open(suspend_file, 'w') as f:
                f.write(f"Conversion suspended: {reason}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            
            logger.info(f"Moved to suspended folder: {target_path.name}")
        
        except Exception as e:
            logger.error(f"Error moving file to suspended folder: {e}")
    
    async def retry_suspended_files(self, converter_name: str, user_settings: Optional[Dict[str, Any]] = None) -> int:
        """
        Retry suspended conversions.
        
        Args:
            converter_name: Name of converter
            user_settings: User settings for converter
        
        Returns:
            Number of files retried
        """
        logger.info(f"Retrying suspended files for converter: {converter_name}")
        
        retried = 0
        
        # Find suspended files
        for suspended_file in self.suspended_folder.glob("*"):
            if suspended_file.suffix in [".txt", ".error", ".suspend"]:
                continue
            
            # Move back to drop folder
            drop_path = self.drop_folder / suspended_file.name
            
            try:
                shutil.move(str(suspended_file), str(drop_path))
                
                # Delete suspend info file
                suspend_info = suspended_file.with_suffix(suspended_file.suffix + '.suspend.txt')
                if suspend_info.exists():
                    suspend_info.unlink()
                
                # Process file
                await self.process_file(drop_path, converter_name, user_settings)
                retried += 1
            
            except Exception as e:
                logger.error(f"Error retrying suspended file {suspended_file.name}: {e}")
        
        logger.info(f"Retried {retried} suspended files")
        return retried
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        total_records = len(self._conversion_records)
        suspended = sum(
            1 for r in self._conversion_records.values()
            if r.last_status == ConversionStatus.SUSPENDED
        )
        
        return {
            "active_conversions": total_records,
            "suspended_conversions": suspended,
            "done_files": len(list(self.done_folder.glob("*"))),
            "error_files": len(list(self.error_folder.glob("*.error.txt"))),
            "suspended_files": len(list(self.suspended_folder.glob("*.suspend.txt"))),
        }
