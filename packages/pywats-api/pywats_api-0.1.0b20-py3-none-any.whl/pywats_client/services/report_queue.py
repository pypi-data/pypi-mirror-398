"""
Report Queue Service

Manages offline report storage and automatic upload when online.
Reports are stored as JSON files in the reports folder and processed
when connection is available.
"""

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .connection import ConnectionService, ConnectionStatus

logger = logging.getLogger(__name__)


class ReportStatus(Enum):
    """Report queue status"""
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"


class QueuedReport:
    """Represents a report in the queue"""
    
    def __init__(
        self,
        report_data: Dict[str, Any],
        report_id: Optional[str] = None,
        status: ReportStatus = ReportStatus.PENDING,
        attempts: int = 0,
        created_at: Optional[datetime] = None,
        last_attempt: Optional[datetime] = None,
        error: Optional[str] = None
    ):
        self.report_id = report_id or str(uuid.uuid4())
        self.report_data = report_data
        self.status = status
        self.attempts = attempts
        self.created_at = created_at or datetime.now()
        self.last_attempt = last_attempt
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'report_id': self.report_id,
            'report_data': self.report_data,
            'status': self.status.value,
            'attempts': self.attempts,
            'created_at': self.created_at.isoformat(),
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'error': self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedReport':
        """Create from dictionary"""
        return cls(
            report_id=data['report_id'],
            report_data=data['report_data'],
            status=ReportStatus(data['status']),
            attempts=data.get('attempts', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_attempt=datetime.fromisoformat(data['last_attempt']) if data.get('last_attempt') else None,
            error=data.get('error')
        )


class ReportQueueService:
    """
    Manages offline report queue.
    
    Features:
    - Queue reports when offline
    - Automatic upload when online
    - Retry with exponential backoff
    - Failed report management
    """
    
    def __init__(
        self,
        connection: ConnectionService,
        reports_folder: Path,
        max_retries: int = 5,
        retry_interval: int = 60
    ):
        self.connection = connection
        self.reports_folder = Path(reports_folder)
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        
        self._queue: List[QueuedReport] = []
        self._process_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Ensure folders exist
        self.pending_folder = self.reports_folder / "pending"
        self.failed_folder = self.reports_folder / "failed"
        self.completed_folder = self.reports_folder / "completed"
        
        for folder in [self.pending_folder, self.failed_folder, self.completed_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Load existing queued reports
        self._load_pending_reports()
        
        # Register for connection status changes
        self.connection.on_status_change(self._on_connection_change)
    
    async def start(self) -> None:
        """Start the queue processing service"""
        if self._running:
            return
        
        self._running = True
        logger.info(f"Starting report queue service (folder: {self.reports_folder})")
        
        # Start processing task
        self._process_task = asyncio.create_task(self._process_loop())
    
    async def stop(self) -> None:
        """Stop the queue processing service"""
        self._running = False
        
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None
        
        logger.info("Report queue service stopped")
    
    async def submit(self, report_data: Dict[str, Any]) -> bool:
        """
        Submit a report for upload.
        
        If online, attempts immediate upload.
        If offline, queues for later upload.
        
        Returns True if queued/uploaded successfully.
        """
        try:
            # Create queued report
            queued = QueuedReport(report_data)
            
            # Try immediate upload if online
            if self.connection.status == ConnectionStatus.ONLINE:
                if await self._upload_report(queued):
                    return True
            
            # Queue for later
            self._queue.append(queued)
            self._save_report(queued)
            logger.info(f"Report {queued.report_id} queued for upload")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit report: {e}")
            return False
    
    async def _upload_report(self, queued: QueuedReport) -> bool:
        """
        Upload a single report to WATS.
        
        Returns True if upload successful.
        """
        client = self.connection.get_client()
        if not client:
            return False
        
        try:
            queued.status = ReportStatus.PROCESSING
            queued.last_attempt = datetime.now()
            queued.attempts += 1
            
            # Submit to WATS using WSJF (dict) format
            result = client.report.submit_wsjf(queued.report_data)
            
            if result:
                queued.status = ReportStatus.COMPLETED
                self._move_to_completed(queued)
                logger.info(f"Report {queued.report_id} uploaded successfully")
                return True
            else:
                raise Exception("Submit returned None/False")
                
        except Exception as e:
            queued.error = str(e)
            queued.status = ReportStatus.PENDING
            
            if queued.attempts >= self.max_retries:
                queued.status = ReportStatus.FAILED
                self._move_to_failed(queued)
                logger.error(f"Report {queued.report_id} failed after {queued.attempts} attempts: {e}")
            else:
                self._save_report(queued)
                logger.warning(f"Report {queued.report_id} upload failed (attempt {queued.attempts}): {e}")
            
            return False
    
    async def _process_loop(self) -> None:
        """Background task to process queued reports"""
        while self._running:
            try:
                await asyncio.sleep(self.retry_interval)
                
                if self.connection.status == ConnectionStatus.ONLINE:
                    await self._process_queue()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _process_queue(self) -> None:
        """Process all pending reports in the queue"""
        pending = [r for r in self._queue if r.status == ReportStatus.PENDING]
        
        for report in pending:
            if not self._running:
                break
            
            if self.connection.status != ConnectionStatus.ONLINE:
                break
            
            await self._upload_report(report)
            await asyncio.sleep(1)  # Small delay between uploads
        
        # Remove completed/failed from in-memory queue
        self._queue = [r for r in self._queue if r.status == ReportStatus.PENDING]
    
    def _on_connection_change(self, status: ConnectionStatus) -> None:
        """Handle connection status changes"""
        if status == ConnectionStatus.ONLINE and self._running:
            # Process queue when coming online
            asyncio.create_task(self._process_queue())
    
    def _load_pending_reports(self) -> None:
        """Load pending reports from disk"""
        try:
            for file in self.pending_folder.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    report = QueuedReport.from_dict(data)
                    self._queue.append(report)
                except Exception as e:
                    logger.warning(f"Failed to load report {file}: {e}")
            
            logger.info(f"Loaded {len(self._queue)} pending reports from queue")
        except Exception as e:
            logger.error(f"Failed to load pending reports: {e}")
    
    def _save_report(self, report: QueuedReport) -> None:
        """Save report to pending folder"""
        try:
            file_path = self.pending_folder / f"{report.report_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save report {report.report_id}: {e}")
    
    def _move_to_completed(self, report: QueuedReport) -> None:
        """Move report to completed folder"""
        try:
            src = self.pending_folder / f"{report.report_id}.json"
            dst = self.completed_folder / f"{report.report_id}.json"
            
            if src.exists():
                src.rename(dst)
            
            # Remove from queue
            self._queue = [r for r in self._queue if r.report_id != report.report_id]
        except Exception as e:
            logger.error(f"Failed to move report to completed: {e}")
    
    def _move_to_failed(self, report: QueuedReport) -> None:
        """Move report to failed folder"""
        try:
            src = self.pending_folder / f"{report.report_id}.json"
            dst = self.failed_folder / f"{report.report_id}.json"
            
            # Update status in file
            with open(dst, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2)
            
            if src.exists():
                src.unlink()
            
            # Remove from queue
            self._queue = [r for r in self._queue if r.report_id != report.report_id]
        except Exception as e:
            logger.error(f"Failed to move report to failed: {e}")
    
    async def retry_failed(self, report_id: str) -> bool:
        """
        Retry a failed report.
        
        Returns True if moved back to pending queue.
        """
        try:
            src = self.failed_folder / f"{report_id}.json"
            if not src.exists():
                return False
            
            with open(src, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            report = QueuedReport.from_dict(data)
            report.status = ReportStatus.PENDING
            report.attempts = 0
            report.error = None
            
            self._queue.append(report)
            self._save_report(report)
            src.unlink()
            
            logger.info(f"Report {report_id} moved back to pending queue")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry report {report_id}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status"""
        pending = len([r for r in self._queue if r.status == ReportStatus.PENDING])
        failed = len(list(self.failed_folder.glob("*.json")))
        
        return {
            "pending": pending,
            "failed": failed,
            "folder": str(self.reports_folder),
        }
    
    def get_pending_reports(self) -> List[Dict[str, Any]]:
        """Get list of pending reports"""
        return [r.to_dict() for r in self._queue if r.status == ReportStatus.PENDING]
    
    def get_failed_reports(self) -> List[Dict[str, Any]]:
        """Get list of failed reports"""
        failed = []
        for file in self.failed_folder.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    failed.append(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                logger.debug(f"Could not load failed report {file}: {e}")
                continue
        return failed
