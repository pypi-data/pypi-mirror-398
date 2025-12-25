"""
Main Window for WATS Client GUI

Implements the main application window with navigation sidebar
and content pages matching the WATS Client design.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, TYPE_CHECKING, cast
from pathlib import Path

logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QListWidget, QListWidgetItem, QLabel, QFrame, QSizePolicy,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication, QPushButton
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QCloseEvent

from .styles import DARK_STYLESHEET
from .settings_dialog import SettingsDialog
from .pages import (
    BasePage, SetupPage, ConnectionPage,
    ConvertersPage, ConvertersPageV2, SNHandlerPage, SoftwarePage, AboutPage, LogPage,
    AssetPage, RootCausePage, ProductionPage, ProductPage
)
from ..core.config import ClientConfig
from ..app import pyWATSApplication, ApplicationStatus


class SidebarMode(Enum):
    """Sidebar display modes"""
    ADVANCED = "advanced"   # All items visible, full width
    COMPACT = "compact"     # Essential items only, full width  
    MINIMIZED = "minimized" # Icons only, narrow width


class MainWindow(QMainWindow):
    """
    Main application window for WATS Client.
    
    Features:
    - Navigation sidebar with page selection
    - Stacked widget for page content
    - System tray integration
    - Status bar with connection info
    - Integration with pyWATSApplication service layer
    """
    
    # Signals for async updates
    connection_status_changed = Signal(str)
    application_status_changed = Signal(str)
    
    # Pages hidden in Compact mode (advanced features)
    ADVANCED_PAGES = {"Assets", "Software", "RootCause", "Products", "Production"}
    
    def __init__(
        self, 
        config: ClientConfig, 
        app: Optional[pyWATSApplication] = None, 
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.config = config
        self.app = app if app else pyWATSApplication(config)  # pyWATSApplication instance
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._is_connected = False
        
        # Setup UI
        self._setup_window()
        self._setup_tray_icon()
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
        # Connect application status callbacks
        self.app.on_status_changed(self._on_app_status_changed)
        
        # Update timer for status refresh
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(5000)  # Update every 5 seconds
        
        # Auto-start application if previously connected or auto_connect is enabled
        QTimer.singleShot(500, self._auto_start_on_startup)
    
    def _auto_start_on_startup(self) -> None:
        """Auto-start application on startup if configured"""
        # Auto-start disabled - connection established at login
        # User is already connected when main window opens
        pass
    
    def _do_auto_start(self) -> None:
        """Perform auto-start of application services"""
        try:
            self.application_status_changed.emit("Starting")
            self.app.start()
            self._is_connected = True
            
            # Update UI based on connection status
            if self.app.is_online():
                self.connection_status_changed.emit("Online")
            else:
                self.connection_status_changed.emit("Offline (Queuing)")
            
            # Update setup page state
            if "Setup" in self._pages:
                setup_page = cast(SetupPage, self._pages["Setup"])
                setup_page.set_connected(True)
        except Exception as e:
            self.connection_status_changed.emit(f"Error: {str(e)[:20]}")
            self.application_status_changed.emit("Error")
    
    def _on_app_status_changed(self, status: ApplicationStatus) -> None:
        """Handle application status changes"""
        self.application_status_changed.emit(status.value)
    
    def _setup_window(self) -> None:
        """Configure window properties"""
        self.setWindowTitle(f"WATS Client - {self.config.instance_name}")
        self.setMinimumSize(800, 600)
        self.resize(900, 650)
        
        # Set window icon for taskbar
        from PySide6.QtGui import QIcon
        icon_path = Path(__file__).parent / "resources" / "favicon2.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def _setup_tray_icon(self) -> None:
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)
        
        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(self._on_tray_activated)
        
        if self.config.minimize_to_tray:
            tray_icon.show()
        
        self._tray_icon = tray_icon
    
    def _setup_ui(self) -> None:
        """Setup the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self._create_sidebar(main_layout)
        
        # Create content area
        self._create_content_area(main_layout)
        
        # Create status bar
        self._create_status_bar()
    
    def _create_sidebar(self, layout: QHBoxLayout) -> None:
        """Create navigation sidebar with collapsible modes"""
        # Track sidebar mode
        self._sidebar_mode = SidebarMode.ADVANCED
        
        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet("background-color: #252526;")
        
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo/Title area with mode toggle
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(15, 15, 15, 15)
        
        # Logo icon - use bee favicon
        from PySide6.QtGui import QPixmap
        self._logo_icon = QLabel()
        icon_path = Path(__file__).parent / "resources" / "favicon2.ico"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                28, 28, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self._logo_icon.setPixmap(pixmap)
        else:
            self._logo_icon.setText("🐝")
            self._logo_icon.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(self._logo_icon)
        
        self._title_label = QLabel("WATS Client")
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        logo_layout.addWidget(self._title_label)
        logo_layout.addStretch()
        
        # Mode toggle button
        self._mode_btn = QPushButton("◀")
        self._mode_btn.setObjectName("modeButton")
        self._mode_btn.setToolTip("Toggle sidebar mode (Advanced/Compact/Minimized)")
        self._mode_btn.setFixedSize(24, 24)
        self._mode_btn.setStyleSheet("""
            QPushButton#modeButton {
                background-color: transparent;
                border: none;
                color: #808080;
                font-size: 12px;
            }
            QPushButton#modeButton:hover {
                color: #ffffff;
                background-color: #3c3c3c;
                border-radius: 4px;
            }
        """)
        self._mode_btn.clicked.connect(self._toggle_sidebar_mode)
        logo_layout.addWidget(self._mode_btn)
        
        sidebar_layout.addWidget(logo_frame)
        
        # Navigation list
        self._nav_list = QListWidget()
        self._nav_list.setObjectName("navList")
        
        # Build nav items - store all items for filtering by mode
        self._all_nav_items = self._build_nav_items()
        self._update_nav_list()
        
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self._nav_list, 1)
        
        # Footer with Settings button
        self._footer_frame = QFrame()
        footer_layout = QVBoxLayout(self._footer_frame)
        footer_layout.setContentsMargins(15, 10, 15, 15)
        footer_layout.setSpacing(10)
        
        # Settings button row
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(0, 0, 0, 5)
        
        self._settings_btn = QPushButton("⚙  Settings")
        self._settings_btn.setObjectName("settingsButton")
        self._settings_btn.setStyleSheet("""
            QPushButton#settingsButton {
                background-color: transparent;
                border: none;
                color: #808080;
                text-align: left;
                padding: 8px 10px;
                font-size: 13px;
            }
            QPushButton#settingsButton:hover {
                background-color: #2a2d2e;
                color: #ffffff;
            }
        """)
        self._settings_btn.clicked.connect(self._open_settings_dialog)
        settings_row.addWidget(self._settings_btn)
        settings_row.addStretch()
        
        footer_layout.addLayout(settings_row)
        
        from .. import __version__
        self._footer_label = QLabel(f"pyWATS Client | v{__version__}")
        self._footer_label.setObjectName("footerLabel")
        footer_layout.addWidget(self._footer_label)
        
        sidebar_layout.addWidget(self._footer_frame)
        
        layout.addWidget(self._sidebar)
    
    def _build_nav_items(self) -> list:
        """Build list of all navigation items based on config"""
        # Core navigation items that are always shown
        nav_items = [
            ("General", "⚙️"),
            ("Connection", "🔗"),
            ("Log", "📋"),
        ]
        
        # Add optional operational tabs based on configuration
        # Note: Location and Proxy Settings are now in Settings dialog only
        if self.config.show_converters_tab:
            nav_items.append(("Converters", "🔄"))
        if self.config.show_sn_handler_tab:
            nav_items.append(("SN Handler", "🔢"))
        if self.config.show_software_tab:
            nav_items.append(("Software", "💻"))
        if self.config.show_asset_tab:
            nav_items.append(("Assets", "🔧"))
        if self.config.show_rootcause_tab:
            nav_items.append(("RootCause", "🎫"))
        if self.config.show_production_tab:
            nav_items.append(("Production", "🏭"))
        if self.config.show_product_tab:
            nav_items.append(("Products", "📦"))
        
        return nav_items
    
    def _update_nav_list(self) -> None:
        """Update navigation list based on current sidebar mode"""
        self._nav_list.clear()
        
        for name, icon in self._all_nav_items:
            # In Compact mode, skip advanced pages
            if self._sidebar_mode == SidebarMode.COMPACT and name in self.ADVANCED_PAGES:
                continue
            
            if self._sidebar_mode == SidebarMode.MINIMIZED:
                # Icons only
                item = QListWidgetItem(icon)
                item.setToolTip(name)
            else:
                # Full text with icon
                item = QListWidgetItem(f"  {icon}  {name}")
            
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setSizeHint(QSize(0, 45))
            self._nav_list.addItem(item)
        
        # Select first item
        if self._nav_list.count() > 0:
            self._nav_list.setCurrentRow(0)
    
    def _toggle_sidebar_mode(self) -> None:
        """Cycle through sidebar modes: Advanced -> Compact -> Minimized -> Advanced"""
        if self._sidebar_mode == SidebarMode.ADVANCED:
            self._sidebar_mode = SidebarMode.COMPACT
            self._mode_btn.setText("◀")
            self._mode_btn.setToolTip("Compact mode (essential items) - click for Minimized")
        elif self._sidebar_mode == SidebarMode.COMPACT:
            self._sidebar_mode = SidebarMode.MINIMIZED
            self._mode_btn.setText("▶")
            self._mode_btn.setToolTip("Minimized mode (icons only) - click for Advanced")
        else:
            self._sidebar_mode = SidebarMode.ADVANCED
            self._mode_btn.setText("◀")
            self._mode_btn.setToolTip("Advanced mode (all items) - click for Compact")
        
        self._apply_sidebar_mode()
    
    def _apply_sidebar_mode(self) -> None:
        """Apply current sidebar mode styling and layout"""
        if self._sidebar_mode == SidebarMode.MINIMIZED:
            self._sidebar.setFixedWidth(60)
            self._title_label.hide()
            self._settings_btn.setText("⚙")
            self._footer_label.hide()
        else:
            self._sidebar.setFixedWidth(200)
            self._title_label.show()
            self._settings_btn.setText("⚙  Settings")
            self._footer_label.show()
        
        self._update_nav_list()
    
    def _create_content_area(self, layout: QHBoxLayout) -> None:
        """Create main content area"""
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Stacked widget for pages
        self._page_stack = QStackedWidget()
        
        # Create pages matching reference design (from screenshots)
        # Build page dict dynamically based on config visibility settings
        # Note: SetupPage is now shown as "General" in navigation
        # Note: Location and Proxy Settings are now in Settings dialog only
        self._pages: Dict[str, BasePage] = {
            "General": SetupPage(self.config, self),
            "Connection": ConnectionPage(self.config, self),
            "Log": LogPage(self.config, self),
        }
        
        # Add optional operational pages based on configuration
        if self.config.show_converters_tab:
            # Use new unified converters page (V2) with system/user distinction
            self._pages["Converters"] = ConvertersPageV2(self.config, self)
        if self.config.show_sn_handler_tab:
            self._pages["SN Handler"] = SNHandlerPage(self.config, self)
        if self.config.show_software_tab:
            self._pages["Software"] = SoftwarePage(self.config, self)
        if self.config.show_asset_tab:
            self._pages["Assets"] = AssetPage(self.config, self)
        if self.config.show_rootcause_tab:
            self._pages["RootCause"] = RootCausePage(self.config, self)
        if self.config.show_production_tab:
            self._pages["Production"] = ProductionPage(self.config, self)
        if self.config.show_product_tab:
            self._pages["Products"] = ProductPage(self.config, self)
        
        for page in self._pages.values():
            self._page_stack.addWidget(page)
            # Connect config change signal to enable Apply button
            if hasattr(page, 'config_changed'):
                page.config_changed.connect(self._on_config_changed)
        
        content_layout.addWidget(self._page_stack, 1)
        
        # Add stretch to push buttons to bottom
        content_layout.addStretch()
        
        # Apply/Cancel buttons at bottom
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 5)
        button_layout.addStretch()
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setObjectName("primaryButton")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(self._apply_btn)
        
        self._ok_btn = QPushButton("Ok")
        self._ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self._ok_btn)
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)
        
        content_layout.addWidget(button_frame)
        
        layout.addWidget(content_frame, 1)
        
        # Select first page
        self._nav_list.setCurrentRow(0)
    
    def _create_status_bar(self) -> None:
        """Create status bar with station indicator"""
        status_bar = self.statusBar()
        
        # Connection status
        self._status_label = QLabel("Disconnected")
        status_bar.addWidget(self._status_label)
        
        status_bar.addWidget(QLabel(" | "))
        
        # Station indicator (shows effective station name)
        station_label = QLabel("Station:")
        status_bar.addWidget(station_label)
        
        self._station_status_label = QLabel(self._get_effective_station_display())
        self._station_status_label.setToolTip("Active station name for reports")
        status_bar.addWidget(self._station_status_label)
        
        status_bar.addWidget(QLabel(" | "))
        
        # Instance info
        self._instance_label = QLabel(f"Instance: {self.config.instance_id}")
        status_bar.addWidget(self._instance_label)
    
    def _get_effective_station_display(self) -> str:
        """Get the effective station name for status bar display."""
        station_name = self.config.get_effective_station_name()
        if self.config.multi_station_enabled:
            return f"📍 {station_name}"
        return station_name
    
    def _update_station_status(self) -> None:
        """Update station display in status bar."""
        if hasattr(self, '_station_status_label'):
            self._station_status_label.setText(self._get_effective_station_display())
    
    def _apply_styles(self) -> None:
        """Apply dark theme stylesheet"""
        self.setStyleSheet(DARK_STYLESHEET)
    
    def _connect_signals(self) -> None:
        """Connect signals and slots"""
        self.connection_status_changed.connect(self._on_connection_status_ui)
        self.application_status_changed.connect(self._on_application_status_ui)
        
        # Connect page change signals
        for page in self._pages.values():
            if hasattr(page, 'config_changed'):
                page.config_changed.connect(self._on_config_changed)
        
        # Connect setup page connection signal
        if "Setup" in self._pages:
            setup_page = cast(SetupPage, self._pages["Setup"])
            setup_page.connection_changed.connect(self._on_connection_request)
            # Connect station change signal to update status bar
            if hasattr(setup_page, 'station_changed'):
                setup_page.station_changed.connect(self._update_station_status)
    
    @Slot(bool)
    def _on_connection_request(self, should_connect: bool) -> None:
        """Handle connection request from setup page"""
        if should_connect:
            asyncio.create_task(self._perform_start())
        else:
            asyncio.create_task(self._perform_stop())
    
    async def _perform_start(self) -> None:
        """Start application services"""
        self.application_status_changed.emit("Starting")
        try:
            await self.app.start()
            self._is_connected = True
            
            # Update connection status based on actual connection
            if self.app.is_online():
                self.connection_status_changed.emit("Online")
            else:
                self.connection_status_changed.emit("Offline (Queuing)")
            
            self.application_status_changed.emit("Running")
        except Exception as e:
            self.connection_status_changed.emit(f"Error: {str(e)[:20]}")
            self.application_status_changed.emit("Error")
            # Revert setup page state
            if "Setup" in self._pages:
                setup_page = cast(SetupPage, self._pages["Setup"])
                setup_page.set_connected(False)
    
    async def _perform_stop(self) -> None:
        """Stop application services"""
        self.application_status_changed.emit("Stopping")
        await self.app.stop()
        self._is_connected = False
        self.connection_status_changed.emit("Disconnected")
        self.application_status_changed.emit("Stopped")
    
    # Navigation handling
    
    @Slot(int)
    def _on_nav_changed(self, index: int) -> None:
        """Handle navigation item selection"""
        item = self._nav_list.item(index)
        if not item:
            return
        
        page_name = item.data(Qt.ItemDataRole.UserRole)
        if page_name and page_name in self._pages:
            page_index = list(self._pages.keys()).index(page_name)
            self._page_stack.setCurrentIndex(page_index)
    
    def _open_settings_dialog(self) -> None:
        """Open the settings dialog"""
        dialog = SettingsDialog(self.config, parent=self)
        dialog.settings_changed.connect(self._on_settings_dialog_closed)
        dialog.exec()
    
    def _on_settings_dialog_closed(self) -> None:
        """Handle settings dialog changes"""
        # Notify all pages that config may have changed
        for page in self._pages.values():
            if hasattr(page, 'load_config'):
                page.load_config()
        
        # Save client config
        self.config.save()
    
    # Button handlers
    
    def _on_apply(self) -> None:
        """Handle Apply button click - save changes and disable button"""
        self._save_config()
        self._apply_btn.setEnabled(False)
    
    def _on_ok(self) -> None:
        """Handle Ok button click"""
        self._save_config()
        self.close()
    
    def _on_cancel(self) -> None:
        """Handle Cancel button click"""
        self.close()
    
    def _on_config_changed(self) -> None:
        """Handle configuration changes"""
        self._apply_btn.setEnabled(True)
    
    def _save_config(self) -> None:
        """Save configuration from all pages"""
        for page in self._pages.values():
            if hasattr(page, 'save_config'):
                page.save_config()
        
        self.config.save()
    
    # Status handling
    
    @Slot(str)
    def _on_connection_status_ui(self, status: str) -> None:
        """Update UI for connection status change"""
        self._status_label.setText(status)
        
        # Update connection page
        if "Connection" in self._pages:
            connection_page = self._pages["Connection"]
            if isinstance(connection_page, ConnectionPage):
                connection_page.update_status(status)
    
    @Slot(str)
    def _on_application_status_ui(self, status: str) -> None:
        """Update UI for application status change"""
        # Update window title with status
        title = f"WATS Client - {self.config.instance_name}"
        if status not in ["Stopped", "Running"]:
            title += f" [{status}]"
        self.setWindowTitle(title)
    
    def _update_status(self) -> None:
        """Periodic status update"""
        # Update connection status
        if self.app.is_online():
            self.connection_status_changed.emit("Online")
        elif self.app.status == ApplicationStatus.RUNNING:
            self.connection_status_changed.emit("Offline (Queuing)")
        
        # Update queue status
        queue_status = self.app.get_queue_status()
        if queue_status.get("pending_reports", 0) > 0:
            pending = queue_status["pending_reports"]
            self._status_label.setToolTip(f"{pending} reports queued")
    
    # Window events
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event"""
        if self.config.minimize_to_tray and self._tray_icon:
            event.ignore()
            self.hide()
            self._tray_icon.showMessage(
                "WATS Client",
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self._quit_application()
            event.accept()
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def _quit_application(self) -> None:
        """Quit the application"""
        # Stop application services
        asyncio.create_task(self.app.stop())
        
        # Hide tray icon
        if self._tray_icon:
            self._tray_icon.hide()
        
        QApplication.quit()
    
    # Public methods for pages
    
    async def test_connection(self) -> bool:
        """Test connection to WATS server"""
        if self.app.wats_client:
            # Test connection by refreshing process cache
            try:
                self.app.wats_client.process.refresh()
                return True
            except Exception as e:
                logger.debug(f"Connection test failed: {e}")
                return False
        return False
    
    async def start_services(self) -> bool:
        """Start application services"""
        try:
            await self.app.start()
            self._is_connected = True
            # Persist connection state
            self.config.was_connected = True
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            return False
    
    async def stop_services(self) -> None:
        """Stop application services"""
        self._is_connected = False
        # Persist disconnected state
        self.config.was_connected = False
        self._save_config()
        await self.app.stop()
    
    def refresh_converters(self) -> None:
        """Refresh converters from converter manager"""
        if self.app.converter_manager:
            # Converter manager handles converter discovery
            pass

    async def send_test_uut(self) -> dict:
        """
        Send a test UUT report to verify full connectivity.
        
        Creates a comprehensive test report with various test types
        and submits it to the WATS server.
        
        Uses effective station info from config (respects multi-station mode).
        
        Returns:
            dict with keys:
                - success: bool indicating if submission was successful
                - report_id: UUID of submitted report (if successful)
                - serial_number: Serial number of test report
                - part_number: Part number of test report
                - error: Error message (if failed)
        """
        from pywats.tools.test_uut import create_test_uut_report
        
        try:
            # Get effective station info from config (respects multi-station mode)
            station_name = self.config.get_effective_station_name() or "pyWATS-Client"
            location = self.config.get_effective_location() or "TestLocation"
            purpose = self.config.get_effective_purpose() or "Development"
            
            # Create test report with effective station info
            report = create_test_uut_report(
                station_name=station_name,
                location=location,
                operator_name=getattr(self.config, 'operator', 'pyWATS-User')
            )
            
            # Override purpose if create_test_uut_report doesn't accept it
            if hasattr(report, 'purpose'):
                report.purpose = purpose
            
            result = {
                "success": False,
                "serial_number": report.sn,
                "part_number": report.pn,
                "report_id": str(report.id),
                "station_name": station_name
            }
            
            if self.app.wats_client:
                # Convert to dictionary for submission
                report_data = report.model_dump(mode="json", by_alias=True, exclude_none=True)
                
                # Submit the report via API client
                submit_result = await self.app.wats_client.report.create(report_data)
                if submit_result:
                    result["success"] = True
                else:
                    result["error"] = "Report submission returned false"
            else:
                result["error"] = "Client not initialized"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "serial_number": "N/A",
                "part_number": "N/A"
            }

    async def test_send_uut(self) -> bool:
        """
        Create and submit a test UUT report.
        
        Uses effective station info (respects multi-station mode).
        """
        if not self.app.wats_client:
            return False
        
        try:
            from pywats.tools import create_test_uut_report
            
            # Get effective station info from config
            station_name = self.config.get_effective_station_name() or "pyWATS-Client"
            location = self.config.get_effective_location() or "TestLocation"
            
            # Create test report using effective station info
            report = create_test_uut_report(
                station_name=station_name,
                location=location,
            )
            
            # Convert to dictionary for submission (Pydantic model_dump with by_alias for serialization)
            report_data = report.model_dump(mode="json", by_alias=True, exclude_none=True)
            
            # Submit via API client
            result = await self.app.wats_client.report.create(report_data)
            return bool(result)
        except Exception as e:
            print(f"Error creating/submitting test UUT: {e}")
            return False
