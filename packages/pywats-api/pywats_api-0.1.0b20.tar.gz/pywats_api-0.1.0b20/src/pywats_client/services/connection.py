"""
Connection Service

Manages connection to WATS server and monitors connectivity status.
Supports persistent authentication with encrypted token storage.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Callable, List, TYPE_CHECKING
from datetime import datetime

from ..core.connection_config import ConnectionConfig, ConnectionState
from ..core.encryption import encrypt_token, decrypt_token

if TYPE_CHECKING:
    from ..core.config import ProxyConfig

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status states (for internal use)"""
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    ONLINE = "Online"
    OFFLINE = "Offline"
    ERROR = "Error"
    AUTHENTICATING = "Authenticating"


class ConnectionService:
    """
    Manages connection to WATS server with persistent authentication.
    
    Features:
    - Persistent connection state (Connected/Offline/Not Connected)
    - Password-to-token authentication
    - Encrypted token storage
    - Automatic health monitoring
    - Automatic reconnection when server comes back online
    - Connection statistics tracking
    """
    
    def __init__(
        self,
        connection_config: ConnectionConfig,
        proxy_config: Optional['ProxyConfig'] = None,
        on_config_changed: Optional[Callable[[], None]] = None
    ):
        """
        Initialize connection service.
        
        Args:
            connection_config: Connection configuration with persistent state
            proxy_config: Optional proxy configuration
            on_config_changed: Callback when config needs to be saved
        """
        self.config = connection_config
        self.proxy_config = proxy_config
        self._on_config_changed = on_config_changed
        
        self._status = ConnectionStatus.DISCONNECTED
        self._status_callbacks: List[Callable[[ConnectionStatus], None]] = []
        self._pywats_client: Optional[any] = None  # pyWATS client instance
        self._check_task: Optional[asyncio.Task] = None
        self._last_check: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._reconnect_attempts = 0
    
    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status"""
        return self._status
    
    @status.setter
    def status(self, value: ConnectionStatus) -> None:
        """Set status and notify callbacks"""
        if self._status != value:
            old_status = self._status
            self._status = value
            logger.info(f"Connection status changed: {old_status.value} -> {value.value}")
            for callback in self._status_callbacks:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message"""
        return self._last_error
    
    def on_status_change(self, callback: Callable[[ConnectionStatus], None]) -> None:
        """Register callback for status changes"""
        self._status_callbacks.append(callback)
    
    def authenticate(self, server_url: str, password: str, username: str = "") -> bool:
        """
        Authenticate with server using password and store encrypted token.
        
        This is the primary way to establish a connection. The password is
        exchanged for an API token which is then encrypted and stored.
        
        Args:
            server_url: WATS server URL (e.g., https://company.wats.com)
            password: User password for authentication
            username: Optional username for display purposes
            
        Returns:
            True if authentication successful
        """
        server_url = server_url.rstrip('/')
        
        if not server_url or not password:
            logger.error("Server URL and password are required")
            self.status = ConnectionStatus.ERROR
            self._last_error = "Server URL and password are required"
            return False
        
        self.status = ConnectionStatus.AUTHENTICATING
        
        try:
            # Exchange password for API token
            token = self._exchange_credentials(server_url, password)
            
            if not token:
                self.status = ConnectionStatus.ERROR
                self._last_error = "Authentication failed - invalid credentials"
                return False
            
            # Encrypt and store token
            self.config.server_url = server_url
            self.config.username = username
            self.config.token_encrypted = encrypt_token(token)
            self.config.mark_connected()
            self._save_config()
            
            # Now connect using the token
            return self.connect()
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self.status = ConnectionStatus.ERROR
            self._last_error = f"Authentication failed: {e}"
            return False
    
    def _exchange_credentials(self, server_url: str, password: str) -> Optional[str]:
        """
        Exchange password for API token.
        
        Args:
            server_url: WATS server URL
            password: User password
            
        Returns:
            API token if successful, None otherwise
        """
        try:
            from pywats import pyWATS
            
            # Create temporary client with password auth
            # Note: This assumes pyWATS supports password auth
            # If not, we'll need to use the password as the token directly
            # or implement a separate auth endpoint
            
            # For now, use password as token (WATS API uses password as token)
            client = pyWATS(base_url=server_url, token=password)
            
            # Test if credentials work by getting version
            try:
                version = client.get_version()
                if version:
                    logger.info("Authentication successful")
                    return password  # In WATS, the password IS the API token
                else:
                    logger.error("Credential test failed: get_version returned None")
                    self._last_error = "Invalid credentials or server unreachable"
                    return None
            except Exception as e:
                logger.error(f"Credential test failed: {e}")
                self._last_error = f"Connection failed: {str(e)}"
                return None
                
        except Exception as e:
            logger.error(f"Error during credential exchange: {e}")
            return None
    
    def connect(self) -> bool:
        """
        Establish connection to WATS server using stored credentials.
        
        This method uses the encrypted token from config.
        For initial authentication, use authenticate() instead.
        
        Returns:
            True if connection successful
        """
        if not self.config.is_authenticated():
            logger.error("No stored credentials - use authenticate() first")
            self.status = ConnectionStatus.ERROR
            self._last_error = "No stored credentials"
            return False
        
        self.status = ConnectionStatus.CONNECTING
        
        try:
            # Decrypt token
            token = decrypt_token(self.config.token_encrypted)
            
            # Import pyWATS and create client
            from pywats import pyWATS
            
            self._pywats_client = pyWATS(
                base_url=self.config.server_url,
                token=token
            )
            
            # Test connection
            if self.test_connection():
                self.status = ConnectionStatus.ONLINE
                self.config.mark_connected()
                self._save_config()
                self._reconnect_attempts = 0
                
                logger.info("Connected to WATS server")
                return True
            else:
                self.status = ConnectionStatus.OFFLINE
                self.config.mark_offline()
                self._save_config()
                self._last_error = "Server unreachable"
                
                return False
                
        except ImportError:
            logger.error("pyWATS package not found")
            self.status = ConnectionStatus.ERROR
            self._last_error = "pyWATS package not installed"
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.status = ConnectionStatus.ERROR
            self._last_error = str(e)
            return False
    
    def disconnect(self, clear_credentials: bool = True) -> None:
        """
        Disconnect from WATS server.
        
        Args:
            clear_credentials: If True, clears stored credentials (logout).
                             If False, keeps credentials for reconnect (temporary disconnect).
        """
        # Cancel health check task if exists
        if self._check_task:
            self._check_task.cancel()
            self._check_task = None
        
        self._pywats_client = None
        self.status = ConnectionStatus.DISCONNECTED
        
        if clear_credentials:
            # User-initiated logout - clear all credentials
            logger.info("Logging out - clearing credentials")
            self.config.mark_disconnected()
            self._save_config()
        else:
            # Temporary disconnect - keep credentials
            logger.info("Disconnecting (credentials retained)")
    
    def _save_config(self) -> None:
        """Save config changes"""
        if self._on_config_changed:
            try:
                self._on_config_changed()
            except Exception as e:
                logger.error(f"Error saving config: {e}")
    
    def test_connection(self) -> bool:
        """
        Test connection to WATS server.
        
        Returns True if server is reachable and credentials are valid.
        """
        if not self._pywats_client:
            self._last_error = "Client not initialized"
            return False
        
        try:
            # Try to get version info as a simple connection test
            version = self._pywats_client.get_version()
            self._last_check = datetime.now()
            if version is not None:
                return True
            else:
                self._last_error = "get_version returned None"
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            self._last_error = f"Connection test failed: {str(e)}"
            return False
    
    async def _health_check_loop(self) -> None:
        """
        Background task to monitor connection health and handle reconnection.
        
        This runs continuously when credentials are stored:
        - If ONLINE: Monitors for connection loss
        - If OFFLINE: Attempts reconnection at intervals
        """
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Record health check
                is_healthy = self.test_connection()
                self.config.record_health_check(is_healthy)
                
                if is_healthy:
                    # Server is reachable
                    if self.status == ConnectionStatus.OFFLINE:
                        # Connection restored
                        logger.info("Connection restored")
                        self.status = ConnectionStatus.ONLINE
                        self.config.mark_connected()
                        self._save_config()
                        self._reconnect_attempts = 0
                    elif self.status != ConnectionStatus.ONLINE:
                        # First successful check after connect
                        self.status = ConnectionStatus.ONLINE
                else:
                    # Server is unreachable
                    if self.status == ConnectionStatus.ONLINE:
                        # Connection lost
                        logger.warning("Connection lost - entering offline mode")
                        self.status = ConnectionStatus.OFFLINE
                        self.config.mark_offline()
                        self._save_config()
                    
                    # Handle reconnection attempts
                    if self.config.auto_reconnect:
                        if self.config.max_reconnect_attempts == 0 or \
                           self._reconnect_attempts < self.config.max_reconnect_attempts:
                            self._reconnect_attempts += 1
                            logger.debug(f"Reconnection attempt {self._reconnect_attempts}")
                            
                            # Try to reconnect
                            try:
                                if not self._pywats_client and self.config.is_authenticated():
                                    token = decrypt_token(self.config.token_encrypted)
                                    from pywats import pyWATS
                                    self._pywats_client = pyWATS(
                                        base_url=self.config.server_url,
                                        token=token
                                    )
                            except Exception as e:
                                logger.debug(f"Reconnection failed: {e}")
                        
            except asyncio.CancelledError:
                logger.debug("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def get_client(self) -> Optional[any]:
        """
        Get the pyWATS client instance.
        
        Returns None if not connected.
        """
        return self._pywats_client
    
    def is_authenticated(self) -> bool:
        """Check if we have stored credentials"""
        return self.config.is_authenticated()
    
    def is_online(self) -> bool:
        """Check if currently connected and online"""
        return self.status == ConnectionStatus.ONLINE
    
    def is_offline(self) -> bool:
        """Check if offline (authenticated but server unreachable)"""
        return self.status == ConnectionStatus.OFFLINE
    
    def get_connection_state(self) -> ConnectionState:
        """Get persistent connection state"""
        return self.config.get_state()
    
    def get_status_info(self) -> dict:
        """Get detailed status information"""
        return {
            "status": self.status.value,
            "connection_state": self.config.connection_state,
            "server_url": self.config.server_url,
            "username": self.config.username,
            "authenticated": self.config.is_authenticated(),
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "last_connected": self.config.last_connected,
            "last_error": self._last_error,
            "health_check_success_rate": self.config.get_health_check_success_rate(),
            "reconnect_attempts": self._reconnect_attempts,
        }
    
    def restore_connection(self) -> bool:
        """
        Restore connection using stored credentials.
        
        This is called on application startup to automatically reconnect
        if credentials are stored.
        
        Returns:
            True if connection restored successfully
        """
        if not self.config.is_authenticated():
            logger.info("No stored credentials to restore")
            return False
        
        if self.config.get_state() == ConnectionState.NOT_CONNECTED:
            logger.info("Previous state was 'Not Connected' - not restoring")
            return False
        
        logger.info("Restoring connection from stored credentials")
        return self.connect()
