"""
HTTP Client for WATS API.

This module provides a clean HTTP client with Basic authentication
for communicating with the WATS server.

Note: The HttpClient does NOT raise exceptions for HTTP error status codes.
It always returns a Response object. Error handling is delegated to the
ErrorHandler class in the repository layer.

Rate Limiting:
    The client includes built-in rate limiting to comply with WATS API limits
    (500 requests per minute by default). Throttling can be configured via:
    
    >>> from pywats.core.throttle import configure_throttling
    >>> configure_throttling(max_requests=500, window_seconds=60, enabled=True)
"""
from typing import Optional, Dict, Any, Iterator
from contextlib import contextmanager
import time
from pydantic import BaseModel, Field, ConfigDict, computed_field
import httpx
import json

from .exceptions import (
    ConnectionError,
    TimeoutError,
    PyWATSError
)
from .throttle import RateLimiter, get_default_limiter


class Response(BaseModel):
    """HTTP Response wrapper.
    
    Attributes:
        status_code: HTTP status code (200, 404, 500, etc.)
        data: Parsed response data (dict, list, or primitive)
        headers: Response headers as dict
        raw: Raw response bytes
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    status_code: int = Field(..., description="HTTP status code")
    data: Any = Field(default=None, description="Parsed response data")
    headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    raw: bytes = Field(default=b"", description="Raw response bytes")

    @computed_field
    @property
    def is_success(self) -> bool:
        """True if status code is 2xx."""
        return 200 <= self.status_code < 300

    @computed_field
    @property
    def is_error(self) -> bool:
        """True if status code is 4xx or 5xx."""
        return self.status_code >= 400
    
    @computed_field
    @property
    def is_not_found(self) -> bool:
        """True if status code is 404."""
        return self.status_code == 404
    
    @computed_field
    @property
    def is_server_error(self) -> bool:
        """True if status code is 5xx."""
        return 500 <= self.status_code < 600
    
    @computed_field
    @property
    def is_client_error(self) -> bool:
        """True if status code is 4xx."""
        return 400 <= self.status_code < 500
    
    @property
    def error_message(self) -> Optional[str]:
        """Extract error message from response data if available."""
        if self.is_success:
            return None
        
        if isinstance(self.data, dict):
            return (
                self.data.get("message") or 
                self.data.get("Message") or
                self.data.get("error") or 
                self.data.get("detail") or
                self.data.get("title")
            )
        elif isinstance(self.data, str):
            return self.data
        
        return f"HTTP {self.status_code}"


class HttpClient:
    """
    HTTP client with Basic authentication for WATS API.

    This client handles all HTTP communication with the WATS server,
    including authentication, request/response handling, and error management.
    
    Rate limiting is enabled by default to comply with WATS API limits
    (500 requests per minute). This can be disabled or customized.
    
    Example:
        >>> client = HttpClient(base_url="https://wats.example.com", token="...")
        >>> response = client.get("/api/Product/ABC123")
        >>> print(client.rate_limiter.stats)  # Check throttling statistics
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
        enable_throttling: bool = True
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL of the WATS server
            token: Base64 encoded authentication token for Basic auth
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
            rate_limiter: Custom RateLimiter instance (default: global limiter)
            enable_throttling: Enable/disable rate limiting (default: True)
        """
        # Clean up base URL - remove trailing slashes and /api suffixes
        self.base_url = base_url.rstrip("/")
        if self.base_url.endswith("/api"):
            self.base_url = self.base_url[:-4]

        self.token = token
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Rate limiter - use provided, global default, or create disabled one
        if rate_limiter is not None:
            self._rate_limiter = rate_limiter
        elif enable_throttling:
            self._rate_limiter = get_default_limiter()
        else:
            self._rate_limiter = RateLimiter(enabled=False)

        # Default headers
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Create httpx client
        self._client: Optional[httpx.Client] = None

        # Optional per-call HTTP trace capture (opt-in via capture_traces()).
        # A stack is used so nested capture contexts work as expected.
        self._trace_stack: list[list[dict[str, Any]]] = []

    @contextmanager
    def capture_traces(self) -> Iterator[list[dict[str, Any]]]:
        """Capture HTTP request/response traces within this context.

        The returned list is populated with dicts like:
            {
              "method": "POST",
              "url": "https://.../api/...",
              "params": {...},
              "json": {...},
              "status_code": 200,
              "duration_ms": 12.3,
              "response_bytes": 1234,
            }

        Notes:
            - Authorization headers are never recorded.
            - Intended for UI/debug surfaces; do not inline traces into LLM context.
        """
        bucket: list[dict[str, Any]] = []
        self._trace_stack.append(bucket)
        try:
            yield bucket
        finally:
            # Pop only if it's still the top (defensive in case of misuse)
            if self._trace_stack and self._trace_stack[-1] is bucket:
                self._trace_stack.pop()

    def _emit_trace(self, trace: dict[str, Any]) -> None:
        """Append trace to all active capture buckets."""
        if not self._trace_stack:
            return
        for bucket in self._trace_stack:
            bucket.append(trace)

    @staticmethod
    def _bounded_json(value: Any, *, max_chars: int = 10_000) -> Any:
        """Return a JSON-serializable structure, bounded for debug surfaces."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            try:
                text = json.dumps(value, ensure_ascii=False, default=str)
            except Exception:
                return {"_unserializable": True, "type": type(value).__name__}
            if len(text) <= max_chars:
                return value
            return {
                "_truncated": True,
                "_original_chars": len(text),
                "_preview": text[:max_chars],
            }
        if isinstance(value, (bytes, bytearray)):
            size = len(value)
            if size <= max_chars:
                return value.decode("utf-8", errors="replace")
            return {
                "_truncated": True,
                "_original_bytes": size,
                "_preview": value[:max_chars].decode("utf-8", errors="replace"),
            }
        if isinstance(value, str):
            if len(value) <= max_chars:
                return value
            return {
                "_truncated": True,
                "_original_chars": len(value),
                "_preview": value[:max_chars],
            }
        return value

    @property
    def rate_limiter(self) -> RateLimiter:
        """Get the rate limiter instance."""
        return self._rate_limiter

    @property
    def client(self) -> httpx.Client:
        """Get or create the httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=True
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any]
    ) -> None:
        self.close()

    def _handle_response(self, response: httpx.Response) -> Response:
        """
        Handle HTTP response and convert to Response object.

        Args:
            response: The httpx response

        Returns:
            Response object with parsed data
            
        Note:
            This method does NOT raise exceptions for HTTP error status codes.
            Error handling is delegated to the ErrorHandler in the repository layer.
        """
        # Try to parse JSON response
        data = None
        try:
            if response.content:
                data = response.json()
        except (json.JSONDecodeError, ValueError):
            data = response.text if response.text else None

        # Create and return response object (no exceptions raised here)
        return Response(
            status_code=response.status_code,
            data=data,
            headers=dict(response.headers),
            raw=response.content
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Response:
        """
        Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/Product/ABC123")
            params: Query parameters
            data: Request body data (will be JSON encoded)
            headers: Additional headers to merge with defaults

        Returns:
            Response object
            
        Note:
            This method respects rate limiting. If the rate limit is reached,
            the call will block until a slot becomes available.
        """
        # Acquire rate limiter slot (blocks if limit reached)
        self._rate_limiter.acquire()
        
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        # Merge headers
        request_headers = self._headers.copy()
        if headers:
            request_headers.update(headers)

        # Prepare request kwargs
        kwargs: Dict[str, Any] = {
            "method": method,
            "url": endpoint,
            "headers": request_headers
        }

        if params:
            # Filter out None values
            kwargs["params"] = {
                k: v for k, v in params.items() if v is not None
            }

        if data is not None:
            if isinstance(data, (dict, list)):
                kwargs["json"] = data
            else:
                kwargs["content"] = data

        # Build a full URL string for debugging (no auth headers included)
        full_url = f"{self.base_url}{endpoint}"
        started = time.perf_counter()
        try:
            response = self.client.request(**kwargs)
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._emit_trace(
                {
                    "method": method,
                    "url": full_url,
                    "params": self._bounded_json(kwargs.get("params")),
                    "json": self._bounded_json(kwargs.get("json")),
                    "content": self._bounded_json(kwargs.get("content")),
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_bytes": len(response.content or b""),
                }
            )
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")
        except Exception as e:
            raise PyWATSError(f"HTTP request failed: {e}")

    # Convenience methods
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, **kwargs)

    def post(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make a POST request."""
        return self._make_request(
            "POST", endpoint, data=data, params=params, **kwargs
        )

    def put(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make a PUT request."""
        return self._make_request(
            "PUT", endpoint, data=data, params=params, **kwargs
        )

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make a DELETE request."""
        return self._make_request("DELETE", endpoint, params=params, **kwargs)

    def patch(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make a PATCH request."""
        return self._make_request(
            "PATCH", endpoint, data=data, params=params, **kwargs
        )
