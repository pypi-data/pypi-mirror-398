"""pyWATS - Main API Class

The main entry point for the pyWATS library.
"""
import logging
from typing import Optional, Union

from .core.client import HttpClient
from .core.station import Station, StationRegistry

logger = logging.getLogger(__name__)
from .core.exceptions import ErrorMode, ErrorHandler
from .domains.product import (
    ProductService, 
    ProductRepository,
    ProductServiceInternal,
    ProductRepositoryInternal,
)
from .domains.asset import (
    AssetService,
    AssetRepository,
    AssetServiceInternal,
    AssetRepositoryInternal,
)
from .domains.production import (
    ProductionService,
    ProductionRepository,
    ProductionServiceInternal,
    ProductionRepositoryInternal,
)
from .domains.report import ReportService, ReportRepository
from .domains.software import SoftwareService, SoftwareRepository
from .domains.analytics import AnalyticsService, AnalyticsRepository
from .domains.rootcause import RootCauseService, RootCauseRepository
from .domains.process import (
    ProcessService, 
    ProcessRepository,
    ProcessServiceInternal,
    ProcessRepositoryInternal,
)


class pyWATS:
    """
    Main pyWATS API class.
    
    Provides access to all WATS functionality through module properties:
    - product: Product management
    - asset: Asset management
    - production: Production/unit management
    - report: Report querying and submission
    - software: Software distribution
    - analytics: Yield statistics, KPIs, and failure analysis (also available as 'app')
    - rootcause: Ticketing system for issue collaboration
    
    Station Configuration:
        pyWATS supports a Station concept for managing test station identity.
        A Station encapsulates: name (machineName), location, and purpose.
        
        Single station mode (most common):
            api = pyWATS(
                base_url="https://your-wats-server.com",
                token="your-api-token",
                station=Station("TEST-STATION-01", "Lab A", "Production")
            )
        
        Multi-station mode (hub):
            api = pyWATS(base_url="...", token="...")
            api.stations.add("line-1", Station("PROD-LINE-1", "Building A", "Production"))
            api.stations.add("line-2", Station("PROD-LINE-2", "Building A", "Production"))
            api.stations.set_active("line-1")
    
    Usage:
        from pywats import pyWATS
        
        # Initialize the API
        api = pyWATS(
            base_url="https://your-wats-server.com",
            token="your-api-token"
        )
        
        # Access product operations
        products = api.product.get_products()
        product = api.product.get_product("PART-001")
        
        # Access report operations
        headers = api.report.query_uut_headers()
        report = api.report.get_report("report-uuid")
        
        # Access statistics
        yield_data = api.analytics.get_dynamic_yield(filter)
    
    Authentication:
        The API uses Basic authentication. The token should be a Base64-encoded
        string in the format "username:password". The Authorization header will
        be sent as: "Basic <token>"
    """
    
    # Default process cache refresh interval (5 minutes)
    DEFAULT_PROCESS_REFRESH_INTERVAL = 300
    
    def __init__(
        self,
        base_url: str,
        token: str,
        station: Optional[Station] = None,
        timeout: int = 30,
        process_refresh_interval: int = DEFAULT_PROCESS_REFRESH_INTERVAL,
        error_mode: ErrorMode = ErrorMode.STRICT
    ):
        """
        Initialize the pyWATS API.
        
        Args:
            base_url: Base URL of the WATS server (e.g., "https://your-wats.com")
            token: API token (Base64-encoded credentials)
            station: Default station configuration for reports. If provided,
                     this station's name, location, and purpose will be used
                     when creating reports (unless overridden).
            timeout: Request timeout in seconds (default: 30)
            process_refresh_interval: Process cache refresh interval in seconds (default: 300)
            error_mode: Error handling mode (STRICT or LENIENT). Default is STRICT.
                - STRICT: Raises exceptions for 404/empty responses
                - LENIENT: Returns None for 404/empty responses
        """
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._process_refresh_interval = process_refresh_interval
        self._error_mode = error_mode
        self._error_handler = ErrorHandler(error_mode)
        
        # Station configuration
        self._station: Optional[Station] = station
        self._station_registry = StationRegistry()
        if station:
            self._station_registry.set_default(station)
        
        # Initialize HTTP client
        self._http_client = HttpClient(
            base_url=self._base_url,
            token=self._token,
            timeout=self._timeout
        )
        
        # Service instances (lazy initialization)
        self._product: Optional[ProductService] = None
        self._product_internal: Optional[ProductServiceInternal] = None
        self._asset: Optional[AssetService] = None
        self._asset_internal: Optional[AssetServiceInternal] = None
        self._production: Optional[ProductionService] = None
        self._production_internal: Optional[ProductionServiceInternal] = None
        self._report: Optional[ReportService] = None
        self._software: Optional[SoftwareService] = None
        self._analytics: Optional[AnalyticsService] = None
        self._rootcause: Optional[RootCauseService] = None
        self._process: Optional[ProcessService] = None
        self._process_internal: Optional[ProcessServiceInternal] = None
    
    # -------------------------------------------------------------------------
    # Module Properties
    # -------------------------------------------------------------------------
    
    @property
    def product(self) -> ProductService:
        """
        Access product management operations.
        
        Returns:
            ProductService instance
        """
        if self._product is None:
            repo = ProductRepository(self._http_client, self._error_handler)
            self._product = ProductService(repo)
        return self._product
    
    @property
    def product_internal(self) -> ProductServiceInternal:
        """
        Access internal product operations.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        This service uses internal WATS API endpoints that are not publicly
        documented. Methods may change or be removed without notice.
        
        Use this for:
        - Box build template management (subunit definitions)
        - BOM operations
        - Product categories
        
        Example:
            # Get a box build template
            with api.product_internal.get_box_build("MAIN-BOARD", "A") as bb:
                bb.add_subunit("PCBA-001", "A", quantity=2)
                bb.add_subunit("PSU-100", "B")
            # Changes saved automatically
        
        Returns:
            ProductServiceInternal instance
        """
        if self._product_internal is None:
            repo = ProductRepository(self._http_client)
            repo_internal = ProductRepositoryInternal(self._http_client, self._base_url)
            self._product_internal = ProductServiceInternal(repo, repo_internal)
        return self._product_internal
    
    @property
    def asset(self) -> AssetService:
        """
        Access asset management operations.
        
        Returns:
            AssetService instance
        """
        if self._asset is None:
            repo = AssetRepository(self._http_client, self._error_handler)
            self._asset = AssetService(repo)
        return self._asset
    
    @property
    def asset_internal(self) -> AssetServiceInternal:
        """
        Access internal asset operations (file operations).
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        This service uses internal WATS API endpoints that are not publicly
        documented. Methods may change or be removed without notice.
        
        Use this for:
        - Uploading files to assets
        - Downloading files from assets
        - Listing files attached to assets
        - Deleting files from assets
        
        Returns:
            AssetServiceInternal instance
        """
        if self._asset_internal is None:
            repo = AssetRepositoryInternal(self._http_client, self._base_url)
            self._asset_internal = AssetServiceInternal(repo)
        return self._asset_internal
    
    @property
    def production(self) -> ProductionService:
        """
        Access production/unit management operations.
        
        Includes sub-modules:
        - serial_number: Serial number operations
        - verification: Unit verification operations
        
        Unit phases are cached and accessible via:
        - get_phases(): Get all available phases
        - get_phase(id_or_name): Get a specific phase
        
        Returns:
            ProductionService instance
        """
        if self._production is None:
            repo = ProductionRepository(self._http_client, self._error_handler)
            self._production = ProductionService(repo, base_url=self._base_url)
        return self._production
    
    @property
    def production_internal(self) -> ProductionServiceInternal:
        """
        Access internal production operations (MES operations).
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        This service uses internal WATS API endpoints that are not publicly
        documented. Methods may change or be removed without notice.
        
        Use this for:
        - Getting unit phases from WATS MES
        - Getting detailed phase information
        
        Returns:
            ProductionServiceInternal instance
        """
        if self._production_internal is None:
            repo = ProductionRepositoryInternal(self._http_client, self._base_url)
            self._production_internal = ProductionServiceInternal(repo)
        return self._production_internal
    
    @property
    def report(self) -> ReportService:
        """
        Access report operations.
        
        Returns:
            ReportService instance
        """
        if self._report is None:
            repo = ReportRepository(self._http_client, self._error_handler)
            self._report = ReportService(repo, station_provider=self._get_station)
        return self._report
    
    @property
    def software(self) -> SoftwareService:
        """
        Access software distribution operations.
        
        Returns:
            SoftwareService instance
        """
        if self._software is None:
            repo = SoftwareRepository(self._http_client, self._error_handler)
            self._software = SoftwareService(repo)
        return self._software
    
    @property
    def analytics(self) -> AnalyticsService:
        """
        Access yield statistics, KPIs, and failure analysis.
        
        Provides high-level operations for:
        - Yield statistics (dynamic yield, volume yield, worst yield)
        - Failure analysis (top failed steps, test step analysis)
        - Production metrics (OEE, measurements)
        - Report queries (serial number history, UUT/UUR reports)
        
        Example:
            >>> # Get yield for a product
            >>> yield_data = api.analytics.get_dynamic_yield(
            ...     WATSFilter(part_number="WIDGET-001", period_count=30)
            ... )
            >>> # Get top failures
            >>> failures = api.analytics.get_top_failed(part_number="WIDGET-001")
        
        Returns:
            AnalyticsService instance
        """
        if self._analytics is None:
            repo = AnalyticsRepository(self._http_client, self._error_handler)
            self._analytics = AnalyticsService(repo)
        return self._analytics
    
    @property
    def rootcause(self) -> RootCauseService:
        """
        Access RootCause ticketing operations.
        
        The RootCause module provides a ticketing system for 
        collaboration on issue tracking and resolution.
        
        Returns:
            RootCauseService instance
        """
        if self._rootcause is None:
            repo = RootCauseRepository(self._http_client, self._error_handler)
            self._rootcause = RootCauseService(repo)
        return self._rootcause
    
    @property
    def process(self) -> ProcessService:
        """
        Access process/operation management (cached).
        
        Processes define the types of operations:
        - Test operations (e.g., End of line test, PCBA test)
        - Repair operations (e.g., Repair, RMA repair)
        - WIP operations (e.g., Assembly)
        
        The process list is cached in memory and refreshes at the configured
        interval (default: 5 minutes). Use api.process.refresh() to force refresh.
        
        Example:
            # Get by code
            test_op = api.process.get_test_operation(100)
            
            # Get by name
            repair_op = api.process.get_repair_operation("Repair")
            
            # Force refresh
            api.process.refresh()
        
        Returns:
            ProcessService instance
        """
        if self._process is None:
            repo = ProcessRepository(self._http_client, self._error_handler)
            self._process = ProcessService(repo, self._process_refresh_interval)
        return self._process
    
    @property
    def process_internal(self) -> ProcessServiceInternal:
        """
        Access internal process operations.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        This service uses internal WATS API endpoints that are not publicly
        documented. Methods may change or be removed without notice.
        
        Use this for:
        - Getting detailed process information with ProcessID
        - Getting repair categories and fail codes
        - Extended validation of process codes
        
        Returns:
            ProcessServiceInternal instance
        """
        if self._process_internal is None:
            repo = ProcessRepositoryInternal(self._http_client, self._base_url)
            self._process_internal = ProcessServiceInternal(repo)
        return self._process_internal
    
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    
    @property
    def base_url(self) -> str:
        """Get the configured base URL."""
        return self._base_url
    
    @property
    def timeout(self) -> int:
        """Get the configured request timeout."""
        return self._timeout
    
    @timeout.setter
    def timeout(self, value: int):
        """Set the request timeout."""
        self._timeout = value
        self._http_client.timeout = value
    
    @property
    def error_mode(self) -> ErrorMode:
        """Get the configured error handling mode."""
        return self._error_mode
    
    # -------------------------------------------------------------------------
    # Station Configuration
    # -------------------------------------------------------------------------
    
    @property
    def station(self) -> Optional[Station]:
        """
        Get the currently active station.
        
        Returns the active station from the registry, or the default station
        if no active station is set.
        
        Returns:
            Active Station or None
        """
        return self._station_registry.active or self._station
    
    @station.setter
    def station(self, station: Optional[Station]) -> None:
        """
        Set the default station.
        
        This station will be used for reports when no station is explicitly
        specified.
        
        Args:
            station: Station to set as default
        """
        self._station = station
        if station:
            self._station_registry.set_default(station)
    
    @property
    def stations(self) -> StationRegistry:
        """
        Access the station registry for multi-station support.
        
        Use this for scenarios where a single client handles reports
        from multiple stations (hub mode).
        
        Example:
            # Add stations
            api.stations.add("line-1", Station("PROD-LINE-1", "Building A", "Production"))
            api.stations.add("line-2", Station("PROD-LINE-2", "Building A", "Production"))
            
            # Set active station
            api.stations.set_active("line-1")
            
            # Get active station
            station = api.stations.active
        
        Returns:
            StationRegistry instance
        """
        return self._station_registry
    
    def _get_station(self) -> Optional[Station]:
        """
        Internal method to get the current station.
        
        Used by services that need station information.
        
        Returns:
            Current station or None
        """
        return self.station
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def test_connection(self) -> bool:
        """
        Test the connection to the WATS server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            version = self.analytics.get_version()
            return version is not None
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False
    
    def get_version(self) -> dict:
        """
        Get WATS server version information.
        
        Returns:
            Version information dictionary
        """
        return self.analytics.get_version()
    
    def __repr__(self) -> str:
        """String representation of the pyWATS instance."""
        return f"pyWATS(base_url='{self._base_url}')"
