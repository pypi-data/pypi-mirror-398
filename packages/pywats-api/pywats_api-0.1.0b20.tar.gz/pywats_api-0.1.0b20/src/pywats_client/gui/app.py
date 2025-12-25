"""
Qt Application Entry Point

Provides the main GUI application runner.
"""

import sys
import asyncio
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon

from .main_window import MainWindow
from .login_window import LoginWindow
from ..core.config import ClientConfig, get_default_config_path
from ..core.connection_config import ConnectionState, migrate_legacy_config
from ..app import pyWATSApplication


def run_gui(config: Optional[ClientConfig] = None, config_path: Optional[Path] = None, instance_id: Optional[str] = None) -> int:
    """
    Run the pyWATS Client GUI application.
    
    Flow:
    1. Load configuration
    2. Check connection state
    3. Show login if not authenticated
    4. Launch main window if authenticated
    
    Args:
        config: ClientConfig instance (optional)
        config_path: Path to configuration file (optional)
        instance_id: Instance ID for multi-instance support (optional)
    
    Returns:
        Exit code
    """
    # Set application metadata
    QCoreApplication.setOrganizationName("WATS")
    QCoreApplication.setApplicationName("WATS Client")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Create Qt application
    qt_app = QApplication(sys.argv)
    
    # Set Windows taskbar icon (AppUserModelID)
    if sys.platform == 'win32':
        import ctypes
        myappid = 'WATS.Client.1.0.0'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # Set application icon
    icon_path = Path(__file__).parent / "resources" / "favicon.ico"
    if icon_path.exists():
        qt_app.setWindowIcon(QIcon(str(icon_path)))
    
    # Apply dark theme
    qt_app.setStyle("Fusion")
    
    # Load or create configuration
    if config:
        pass  # Use provided config
    elif config_path:
        config = ClientConfig.load_or_create(Path(config_path))
    else:
        config = ClientConfig.load_or_create(get_default_config_path(instance_id))
    
    # Migrate legacy config if needed
    if not hasattr(config, 'connection') or not config.connection:
        config_dict = config.to_dict()
        migrated_dict = migrate_legacy_config(config_dict)
        from ..core.connection_config import ConnectionConfig
        config.connection = ConnectionConfig.from_dict(migrated_dict['connection'])
        config.save()
    
    # Check if authentication is required
    connection_config = getattr(config, 'connection', None)
    needs_auth = (
        connection_config is None or
        not connection_config.is_authenticated() or
        connection_config.get_state() == ConnectionState.NOT_CONNECTED
    )
    
    if needs_auth:
        # Show login dialog
        config = LoginWindow.show_login_dialog(config)
        
        if not config:
            # User cancelled login
            return 0
    
    # Create pyWATS application (service layer)
    pywats_app = pyWATSApplication(config)
    
    # Create and show main window (UI layer)
    window = MainWindow(config, pywats_app, None)  # config, app, parent
    window.show()
    
    # Run event loop
    return qt_app.exec()


def run_headless(config_path: Optional[Path] = None) -> int:
    """
    Run the pyWATS Client in headless mode (no GUI).
    
    Args:
        config_path: Path to configuration file (optional)
    
    Returns:
        Exit code
    """
    from ..core.client import WATSClient
    
    # Load configuration
    if config_path:
        config = ClientConfig.load(Path(config_path))
    else:
        config = ClientConfig.load(get_default_config_path())
    
    # Create and run client
    client = WATSClient(config)
    
    try:
        client.run()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
