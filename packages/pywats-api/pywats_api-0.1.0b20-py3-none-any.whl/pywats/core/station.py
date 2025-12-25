"""
Station Configuration

Provides a unified concept for test station identity that can be used
throughout the pyWATS API and client.

A Station represents the test station identity that appears in reports:
- name: The station/machine name (serialized as 'machineName' in WATS)
- location: Physical or logical location of the station
- purpose: Testing purpose (Production, Debug, Development, etc.)

This module also provides StationRegistry for managing multiple stations
from a single client (hub mode).
"""

import socket
from typing import Dict, Optional, Any, Iterator, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Common purpose values used in WATS
class Purpose:
    """Common station purpose values."""
    PRODUCTION = "Production"
    DEBUG = "Debug"
    DEVELOPMENT = "Development"
    REPAIR = "Repair"
    QUALIFICATION = "Qualification"
    CALIBRATION = "Calibration"
    ENGINEERING = "Engineering"
    RMA = "RMA"


class Station(BaseModel):
    """
    Represents a test station identity.
    
    A Station encapsulates the identity information that appears in test reports:
    - name: The station/machine name (appears as 'machineName' in reports)
    - location: Physical or logical location
    - purpose: Testing purpose (Production, Debug, Development, etc.)
    
    Usage:
        # Create a station with defaults
        station = Station.from_hostname()
        
        # Create a custom station
        station = Station(
            name="TEST-STATION-01",
            location="Building A, Floor 2",
            purpose="Production"
        )
        
        # Use with report creation
        report = api.report.create_uut_report(
            operator="John",
            part_number="PN-001",
            ...,
            station=station
        )
    
    Attributes:
        name: Station name (appears as machineName in WATS reports).
              Should be unique within an organization.
        location: Physical or logical location description.
                  Helps identify where units are tested.
        purpose: Testing purpose. Common values: Production, Debug, 
                 Development, Repair, Qualification, Calibration.
        description: Optional detailed description of the station.
    """
    model_config = ConfigDict(validate_assignment=True)
    
    name: str = Field(..., description="Station name (appears as machineName in WATS reports)")
    location: str = Field(default="", description="Physical or logical location")
    purpose: str = Field(default=Purpose.DEVELOPMENT, description="Testing purpose")
    description: str = Field(default="", description="Optional station description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate station name is not empty and normalize it."""
        if not v or not v.strip():
            raise ValueError("Station name cannot be empty")
        return v.strip()
    
    @classmethod
    def from_hostname(
        cls, 
        location: str = "", 
        purpose: str = Purpose.DEVELOPMENT,
        description: str = ""
    ) -> "Station":
        """
        Create station using computer hostname as name.
        
        This is the most common pattern for test stations where
        the computer name matches the station identity.
        
        Args:
            location: Station location
            purpose: Testing purpose
            description: Optional description
            
        Returns:
            Station with hostname as name
        """
        hostname = socket.gethostname().upper()
        return cls(
            name=hostname,
            location=location,
            purpose=purpose,
            description=description
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Station":
        """
        Create station from configuration dictionary.
        
        Args:
            data: Dictionary with station fields
            
        Returns:
            Station instance
        """
        return cls(
            name=data.get("name", ""),
            location=data.get("location", ""),
            purpose=data.get("purpose", Purpose.DEVELOPMENT),
            description=data.get("description", "")
        )
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary with station fields
        """
        return self.model_dump()
    
    def copy(self, **kwargs) -> "Station":
        """
        Create a copy of this station with optional overrides.
        
        Args:
            **kwargs: Fields to override
            
        Returns:
            New Station instance
        """
        return self.model_copy(update=kwargs)
    
    def __str__(self) -> str:
        """String representation."""
        parts = [self.name]
        if self.location:
            parts.append(f"@ {self.location}")
        if self.purpose:
            parts.append(f"({self.purpose})")
        return " ".join(parts)


class StationConfig(BaseModel):
    """
    Configuration for a saved station preset.
    
    Used to persist station configurations in client settings.
    
    Attributes:
        key: Unique identifier within registry
        name: Station name (machineName)
        location: Location string
        purpose: Purpose string
        description: Optional description
        is_default: Is this the default station?
    """
    key: str = Field(..., description="Unique identifier within registry")
    name: str = Field(..., description="Station name (machineName)")
    location: str = Field(default="", description="Location string")
    purpose: str = Field(default=Purpose.DEVELOPMENT, description="Purpose string")
    description: str = Field(default="", description="Optional description")
    is_default: bool = Field(default=False, description="Is this the default station?")
    
    def to_station(self) -> Station:
        """Convert to Station instance."""
        return Station(
            name=self.name,
            location=self.location,
            purpose=self.purpose,
            description=self.description
        )
    
    @classmethod
    def from_station(cls, key: str, station: Station, is_default: bool = False) -> "StationConfig":
        """Create from Station instance."""
        return cls(
            key=key,
            name=station.name,
            location=station.location,
            purpose=station.purpose,
            description=station.description,
            is_default=is_default
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StationConfig":
        """Create from dictionary."""
        return cls.model_validate(data)


class StationRegistry:
    """
    Manages multiple station configurations.
    
    Enables a single client to act as a hub for multiple stations:
    - Database converters that import data from multiple test systems
    - Centralized upload clients that receive reports from various stations
    - Test cells with multiple fixtures/positions
    
    Usage:
        registry = StationRegistry()
        
        # Add stations
        registry.add("station-a", Station("STATION-A", "Lab 1", "Production"))
        registry.add("station-b", Station("STATION-B", "Lab 2", "Debug"))
        
        # Set active station
        registry.set_active("station-a")
        
        # Get active station
        station = registry.active
        
        # Iterate over all stations
        for key, station in registry.items():
            print(f"{key}: {station}")
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._stations: Dict[str, Station] = {}
        self._active_key: Optional[str] = None
        self._default: Optional[Station] = None
        self._default_key: Optional[str] = None
    
    def add(self, key: str, station: Station, set_active: bool = False) -> None:
        """
        Add a station to the registry.
        
        Args:
            key: Unique identifier for this station
            station: Station instance to add
            set_active: Whether to set this as active station
        """
        if not key or not key.strip():
            raise ValueError("Station key cannot be empty")
        
        key = key.strip().lower()
        self._stations[key] = station
        
        # Set as active if first station or explicitly requested
        if set_active or self._active_key is None:
            self._active_key = key
    
    def remove(self, key: str) -> Optional[Station]:
        """
        Remove a station from the registry.
        
        Args:
            key: Key of station to remove
            
        Returns:
            The removed station, or None if not found
        """
        key = key.strip().lower()
        station = self._stations.pop(key, None)
        
        if station and self._active_key == key:
            # Set a new active station
            self._active_key = next(iter(self._stations), None)
        
        if self._default_key == key:
            self._default_key = None
            self._default = None
        
        return station
    
    def get(self, key: str) -> Optional[Station]:
        """
        Get a station by key.
        
        Args:
            key: Station key
            
        Returns:
            Station if found, None otherwise
        """
        return self._stations.get(key.strip().lower())
    
    def has(self, key: str) -> bool:
        """Check if a station exists in the registry."""
        return key.strip().lower() in self._stations
    
    def set_active(self, key: str) -> None:
        """
        Set the active station.
        
        Args:
            key: Key of station to make active
            
        Raises:
            ValueError: If station not found
        """
        key = key.strip().lower()
        if key not in self._stations:
            raise ValueError(f"Station '{key}' not found in registry")
        self._active_key = key
    
    def set_default(self, station: Station, key: Optional[str] = None) -> None:
        """
        Set the default station.
        
        The default station is used when no active station is set
        or when the registry is empty.
        
        Args:
            station: Default station
            key: Optional key to also add to registry
        """
        self._default = station
        if key:
            key = key.strip().lower()
            self._default_key = key
            self._stations[key] = station
    
    @property
    def active(self) -> Optional[Station]:
        """
        Get the currently active station.
        
        Returns:
            Active station, or default if no active, or None
        """
        if self._active_key and self._active_key in self._stations:
            return self._stations[self._active_key]
        return self._default
    
    @property
    def active_key(self) -> Optional[str]:
        """Get the key of the active station."""
        return self._active_key
    
    @property
    def default(self) -> Optional[Station]:
        """Get the default station."""
        return self._default
    
    @property
    def keys(self) -> List[str]:
        """Get all station keys."""
        return list(self._stations.keys())
    
    def items(self) -> Iterator[tuple]:
        """Iterate over (key, station) pairs."""
        return iter(self._stations.items())
    
    def values(self) -> Iterator[Station]:
        """Iterate over stations."""
        return iter(self._stations.values())
    
    def clear(self) -> None:
        """Remove all stations from registry."""
        self._stations.clear()
        self._active_key = None
    
    def to_list(self) -> List[StationConfig]:
        """
        Convert to list of StationConfig for serialization.
        
        Returns:
            List of StationConfig objects
        """
        configs = []
        for key, station in self._stations.items():
            config = StationConfig.from_station(
                key=key,
                station=station,
                is_default=(key == self._default_key)
            )
            configs.append(config)
        return configs
    
    @classmethod
    def from_list(cls, configs: List[Dict[str, Any]]) -> "StationRegistry":
        """
        Create registry from list of config dictionaries.
        
        Args:
            configs: List of station config dictionaries
            
        Returns:
            Populated StationRegistry
        """
        registry = cls()
        default_key = None
        
        for config_dict in configs:
            config = StationConfig.from_dict(config_dict)
            station = config.to_station()
            registry.add(config.key, station)
            
            if config.is_default:
                default_key = config.key
        
        if default_key:
            registry.set_active(default_key)
        
        return registry
    
    def __len__(self) -> int:
        """Number of stations in registry."""
        return len(self._stations)
    
    def __iter__(self) -> Iterator[Station]:
        """Iterate over stations."""
        return iter(self._stations.values())
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in registry."""
        return self.has(key)
    
    def __bool__(self) -> bool:
        """True if registry has any stations."""
        return len(self._stations) > 0 or self._default is not None


def get_default_station() -> Station:
    """
    Get a sensible default station.
    
    Uses the computer hostname as the station name with default values.
    
    Returns:
        Default Station instance
    """
    return Station.from_hostname(
        location="",
        purpose=Purpose.DEVELOPMENT
    )
