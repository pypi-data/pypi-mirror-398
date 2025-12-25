"""
Scheduled Converter Base Class

Base class for scheduled converters that run on a timer or cron schedule.
These are NOT triggered by file events - they run periodically.

Use cases:
- Polling a database for records to convert
- Syncing with external APIs on a schedule
- Periodic cleanup or aggregation tasks
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging

from .models import (
    ConverterType,
    ConverterSource,
    ConverterResult,
    ArgumentDefinition,
)

if TYPE_CHECKING:
    from .context import ConverterContext

logger = logging.getLogger(__name__)


class ScheduledConverter(ABC):
    """
    Base class for scheduled converters.
    
    Runs on a timer (every N seconds) or cron schedule (at specific times).
    Not triggered by file events.
    
    Use Cases:
        - Poll a database for new records
        - Sync with an external API
        - Aggregate multiple reports into one
        - Cleanup or maintenance tasks
    
    Implementation Requirements:
        - Override `name` property (required)
        - Override `run()` method (required)
        - Override `schedule_interval` OR `cron_expression` (one required)
    
    Example (Database Polling):
        class DatabasePollingConverter(ScheduledConverter):
            @property
            def name(self) -> str:
                return "Database Poller"
            
            @property
            def description(self) -> str:
                return "Polls MES database for new test records"
            
            @property
            def schedule_interval(self) -> timedelta:
                return timedelta(minutes=5)  # Run every 5 minutes
            
            @property
            def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
                return {
                    "connection_string": ArgumentDefinition(
                        arg_type=ArgumentType.STRING,
                        required=True,
                        description="Database connection string"
                    ),
                    "batch_size": ArgumentDefinition(
                        arg_type=ArgumentType.INTEGER,
                        default=100,
                        description="Max records per batch"
                    ),
                }
            
            async def run(self, context: ConverterContext) -> List[ConverterResult]:
                conn_str = context.get_argument("connection_string")
                batch_size = context.get_argument("batch_size", 100)
                
                results = []
                
                # Connect to database
                records = await self.fetch_new_records(conn_str, batch_size)
                
                for record in records:
                    try:
                        # Convert each record
                        source = ConverterSource.from_database_record(
                            record_id=record["id"],
                            metadata=record
                        )
                        
                        report = self.build_report(record)
                        
                        result = ConverterResult.success_result(
                            report=report,
                            source_id=record["id"]
                        )
                        results.append(result)
                        
                        # Mark as processed in database
                        await self.mark_processed(conn_str, record["id"])
                        
                    except Exception as e:
                        results.append(ConverterResult.failed_result(str(e)))
                
                return results
    
    Example (Cron-based):
        class NightlyReportAggregator(ScheduledConverter):
            @property
            def name(self) -> str:
                return "Nightly Report Aggregator"
            
            @property
            def cron_expression(self) -> str:
                return "0 2 * * *"  # Run at 2:00 AM daily
            
            async def run(self, context: ConverterContext) -> List[ConverterResult]:
                # Aggregate yesterday's reports
                yesterday = datetime.now() - timedelta(days=1)
                
                reports = await context.api_client.get_reports(
                    start_date=yesterday
                )
                
                # Create summary report
                summary = self.aggregate_reports(reports)
                
                return [ConverterResult.success_result(report=summary)]
    """
    
    def __init__(self) -> None:
        """Initialize the converter"""
        self._arguments: Dict[str, Any] = {}
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._is_running: bool = False
    
    # =========================================================================
    # Required Properties (must override)
    # =========================================================================
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of the converter.
        
        This is displayed in the GUI and used for logging.
        """
        pass
    
    # =========================================================================
    # Schedule Properties (override one)
    # =========================================================================
    
    @property
    def schedule_interval(self) -> Optional[timedelta]:
        """
        Time interval between runs.
        
        If set, the converter runs every N seconds/minutes/hours.
        Mutually exclusive with cron_expression (interval takes precedence).
        
        Examples:
            timedelta(seconds=30)   - Every 30 seconds
            timedelta(minutes=5)    - Every 5 minutes
            timedelta(hours=1)      - Every hour
        
        Default: None (use cron_expression instead)
        """
        return None
    
    @property
    def cron_expression(self) -> Optional[str]:
        """
        Cron expression for scheduled runs.
        
        If set (and schedule_interval is None), runs at specific times.
        Uses standard 5-field cron format: minute hour day month weekday
        
        Examples:
            "*/5 * * * *"     - Every 5 minutes
            "0 * * * *"       - Every hour at :00
            "0 2 * * *"       - Daily at 2:00 AM
            "0 0 * * 0"       - Weekly on Sunday at midnight
            "0 9 1 * *"       - Monthly on the 1st at 9:00 AM
        
        Default: None (use schedule_interval instead)
        """
        return None
    
    # =========================================================================
    # Optional Properties (can override)
    # =========================================================================
    
    @property
    def converter_type(self) -> ConverterType:
        """Converter type - always SCHEDULED for this class"""
        return ConverterType.SCHEDULED
    
    @property
    def version(self) -> str:
        """Version string for the converter"""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Description of what this converter does"""
        return ""
    
    @property
    def author(self) -> str:
        """Author/maintainer of this converter"""
        return ""
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """
        Define configurable arguments for this converter.
        
        These are exposed in the GUI for user configuration.
        Values are accessible via context.get_argument() during run().
        
        Returns:
            Dictionary of argument_name -> ArgumentDefinition
        """
        return {}
    
    @property
    def run_on_startup(self) -> bool:
        """
        Whether to run immediately when the converter is loaded.
        
        If True, runs once when the client starts (before first scheduled run).
        If False, waits for the first scheduled interval.
        
        Default: False
        """
        return False
    
    @property
    def max_concurrent_runs(self) -> int:
        """
        Maximum number of concurrent run() executions.
        
        If a scheduled run is triggered while a previous run is still
        executing, this controls whether it waits or runs in parallel.
        
        Default: 1 (no concurrent runs - skip if already running)
        """
        return 1
    
    @property
    def timeout(self) -> Optional[timedelta]:
        """
        Maximum time allowed for a single run.
        
        If run() takes longer than this, it will be cancelled.
        
        Default: None (no timeout)
        """
        return None
    
    @property
    def retry_on_failure(self) -> bool:
        """
        Whether to retry immediately if run() fails.
        
        If True, retries once with a short delay after failure.
        If False, waits for the next scheduled run.
        
        Default: False
        """
        return False
    
    @property
    def retry_delay(self) -> timedelta:
        """
        Delay before retrying after failure (if retry_on_failure is True).
        
        Default: 30 seconds
        """
        return timedelta(seconds=30)
    
    # =========================================================================
    # Schedule State (read-only)
    # =========================================================================
    
    @property
    def last_run(self) -> Optional[datetime]:
        """When the converter last ran (or None if never)"""
        return self._last_run
    
    @property
    def next_run(self) -> Optional[datetime]:
        """When the converter will next run (or None if not scheduled)"""
        return self._next_run
    
    @property
    def is_running(self) -> bool:
        """Whether the converter is currently running"""
        return self._is_running
    
    # =========================================================================
    # Main Entry Point (must override)
    # =========================================================================
    
    @abstractmethod
    async def run(self, context: "ConverterContext") -> List[ConverterResult]:
        """
        Main execution method - called on schedule.
        
        This is the primary method for scheduled converters.
        It may process multiple records/items in one run.
        
        Unlike file/folder converters, scheduled converters:
        - Are not tied to a specific file or folder
        - May create multiple reports per run
        - Are responsible for tracking what has been processed
        
        Args:
            context: Converter context with API client and settings
                - context.api_client: WATS API client
                - context.get_argument(name): Get configured argument value
        
        Returns:
            List of ConverterResult objects (one per processed item).
            Return an empty list if nothing to process.
        
        Example (Database Polling):
            async def run(self, context) -> List[ConverterResult]:
                results = []
                
                # Fetch unprocessed records
                records = await self.query_database("SELECT * FROM tests WHERE processed = 0")
                
                for record in records:
                    try:
                        report = self.convert_record(record)
                        
                        # Create a source reference for tracking
                        source = ConverterSource.from_database_record(
                            record_id=record["id"],
                            metadata={"table": "tests"}
                        )
                        
                        results.append(ConverterResult.success_result(
                            report=report,
                            source=source
                        ))
                        
                        # Mark as processed
                        await self.mark_processed(record["id"])
                        
                    except Exception as e:
                        results.append(ConverterResult.failed_result(str(e)))
                
                return results
        
        Example (API Sync):
            async def run(self, context) -> List[ConverterResult]:
                import httpx
                
                api_key = context.get_argument("api_key")
                endpoint = context.get_argument("endpoint")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        endpoint,
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    data = response.json()
                
                if not data.get("items"):
                    return []  # Nothing to process
                
                results = []
                for item in data["items"]:
                    report = self.transform_item(item)
                    results.append(ConverterResult.success_result(report=report))
                
                return results
        """
        pass
    
    # =========================================================================
    # Lifecycle Callbacks (optional override)
    # =========================================================================
    
    def on_load(self, context: "ConverterContext") -> None:
        """
        Called when the converter is loaded.
        
        Use for one-time initialization (e.g., database connections).
        """
        pass
    
    def on_unload(self) -> None:
        """
        Called when the converter is unloaded.
        
        Use for cleanup (e.g., closing connections).
        """
        pass
    
    def on_run_start(self, context: "ConverterContext") -> None:
        """
        Called at the beginning of each scheduled run.
        
        Use for per-run initialization.
        """
        pass
    
    def on_run_complete(
        self, 
        results: List[ConverterResult], 
        context: "ConverterContext"
    ) -> None:
        """
        Called at the end of each scheduled run.
        
        Use for per-run cleanup or logging.
        
        Args:
            results: List of results from the run
            context: Converter context
        """
        pass
    
    def on_run_error(
        self, 
        error: Exception, 
        context: "ConverterContext"
    ) -> None:
        """
        Called if run() raises an exception.
        
        Use for error logging or notifications.
        
        Args:
            error: The exception that was raised
            context: Converter context
        """
        pass
    
    # =========================================================================
    # Helper Methods (for subclasses)
    # =========================================================================
    
    def get_schedule_description(self) -> str:
        """
        Human-readable description of the schedule.
        
        Returns:
            String like "Every 5 minutes" or "Daily at 2:00 AM"
        """
        if self.schedule_interval:
            total_seconds = self.schedule_interval.total_seconds()
            if total_seconds < 60:
                return f"Every {int(total_seconds)} seconds"
            elif total_seconds < 3600:
                return f"Every {int(total_seconds / 60)} minutes"
            elif total_seconds < 86400:
                hours = total_seconds / 3600
                if hours == int(hours):
                    return f"Every {int(hours)} hours"
                return f"Every {hours:.1f} hours"
            else:
                days = total_seconds / 86400
                if days == int(days):
                    return f"Every {int(days)} days"
                return f"Every {days:.1f} days"
        
        elif self.cron_expression:
            return f"Cron: {self.cron_expression}"
        
        return "Not scheduled"
    
    def calculate_next_run(self, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate the next run time based on schedule.
        
        Args:
            from_time: Calculate next run after this time (default: now)
        
        Returns:
            Next run datetime, or None if not schedulable
        """
        from_time = from_time or datetime.now()
        
        if self.schedule_interval:
            return from_time + self.schedule_interval
        
        if self.cron_expression:
            # Parse cron expression
            try:
                from croniter import croniter
                cron = croniter(self.cron_expression, from_time)
                return cron.get_next(datetime)
            except ImportError:
                logger.warning(
                    "croniter package not installed. "
                    "Install with: pip install croniter"
                )
                return None
            except Exception as e:
                logger.error(f"Invalid cron expression '{self.cron_expression}': {e}")
                return None
        
        return None
    
    def should_run_now(self) -> bool:
        """
        Check if the converter should run now based on schedule.
        
        Returns:
            True if should run
        """
        if self._is_running:
            if self.max_concurrent_runs <= 1:
                return False
        
        if self._next_run is None:
            return False
        
        return datetime.now() >= self._next_run
