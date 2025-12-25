"""
Logging utilities for pyWATS.

The library uses Python's standard logging module but never configures
handlers or output. This allows applications to control logging behavior.

Usage in library code:
    >>> from pywats.core.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.debug("Debug message")
    >>> logger.info("Info message")

Usage for quick debugging:
    >>> from pywats import enable_debug_logging
    >>> enable_debug_logging()
"""

import logging
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given name.
    
    All pyWATS loggers are children of 'pywats' root logger,
    allowing users to control library logging with:
    
        >>> import logging
        >>> logging.getLogger('pywats').setLevel(logging.WARNING)
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def enable_debug_logging(format_string: Optional[str] = None) -> None:
    """
    Convenience function to enable debug logging for pyWATS.
    
    This is a helper for quick debugging but applications should
    configure logging properly for production use.
    
    Args:
        format_string: Custom format string for log messages.
                      Defaults to: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    Example:
        >>> from pywats import enable_debug_logging
        >>> enable_debug_logging()
        >>> # Now all pyWATS debug messages will be visible
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.DEBUG,
        format=format_string
    )
    logging.getLogger('pywats').setLevel(logging.DEBUG)


# Suppress warnings about unconfigured logging
# This prevents "No handlers found" warnings when the library is used
# without explicit logging configuration
logging.getLogger('pywats').addHandler(logging.NullHandler())
