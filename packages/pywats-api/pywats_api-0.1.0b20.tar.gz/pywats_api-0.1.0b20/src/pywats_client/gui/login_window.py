"""
Login Window for pyWATS Client

Separate authentication screen shown before main GUI.
Handles password authentication and instance selection.
"""

from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QFrame, QMessageBox,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QIcon

from ..services.connection import ConnectionService
from ..core.connection_config import ConnectionConfig
from ..core.config import ClientConfig


class AuthWorker(QObject):
    """Worker for performing authentication in a separate thread."""
    
    finished = Signal(bool, str)  # success, error_message
    
    def __init__(self, connection_service: ConnectionService, url: str, password: str, username: str = "admin") -> None:
        super().__init__()
        self.connection_service = connection_service
        self.url = url
        self.password = password
        self.username = username
    
    def run(self) -> None:
        """Perform authentication."""
        try:
            success = self.connection_service.authenticate(self.url, self.password, self.username)
            error = self.connection_service.last_error if not success else ""
            self.finished.emit(success, error)
        except Exception as e:
            self.finished.emit(False, str(e))


class LoginWindow(QDialog):
    """
    Login dialog for pyWATS Client authentication.
    
    Shown when:
    - First time running (no stored credentials)
    - After user logout
    - When stored credentials are invalid
    
    Features:
    - Server URL input
    - Password input (masked)
    - Instance selection
    - Remember connection checkbox
    - Real-time validation
    - Progress indication
    """
    
    # Signal emitted when authentication successful
    authenticated = Signal(ClientConfig)  # Emits config to use
    
    def __init__(self, config: Optional[ClientConfig] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or ClientConfig()
        self.connection_service: Optional[ConnectionService] = None
        
        self._setup_ui()
        self._apply_styles()
        self._populate_from_config()
    
    def _setup_ui(self):
        """Setup the login UI"""
        self.setWindowTitle("pyWATS Client - Login")
        self.setModal(True)
        self.setFixedWidth(450)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("pyWATS Client")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Connect to WATS Server")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #888;")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(10)
        
        # Server URL
        url_label = QLabel("Server URL:")
        layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://company.wats.com")
        self.url_input.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.url_input)
        
        # Password
        password_label = QLabel("Password (API Token):")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your API token")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self._on_input_changed)
        self.password_input.returnPressed.connect(self._on_connect_clicked)
        layout.addWidget(self.password_input)
        
        # Show password checkbox
        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.stateChanged.connect(self._on_show_password_changed)
        layout.addWidget(self.show_password_cb)
        
        layout.addSpacing(5)
        
        # Remember connection
        self.remember_cb = QCheckBox("Remember connection")
        self.remember_cb.setChecked(True)
        self.remember_cb.setToolTip(
            "Keep credentials encrypted for automatic reconnection.\n"
            "Uncheck to require login each time."
        )
        layout.addWidget(self.remember_cb)
        
        # Instance selector (for future multi-instance support)
        instance_label = QLabel("Instance:")
        layout.addWidget(instance_label)
        
        self.instance_combo = QComboBox()
        self.instance_combo.addItem("Default Instance", "default")
        self.instance_combo.setToolTip("Select which instance to connect to")
        layout.addWidget(self.instance_combo)
        
        layout.addSpacing(10)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(5)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedWidth(100)
        self.connect_btn.setDefault(True)
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        button_layout.addWidget(self.connect_btn)
        
        layout.addLayout(button_layout)
        
        # Help text
        help_text = QLabel(
            '<a href="https://wats.com/support">Need help connecting?</a>'
        )
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_text.setOpenExternalLinks(True)
        help_text.setStyleSheet("color: #f0a30a; font-size: 11px;")
        layout.addWidget(help_text)
    
    def _apply_styles(self):
        """Apply styling to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                background-color: #2d2d30;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #f0a30a;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                background-color: #2d2d30;
                color: #ffffff;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                background-color: #3f3f46;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:default {
                background-color: #f0a30a;
                border: 1px solid #f0a30a;
                color: #1e1e1e;
            }
            QPushButton:default:hover {
                background-color: #d49209;
            }
            QPushButton:disabled {
                background-color: #2d2d30;
                color: #666;
            }
            QCheckBox {
                color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #3f3f46;
                border-radius: 4px;
                background-color: #2d2d30;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #f0a30a;
            }
        """)
    
    def _populate_from_config(self) -> None:
        """Populate fields from existing config"""
        if self.config.service_address:
            self.url_input.setText(self.config.service_address)
        
        # Don't populate password for security
        # User must re-enter on login screen
    
    @Slot()
    def _on_input_changed(self) -> None:
        """Validate input and enable/disable connect button"""
        url = self.url_input.text().strip()
        password = self.password_input.text().strip()
        
        # Enable connect button if both fields have content
        is_valid = bool(url and password)
        self.connect_btn.setEnabled(is_valid)
        
        # Clear status on input change
        if self.status_label.text():
            self.status_label.setText("")
    
    @Slot(int)
    def _on_show_password_changed(self, state) -> None:
        """Toggle password visibility"""
        if state == Qt.CheckState.Checked.value:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    @Slot()
    def _on_connect_clicked(self) -> None:
        """Handle connect button click"""
        self._perform_authentication()
    
    def _perform_authentication(self) -> None:
        """Perform authentication in a separate thread"""
        url = self.url_input.text().strip()
        password = self.password_input.text().strip()
        remember = self.remember_cb.isChecked()
        
        if not url or not password:
            return
        
        # Disable UI during authentication
        self.url_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.connect_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Authenticating...")
        self.status_label.setStyleSheet("color: #0078d4; font-size: 11px;")
        
        try:
            # Create connection config
            connection_config = ConnectionConfig(
                server_url=url,
                auto_reconnect=remember
            )
            
            # Create connection service
            self.connection_service = ConnectionService(connection_config)
            
            # Create worker and thread for authentication
            self.auth_thread = QThread()
            self.auth_worker = AuthWorker(self.connection_service, url, password)
            self.auth_worker.moveToThread(self.auth_thread)
            
            # Connect signals
            self.auth_thread.started.connect(self.auth_worker.run)
            self.auth_worker.finished.connect(self._on_auth_finished)
            self.auth_worker.finished.connect(self.auth_thread.quit)
            self.auth_worker.finished.connect(self.auth_worker.deleteLater)
            self.auth_thread.finished.connect(self.auth_thread.deleteLater)
            
            # Start authentication
            self.auth_thread.start()
        
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #f04040; font-size: 11px;")
            self._reset_ui()
    
    def _on_auth_finished(self, success: bool, error_message: str):
        """Handle authentication completion."""
        if success:
            # Authentication successful
            self.status_label.setText("✓ Connected successfully!")
            self.status_label.setStyleSheet("color: #10d010; font-size: 11px;")
            
            # Update config
            url = self.url_input.text().strip()
            password = self.password_input.text()
            remember = self.remember_cb.isChecked()
            
            self.config.service_address = url
            self.config.api_token = password if not remember else ""
            self.config.auto_connect = remember
            self.config.was_connected = True
            
            # Add connection to config
            if self.connection_service and not hasattr(self.config, 'connection'):
                setattr(self.config, 'connection', self.connection_service.config)
            
            # Close dialog after short delay
            QTimer.singleShot(500, lambda: self._on_auth_success())
        else:
            # Authentication failed
            error = error_message or "Authentication failed"
            self.status_label.setText(f"✗ {error}")
            self.status_label.setStyleSheet("color: #f04040; font-size: 11px;")
            
            # Re-enable UI
            self._reset_ui()
    
    def _on_auth_success(self) -> None:
        """Handle successful authentication"""
        self.authenticated.emit(self.config)
        self.accept()
    
    def _reset_ui(self) -> None:
        """Reset UI to allow retry"""
        self.url_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.connect_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.password_input.setFocus()
        self.password_input.selectAll()
    
    @classmethod
    def show_login_dialog(cls, config: Optional[ClientConfig] = None, parent=None) -> Optional[ClientConfig]:
        """
        Show login dialog and return config if successful.
        
        Args:
            config: Existing config to populate from
            parent: Parent widget
            
        Returns:
            ClientConfig if authentication successful, None if cancelled
        """
        dialog = cls(config, parent)
        
        # Use exec() for modal dialog
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return dialog.config
        return None
