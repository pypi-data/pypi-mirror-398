"""
Analysis context with sticky filter memory.

Maintains conversational context across tool calls:
- Filter parameters persist until attention shifts
- Confidence decays over time or topic change
- Implicit filter inheritance without explicit specification

Usage:
    context = AnalysisContext.get_instance()
    
    # First call - user specifies product
    context.update_filter(part_number="WIDGET-001", test_operation="FCT")
    
    # Subsequent calls inherit context
    filter = context.get_effective_filter()  # Has WIDGET-001 and FCT
    
    # User shifts to different topic - context fades
    context.shift_topic(part_number="OTHER-PRODUCT")  # Clears old context
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from pywats import pyWATS


class ContextConfidence(str, Enum):
    """Confidence level in the current context."""
    HIGH = "high"           # Recently set, same topic
    MEDIUM = "medium"       # Set a few turns ago
    LOW = "low"             # Getting stale, may prompt user
    EXPIRED = "expired"     # Too old, should be cleared


class FilterMemory(BaseModel):
    """
    Remembered filter parameters with timestamps.
    
    Tracks when each filter field was last set to determine staleness.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Filter values
    part_number: Optional[str] = None
    revision: Optional[str] = None
    station_name: Optional[str] = None
    product_group: Optional[str] = None
    level: Optional[str] = None
    test_operation: Optional[str] = None
    batch_number: Optional[str] = None
    
    # Time context
    days: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    period_count: Optional[int] = None
    date_grouping: Optional[str] = None
    
    # Timestamps for each field (when it was last set)
    _field_timestamps: Dict[str, datetime] = {}
    
    def update(self, **kwargs) -> "FilterMemory":
        """
        Update filter fields and track timestamps.
        
        Only updates fields that are explicitly provided (not None).
        """
        now = datetime.now()
        updated_fields = {}
        
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                updated_fields[key] = value
                self._field_timestamps[key] = now
        
        return self.model_copy(update=updated_fields)
    
    def get_age(self, field: str) -> Optional[timedelta]:
        """Get the age of a specific field."""
        if field in self._field_timestamps:
            return datetime.now() - self._field_timestamps[field]
        return None
    
    def clear_stale_fields(self, max_age: timedelta = timedelta(minutes=5)) -> "FilterMemory":
        """Clear fields that are older than max_age."""
        now = datetime.now()
        cleared = {}
        
        for field, timestamp in list(self._field_timestamps.items()):
            if now - timestamp > max_age:
                cleared[field] = None
                del self._field_timestamps[field]
        
        if cleared:
            return self.model_copy(update=cleared)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with only non-None values."""
        result = {}
        for field in ['part_number', 'revision', 'station_name', 'product_group',
                      'level', 'test_operation', 'batch_number', 'days',
                      'date_from', 'date_to', 'period_count', 'date_grouping']:
            value = getattr(self, field, None)
            if value is not None:
                result[field] = value
        return result
    
    def has_product_context(self) -> bool:
        """Check if we have product-related context."""
        return bool(self.part_number or self.product_group or self.revision)
    
    def has_process_context(self) -> bool:
        """Check if we have process-related context."""
        return bool(self.test_operation)
    
    def has_location_context(self) -> bool:
        """Check if we have location-related context."""
        return bool(self.station_name or self.level)
    
    def describe(self) -> str:
        """Human-readable description of current context."""
        parts = []
        if self.part_number:
            parts.append(f"product {self.part_number}")
        if self.revision:
            parts.append(f"rev {self.revision}")
        if self.test_operation:
            parts.append(f"process {self.test_operation}")
        if self.station_name:
            parts.append(f"station {self.station_name}")
        if self.product_group:
            parts.append(f"group {self.product_group}")
        if self.batch_number:
            parts.append(f"batch {self.batch_number}")
        
        if not parts:
            return "no filter context"
        return ", ".join(parts)


class AnalysisContext:
    """
    Singleton context manager for analysis tools.
    
    Maintains sticky filter memory across tool calls:
    - Filters persist until explicitly changed or topic shifts
    - Confidence decays over time
    - Provides effective filter by merging memory with explicit params
    
    Thread Safety:
        This is a simple singleton - for multi-tenant use, implement
        per-session context keyed by session_id.
    """
    
    _instance: Optional["AnalysisContext"] = None
    
    def __init__(self):
        self._filter_memory = FilterMemory()
        self._last_interaction = datetime.now()
        self._interaction_count = 0
        self._topic_signature: Optional[str] = None
        
    @classmethod
    def get_instance(cls) -> "AnalysisContext":
        """Get the singleton context instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the context (for testing)."""
        cls._instance = None
    
    @property
    def filter(self) -> FilterMemory:
        """Get the current filter memory."""
        return self._filter_memory
    
    @property
    def confidence(self) -> ContextConfidence:
        """Get confidence level based on age and interactions."""
        age = datetime.now() - self._last_interaction
        
        if age < timedelta(seconds=30):
            return ContextConfidence.HIGH
        elif age < timedelta(minutes=2):
            return ContextConfidence.MEDIUM
        elif age < timedelta(minutes=5):
            return ContextConfidence.LOW
        else:
            return ContextConfidence.EXPIRED
    
    def _compute_topic_signature(self, **kwargs) -> str:
        """Compute a signature for the current topic (for shift detection)."""
        # Topic is defined by product + process combination
        parts = []
        if kwargs.get('part_number'):
            parts.append(f"pn:{kwargs['part_number']}")
        if kwargs.get('product_group'):
            parts.append(f"pg:{kwargs['product_group']}")
        if kwargs.get('test_operation'):
            parts.append(f"op:{kwargs['test_operation']}")
        return "|".join(sorted(parts)) if parts else ""
    
    def _detect_topic_shift(self, **kwargs) -> bool:
        """Detect if the user is shifting to a different topic."""
        new_signature = self._compute_topic_signature(**kwargs)
        
        # No new topic info - not a shift
        if not new_signature:
            return False
        
        # No previous topic - not a shift (just setting context)
        if not self._topic_signature:
            return False
        
        # Different signature = topic shift
        return new_signature != self._topic_signature
    
    def update_filter(
        self,
        clear_on_shift: bool = True,
        **kwargs
    ) -> FilterMemory:
        """
        Update the filter memory with new values.
        
        Args:
            clear_on_shift: If True, clear previous context on topic shift
            **kwargs: Filter parameters to update
            
        Returns:
            Updated FilterMemory
            
        Topic Shift Detection:
            When the user specifies a DIFFERENT product or process than before,
            this is considered a topic shift. The old context is cleared to
            prevent filter bleeding between topics.
        """
        self._last_interaction = datetime.now()
        self._interaction_count += 1
        
        # Check for topic shift
        if clear_on_shift and self._detect_topic_shift(**kwargs):
            # Clear old context on topic shift
            self._filter_memory = FilterMemory()
        
        # Update with new values
        self._filter_memory = self._filter_memory.update(**kwargs)
        
        # Update topic signature
        new_sig = self._compute_topic_signature(**kwargs)
        if new_sig:
            self._topic_signature = new_sig
        
        return self._filter_memory
    
    def get_effective_filter(
        self,
        explicit_params: Optional[Dict[str, Any]] = None,
        require_confirmation_if_stale: bool = False
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Get effective filter by merging memory with explicit params.
        
        Args:
            explicit_params: Explicitly provided parameters (take precedence)
            require_confirmation_if_stale: If True, return prompt when confidence is LOW
            
        Returns:
            Tuple of (effective_filter_dict, optional_confirmation_prompt)
            
        Merge Logic:
            1. Start with filter memory
            2. Override with explicit params (if provided)
            3. Clear stale fields if confidence is LOW
        """
        # Start with memory
        effective = self._filter_memory.to_dict()
        
        # Handle stale context
        if self.confidence == ContextConfidence.EXPIRED:
            self._filter_memory = FilterMemory()
            effective = {}
        elif self.confidence == ContextConfidence.LOW:
            # Clear stale fields
            self._filter_memory = self._filter_memory.clear_stale_fields()
            effective = self._filter_memory.to_dict()
        
        # Merge explicit params (they take precedence)
        if explicit_params:
            for key, value in explicit_params.items():
                if value is not None:
                    effective[key] = value
                    # Also update memory with explicit values
                    self.update_filter(clear_on_shift=False, **{key: value})
        
        # Check if we should prompt for confirmation
        prompt = None
        if require_confirmation_if_stale and self.confidence == ContextConfidence.LOW:
            if effective:
                prompt = (
                    f"Still analyzing {self._filter_memory.describe()}? "
                    f"(Last interaction was {int((datetime.now() - self._last_interaction).seconds / 60)} minutes ago)"
                )
        
        return effective, prompt
    
    def shift_topic(self, **new_context) -> FilterMemory:
        """
        Explicitly shift to a new topic, clearing previous context.
        
        Use this when the user clearly indicates they're moving to
        a different subject.
        """
        self._filter_memory = FilterMemory()
        self._topic_signature = None
        return self.update_filter(**new_context)
    
    def clear(self) -> None:
        """Clear all context."""
        self._filter_memory = FilterMemory()
        self._topic_signature = None
        self._last_interaction = datetime.now()
        self._interaction_count = 0
    
    def describe_context(self) -> str:
        """Get a human-readable description of current context."""
        if self.confidence == ContextConfidence.EXPIRED:
            return "No active context (session expired)"
        
        confidence_desc = {
            ContextConfidence.HIGH: "Active",
            ContextConfidence.MEDIUM: "Recent", 
            ContextConfidence.LOW: "Stale",
        }
        
        filter_desc = self._filter_memory.describe()
        return f"{confidence_desc[self.confidence]} context: {filter_desc}"


# Convenience function for tools
def get_context() -> AnalysisContext:
    """Get the shared analysis context."""
    return AnalysisContext.get_instance()
