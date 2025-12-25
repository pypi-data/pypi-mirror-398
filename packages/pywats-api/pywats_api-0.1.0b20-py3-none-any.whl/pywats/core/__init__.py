"""Core infrastructure for pyWATS.

Contains HTTP client, authentication, error handling, and base exceptions.
"""
from .client import HttpClient, Response
from .config import (
    APISettings,
    APIConfigManager,
    DomainSettings,
    ProductDomainSettings,
    ReportDomainSettings,
    ProductionDomainSettings,
    ProcessDomainSettings,
    SoftwareDomainSettings,
    AssetDomainSettings,
    RootCauseDomainSettings,
    AppDomainSettings,
    get_api_settings,
    get_api_config_manager,
)
from .exceptions import (
    # Error handling
    ErrorMode,
    ErrorHandler,
    # Exceptions
    PyWATSError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConflictError,
    EmptyResponseError,
    ConnectionError,
    TimeoutError,
)
from .station import (
    Station,
    StationConfig,
    StationRegistry,
    Purpose,
    get_default_station,
)
from .throttle import (
    RateLimiter,
    configure_throttling,
    get_default_limiter,
)

__all__ = [
    # Client
    "HttpClient",
    "Response",
    # Config
    "APISettings",
    "APIConfigManager",
    "DomainSettings",
    "ProductDomainSettings",
    "ReportDomainSettings",
    "ProductionDomainSettings",
    "ProcessDomainSettings",
    "SoftwareDomainSettings",
    "AssetDomainSettings",
    "RootCauseDomainSettings",
    "AppDomainSettings",
    "get_api_settings",
    "get_api_config_manager",
    # Station
    "Station",
    "StationConfig",
    "StationRegistry",
    "Purpose",
    "get_default_station",
    # Rate limiting
    "RateLimiter",
    "configure_throttling",
    "get_default_limiter",
    # Error handling
    "ErrorMode",
    "ErrorHandler",
    # Exceptions
    "PyWATSError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "ConflictError",
    "EmptyResponseError",
    "ConnectionError",
    "TimeoutError",
]
