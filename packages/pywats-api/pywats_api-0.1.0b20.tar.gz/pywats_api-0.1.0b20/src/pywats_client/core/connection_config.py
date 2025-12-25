"""
Connection state and configuration management.

Handles persistent connection state, authentication, and token management.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state for persistent tracking"""
    NOT_CONNECTED = "Not Connected"  # No credentials stored
    CONNECTED = "Connected"  # Authenticated and online
    OFFLINE = "Offline"  # Authenticated but server unreachable


@dataclass
class ConnectionConfig:
    """
    Connection-specific configuration with persistent state.
    
    This stores connection credentials and state that persists
    across application restarts.
    """
    # Server details
    server_url: str = ""
    username: str = ""
    
    # Token storage (encrypted)
    token_encrypted: str = ""  # Encrypted API token
    token_version: int = 1  # For future token format changes
    
    # Connection state
    connection_state: str = "Not Connected"  # Stored as string for JSON
    last_connected: Optional[str] = None  # ISO format datetime string
    last_disconnected: Optional[str] = None
    
    # Health monitoring settings
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 10  # seconds
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 0  # 0 = unlimited
    reconnect_delay: int = 10  # seconds between reconnect attempts
    
    # Statistics
    total_connections: int = 0
    total_disconnections: int = 0
    total_health_checks: int = 0
    failed_health_checks: int = 0
    
    def get_state(self) -> ConnectionState:
        """Get connection state as enum"""
        try:
            return ConnectionState(self.connection_state)
        except ValueError:
            return ConnectionState.NOT_CONNECTED
    
    def set_state(self, state: ConnectionState) -> None:
        """Set connection state from enum"""
        self.connection_state = state.value
    
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials"""
        return bool(self.token_encrypted and self.server_url)
    
    def is_connected(self) -> bool:
        """Check if in connected state"""
        return self.get_state() == ConnectionState.CONNECTED
    
    def is_offline(self) -> bool:
        """Check if in offline state (authenticated but unreachable)"""
        return self.get_state() == ConnectionState.OFFLINE
    
    def mark_connected(self) -> None:
        """Mark as connected and update statistics"""
        self.set_state(ConnectionState.CONNECTED)
        self.last_connected = datetime.now().isoformat()
        self.total_connections += 1
    
    def mark_disconnected(self) -> None:
        """Mark as disconnected and update statistics"""
        self.set_state(ConnectionState.NOT_CONNECTED)
        self.last_disconnected = datetime.now().isoformat()
        self.total_disconnections += 1
        # Clear credentials on disconnect
        self.token_encrypted = ""
        self.username = ""
    
    def mark_offline(self) -> None:
        """Mark as offline (credentials retained)"""
        self.set_state(ConnectionState.OFFLINE)
    
    def record_health_check(self, success: bool) -> None:
        """Record health check result"""
        self.total_health_checks += 1
        if not success:
            self.failed_health_checks += 1
    
    def get_health_check_success_rate(self) -> float:
        """Get health check success rate as percentage"""
        if self.total_health_checks == 0:
            return 100.0
        success = self.total_health_checks - self.failed_health_checks
        return (success / self.total_health_checks) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionConfig":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class InstanceConfig:
    """
    Instance-specific configuration.
    
    Each pyWATS Client instance (station) has its own configuration,
    allowing multiple instances on the same machine.
    """
    # Instance identification
    instance_id: str
    instance_name: str
    instance_type: str = "configurator"  # "configurator", "yield_monitor"
    
    # Storage location
    storage_path: str = ""  # Absolute path to instance data
    
    # Connection configuration
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    
    # Instance metadata
    created_at: Optional[str] = None  # ISO format datetime
    last_used: Optional[str] = None
    
    def __post_init__(self):
        """Ensure connection is proper object"""
        if isinstance(self.connection, dict):
            self.connection = ConnectionConfig.from_dict(self.connection)
        
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def mark_used(self) -> None:
        """Update last used timestamp"""
        self.last_used = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "instance_id": self.instance_id,
            "instance_name": self.instance_name,
            "instance_type": self.instance_type,
            "storage_path": self.storage_path,
            "connection": self.connection.to_dict(),
            "created_at": self.created_at,
            "last_used": self.last_used,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstanceConfig":
        """Create from dictionary"""
        return cls(**data)


def migrate_legacy_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate legacy configuration to new format with connection state.
    
    Args:
        config_dict: Old configuration dictionary
    
    Returns:
        Updated configuration dictionary with connection field
    """
    from .encryption import migrate_plain_token
    
    # Check if already migrated
    if "connection" in config_dict:
        return config_dict
    
    logger.info("Migrating legacy configuration to new format")
    
    # Extract legacy fields
    server_url = config_dict.get("service_address", "")
    plain_token = config_dict.get("api_token", "")
    username = config_dict.get("username", "")
    was_connected = config_dict.get("was_connected", False)
    
    # Create connection config
    connection = ConnectionConfig(
        server_url=server_url,
        username=username,
        token_encrypted=migrate_plain_token(plain_token) if plain_token else "",
        connection_state="Connected" if (plain_token and was_connected) else "Not Connected"
    )
    
    # Add connection to config
    config_dict["connection"] = connection.to_dict()
    
    # Keep legacy fields for backward compatibility
    # but they will be synced with connection config
    
    return config_dict
