"""
Request throttling for WATS API.

Implements a sliding window rate limiter to comply with WATS API limits.
Default limit: 500 requests per minute.
"""
import time
import threading
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe sliding window rate limiter.
    
    Limits the number of requests within a rolling time window.
    When the limit is reached, requests are delayed until capacity is available.
    
    Attributes:
        max_requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        
    Example:
        >>> limiter = RateLimiter(max_requests=500, window_seconds=60)
        >>> limiter.acquire()  # Blocks if rate limit exceeded
        >>> # Make your API call here
    """
    
    def __init__(
        self,
        max_requests: int = 500,
        window_seconds: float = 60.0,
        enabled: bool = True
    ):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window (default: 500)
            window_seconds: Size of the sliding window in seconds (default: 60)
            enabled: Whether throttling is enabled (default: True)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        
        # Thread-safe deque to store request timestamps
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
        
        # Statistics
        self._total_requests = 0
        self._total_wait_time = 0.0
        self._throttle_count = 0
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request.
        
        Blocks until a request slot is available or timeout is reached.
        
        Args:
            timeout: Maximum time to wait in seconds. None means wait indefinitely.
            
        Returns:
            True if permission was acquired, False if timeout occurred.
            
        Example:
            >>> if limiter.acquire(timeout=5.0):
            ...     # Make API call
            ... else:
            ...     print("Timed out waiting for rate limit")
        """
        if not self.enabled:
            return True
            
        start_wait = time.monotonic()
        deadline = start_wait + timeout if timeout is not None else None
        
        while True:
            with self._lock:
                now = time.monotonic()
                
                # Remove timestamps outside the window
                cutoff = now - self.window_seconds
                while self._timestamps and self._timestamps[0] < cutoff:
                    self._timestamps.popleft()
                
                # Check if we're under the limit
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    self._total_requests += 1
                    
                    wait_time = now - start_wait
                    if wait_time > 0.001:  # Only log if we actually waited
                        self._total_wait_time += wait_time
                        logger.debug(
                            f"Rate limiter: acquired after {wait_time:.3f}s wait "
                            f"({len(self._timestamps)}/{self.max_requests} slots used)"
                        )
                    return True
                
                # Calculate how long until the oldest request expires
                if self._timestamps:
                    sleep_time = self._timestamps[0] + self.window_seconds - now
                else:
                    sleep_time = 0.01  # Small sleep if deque is somehow empty
                
                # Check timeout
                if deadline is not None and now + sleep_time > deadline:
                    logger.warning(
                        f"Rate limiter: timeout waiting for slot "
                        f"({len(self._timestamps)}/{self.max_requests} slots used)"
                    )
                    return False
            
            # Sleep outside the lock
            if sleep_time > 0:
                self._throttle_count += 1
                logger.info(
                    f"Rate limit reached ({self.max_requests} requests/{self.window_seconds}s). "
                    f"Waiting {sleep_time:.2f}s..."
                )
                time.sleep(min(sleep_time, 1.0))  # Sleep max 1 second at a time
    
    def reset(self) -> None:
        """Reset the rate limiter, clearing all tracked requests."""
        with self._lock:
            self._timestamps.clear()
            logger.debug("Rate limiter reset")
    
    @property
    def current_usage(self) -> int:
        """Get the current number of requests in the window."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            # Count timestamps within the window
            return sum(1 for ts in self._timestamps if ts >= cutoff)
    
    @property
    def available_slots(self) -> int:
        """Get the number of available request slots."""
        return max(0, self.max_requests - self.current_usage)
    
    @property
    def stats(self) -> dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with total_requests, total_wait_time, throttle_count,
            current_usage, and available_slots.
        """
        return {
            "total_requests": self._total_requests,
            "total_wait_time_seconds": round(self._total_wait_time, 3),
            "throttle_count": self._throttle_count,
            "current_usage": self.current_usage,
            "available_slots": self.available_slots,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "enabled": self.enabled,
        }
    
    def __repr__(self) -> str:
        return (
            f"RateLimiter(max_requests={self.max_requests}, "
            f"window_seconds={self.window_seconds}, "
            f"enabled={self.enabled}, "
            f"current_usage={self.current_usage})"
        )


# Global default rate limiter for WATS API (500 requests/minute)
_default_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_default_limiter() -> RateLimiter:
    """
    Get the default global rate limiter.
    
    Creates the limiter on first access (lazy initialization).
    """
    global _default_limiter
    if _default_limiter is None:
        with _limiter_lock:
            if _default_limiter is None:
                _default_limiter = RateLimiter(
                    max_requests=500,
                    window_seconds=60.0,
                    enabled=True
                )
    return _default_limiter


def configure_throttling(
    max_requests: int = 500,
    window_seconds: float = 60.0,
    enabled: bool = True
) -> RateLimiter:
    """
    Configure the global rate limiter.
    
    Call this before creating any pyWATS instances to customize throttling.
    
    Args:
        max_requests: Maximum requests per window (default: 500)
        window_seconds: Window size in seconds (default: 60)
        enabled: Whether throttling is enabled (default: True)
        
    Returns:
        The configured RateLimiter instance
        
    Example:
        >>> from pywats.core.throttle import configure_throttling
        >>> # Disable throttling for testing
        >>> configure_throttling(enabled=False)
        >>> # Or set a custom limit
        >>> configure_throttling(max_requests=100, window_seconds=60)
    """
    global _default_limiter
    with _limiter_lock:
        _default_limiter = RateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
            enabled=enabled
        )
        logger.info(
            f"Throttling configured: {max_requests} requests per {window_seconds}s "
            f"(enabled={enabled})"
        )
        return _default_limiter
