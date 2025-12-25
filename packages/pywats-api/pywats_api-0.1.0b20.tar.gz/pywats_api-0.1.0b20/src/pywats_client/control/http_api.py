"""
HTTP Control API for pyWATS Client

Provides a lightweight REST API for remote management of headless
pyWATS Client instances. Uses only Python standard library to avoid
additional dependencies.

Endpoints:
    GET  /status          - Get service status
    GET  /config          - Get configuration
    POST /config          - Update configuration
    GET  /health          - Health check
    POST /start           - Start services
    POST /stop            - Stop services
    POST /restart         - Restart services
    GET  /converters      - List converters
    GET  /queue           - Get queue status
    POST /queue/process   - Process queue manually

Security:
    - Binds to localhost by default (127.0.0.1)
    - Optional API key authentication
    - Can be exposed via reverse proxy for remote access
"""

import asyncio
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, parse_qs
from functools import partial
import threading

if TYPE_CHECKING:
    from ..core.config import ClientConfig
    from ..app import pyWATSApplication

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for HTTP API"""
    host: str = "127.0.0.1"
    port: int = 8765
    api_key: Optional[str] = None
    enable_cors: bool = False
    read_only: bool = False


class APIResponse:
    """Helper for building API responses"""
    
    @staticmethod
    def json(data: Any, status: int = 200) -> tuple:
        """Create JSON response"""
        return (
            status,
            {"Content-Type": "application/json"},
            json.dumps(data, default=str).encode()
        )
    
    @staticmethod
    def error(message: str, status: int = 400) -> tuple:
        """Create error response"""
        return APIResponse.json({"error": message, "status": status}, status)
    
    @staticmethod
    def ok(message: str = "OK", data: Optional[Dict] = None) -> tuple:
        """Create success response"""
        response = {"status": "ok", "message": message}
        if data:
            response.update(data)
        return APIResponse.json(response)


class ControlAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for control API"""
    
    # These will be set by the server
    config: "ClientConfig" = None
    app: "pyWATSApplication" = None
    api_config: APIConfig = None
    
    def log_message(self, format: str, *args) -> None:
        """Override to use Python logging"""
        logger.debug("%s - %s", self.address_string(), format % args)
    
    def _check_auth(self) -> bool:
        """Check API key if configured"""
        if not self.api_config.api_key:
            return True
        
        auth_header = self.headers.get("X-API-Key", "")
        return auth_header == self.api_config.api_key
    
    def _send_response(self, status: int, headers: Dict[str, str], body: bytes) -> None:
        """Send HTTP response"""
        self.send_response(status)
        
        # CORS headers if enabled
        if self.api_config.enable_cors:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        
        for key, value in headers.items():
            self.send_header(key, value)
        
        self.end_headers()
        self.wfile.write(body)
    
    def _read_body(self) -> Dict[str, Any]:
        """Read and parse JSON body"""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode())
        except json.JSONDecodeError:
            return {}
    
    def _route(self, method: str, path: str) -> tuple:
        """Route request to handler"""
        # Parse path
        parsed = urlparse(path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        
        # Define routes
        routes = {
            ("GET", "/"): self._handle_root,
            ("GET", "/health"): self._handle_health,
            ("GET", "/status"): self._handle_status,
            ("GET", "/config"): self._handle_get_config,
            ("POST", "/config"): self._handle_set_config,
            ("GET", "/converters"): self._handle_list_converters,
            ("GET", "/queue"): self._handle_queue_status,
            ("POST", "/queue/process"): self._handle_process_queue,
            ("POST", "/start"): self._handle_start,
            ("POST", "/stop"): self._handle_stop,
            ("POST", "/restart"): self._handle_restart,
        }
        
        handler = routes.get((method, path))
        if handler:
            return handler(query)
        
        return APIResponse.error("Not found", 404)
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight"""
        self._send_response(200, {}, b"")
    
    def do_GET(self) -> None:
        """Handle GET requests"""
        if not self._check_auth():
            status, headers, body = APIResponse.error("Unauthorized", 401)
        else:
            status, headers, body = self._route("GET", self.path)
        self._send_response(status, headers, body)
    
    def do_POST(self) -> None:
        """Handle POST requests"""
        if not self._check_auth():
            status, headers, body = APIResponse.error("Unauthorized", 401)
        elif self.api_config.read_only:
            status, headers, body = APIResponse.error("Read-only mode", 403)
        else:
            status, headers, body = self._route("POST", self.path)
        self._send_response(status, headers, body)
    
    # Route handlers
    
    def _handle_root(self, query: Dict) -> tuple:
        """API root - show available endpoints"""
        return APIResponse.json({
            "name": "pyWATS Client Control API",
            "version": "1.0.0",
            "endpoints": {
                "GET /health": "Health check",
                "GET /status": "Service status",
                "GET /config": "Get configuration",
                "POST /config": "Update configuration",
                "GET /converters": "List converters",
                "GET /queue": "Queue status",
                "POST /queue/process": "Process queue",
                "POST /start": "Start services",
                "POST /stop": "Stop services",
                "POST /restart": "Restart services",
            }
        })
    
    def _handle_health(self, query: Dict) -> tuple:
        """Health check endpoint"""
        return APIResponse.json({
            "status": "healthy",
            "service": "pywats-client",
        })
    
    def _handle_status(self, query: Dict) -> tuple:
        """Get service status"""
        status_data = {
            "instance_name": self.config.instance_name,
            "station_name": self.config.station_name,
            "server_url": self.config.service_address,
            "connected": False,
            "services": {},
        }
        
        if self.app:
            from ..app import ApplicationStatus
            status_data["connected"] = self.app.status == ApplicationStatus.RUNNING
            status_data["application_status"] = self.app.status.value
            
            # Service status
            if self.app._connection:
                status_data["services"]["connection"] = {
                    "status": self.app._connection.status.value if self.app._connection.status else "unknown"
                }
            if self.app._report_queue:
                # Get actual queue stats
                queue_stats = self._get_queue_stats()
                status_data["services"]["report_queue"] = queue_stats
        
        return APIResponse.json(status_data)
    
    def _get_queue_stats(self) -> Dict[str, Any]:
        """Get report queue statistics"""
        stats = {"pending": 0, "failed": 0, "processed_today": 0}
        if self.app and self.app._report_queue:
            try:
                # Try to get actual counts from the queue service
                queue = self.app._report_queue
                if hasattr(queue, 'get_pending_count'):
                    stats["pending"] = queue.get_pending_count()
                if hasattr(queue, 'get_failed_count'):
                    stats["failed"] = queue.get_failed_count()
                if hasattr(queue, '_pending_reports'):
                    stats["pending"] = len(queue._pending_reports)
            except Exception:
                pass
        return stats
    
    def _handle_get_config(self, query: Dict) -> tuple:
        """Get configuration"""
        config_dict = self.config.to_dict()
        
        # Mask sensitive values
        if "api_token" in config_dict and config_dict["api_token"]:
            config_dict["api_token"] = "****"
        if "proxy_password" in config_dict and config_dict["proxy_password"]:
            config_dict["proxy_password"] = "****"
        
        return APIResponse.json(config_dict)
    
    def _handle_set_config(self, query: Dict) -> tuple:
        """Update configuration"""
        body = self._read_body()
        
        if not body:
            return APIResponse.error("No configuration provided")
        
        # Update allowed fields
        allowed_fields = [
            "instance_name", "station_name", "location", "purpose",
            "log_level", "converters_enabled",
        ]
        
        updated = []
        for key, value in body.items():
            if key in allowed_fields:
                setattr(self.config, key, value)
                updated.append(key)
        
        if updated:
            # Save config
            self.config.save(self.config._config_path)
            return APIResponse.ok(f"Updated: {', '.join(updated)}")
        else:
            return APIResponse.error("No valid fields to update")
    
    def _handle_list_converters(self, query: Dict) -> tuple:
        """List available converters"""
        converters = []
        
        if self.app and self.app._converter_manager:
            for name, conv in self.app._converter_manager._converters.items():
                converters.append({
                    "name": name,
                    "type": type(conv).__name__,
                    "enabled": True,
                })
        
        return APIResponse.json({"converters": converters})
    
    def _handle_queue_status(self, query: Dict) -> tuple:
        """Get report queue status"""
        queue_data = self._get_queue_stats()
        return APIResponse.json(queue_data)
    
    def _handle_process_queue(self, query: Dict) -> tuple:
        """Manually process the report queue"""
        if self.app and self.app._report_queue:
            # Schedule async task safely from sync context
            self._run_async(self.app._report_queue._process_queue())
            return APIResponse.ok("Queue processing triggered")
        return APIResponse.error("Report queue not available")
    
    def _run_async(self, coro) -> None:
        """Run an async coroutine from sync HTTP handler.
        
        This schedules the coroutine on the application's event loop
        if available, otherwise creates a new thread.
        """
        import threading
        
        def run_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(coro)
                loop.close()
            except Exception as e:
                logger.error(f"Async task error: {e}")
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
    
    def _handle_start(self, query: Dict) -> tuple:
        """Start services"""
        if self.app:
            self._run_async(self.app.start())
            return APIResponse.ok("Services starting")
        return APIResponse.error("Application not available")
    
    def _handle_stop(self, query: Dict) -> tuple:
        """Stop services"""
        if self.app:
            self._run_async(self.app.stop())
            return APIResponse.ok("Services stopping")
        return APIResponse.error("Application not available")
    
    def _handle_restart(self, query: Dict) -> tuple:
        """Restart services"""
        if self.app:
            self._run_async(self.app.restart())
            return APIResponse.ok("Services restarting")
        return APIResponse.error("Application not available")


class ControlAPIServer:
    """
    HTTP Control API Server for headless management.
    
    Usage:
        server = ControlAPIServer(config, api_config)
        server.start()  # Starts in background thread
        
        # Later...
        server.stop()
    """
    
    def __init__(self, 
                 client_config: "ClientConfig",
                 api_config: Optional[APIConfig] = None,
                 app: Optional["pyWATSApplication"] = None):
        """
        Initialize API server.
        
        Args:
            client_config: Client configuration
            api_config: API server configuration
            app: pyWATSApplication instance (optional)
        """
        self.client_config = client_config
        self.api_config = api_config or APIConfig()
        self.app = app
        
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
    
    def _create_handler(self):
        """Create handler class with config"""
        handler = ControlAPIHandler
        handler.config = self.client_config
        handler.app = self.app
        handler.api_config = self.api_config
        return handler
    
    def start(self, blocking: bool = False) -> None:
        """
        Start the API server.
        
        Args:
            blocking: If True, run in foreground. If False, run in background thread.
        """
        handler = self._create_handler()
        self._server = HTTPServer(
            (self.api_config.host, self.api_config.port),
            handler
        )
        
        self._running = True
        logger.info(f"Control API starting on http://{self.api_config.host}:{self.api_config.port}")
        
        if blocking:
            try:
                self._server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()
        else:
            self._thread = threading.Thread(target=self._server.serve_forever)
            self._thread.daemon = True
            self._thread.start()
    
    def stop(self) -> None:
        """Stop the API server"""
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Control API stopped")
    
    def set_app(self, app: "pyWATSApplication") -> None:
        """Set the application instance after server creation"""
        self.app = app
        # Update handler reference
        ControlAPIHandler.app = app


# Standalone server for testing
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from pywats_client.core.config import ClientConfig
    
    logging.basicConfig(level=logging.DEBUG)
    
    config = ClientConfig()
    api_config = APIConfig(host="127.0.0.1", port=8765)
    
    server = ControlAPIServer(config, api_config)
    print(f"Starting API server on http://{api_config.host}:{api_config.port}")
    print("Press Ctrl+C to stop")
    
    server.start(blocking=True)
