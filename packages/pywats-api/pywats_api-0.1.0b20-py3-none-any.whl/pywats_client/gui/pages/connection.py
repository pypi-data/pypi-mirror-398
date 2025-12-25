"""
Connection Page

Matches the WATS Client Connection page layout.
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Slot

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ConnectionPage(BasePage):
    """Connection settings page"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Connection"
    
    def _setup_ui(self) -> None:
        """Setup page UI matching WATS Client design"""
        # Service address section
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("Service address"))
        
        self._address_edit = QLineEdit()
        self._address_edit.setPlaceholderText("https://your-wats-server.com/")
        self._address_edit.textChanged.connect(self._emit_changed)
        address_layout.addWidget(self._address_edit, 1)
        
        self._layout.addLayout(address_layout)
        
        # Disconnect button
        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setFixedWidth(120)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        self._layout.addWidget(self._disconnect_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Help text
        help_label = QLabel(
            'Service address to your wats.com account or WATS server. Click\n'
            '"Disconnect" to reset the client and log on to another service.'
        )
        help_label.setStyleSheet("color: #808080; font-size: 11px;")
        self._layout.addWidget(help_label)
        
        self._layout.addSpacing(20)
        
        # Test connection section
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test connection"))
        
        self._test_btn = QPushButton("Run test")
        self._test_btn.setFixedWidth(100)
        self._test_btn.clicked.connect(self._on_test_connection)
        test_layout.addWidget(self._test_btn)
        test_layout.addStretch()
        
        self._layout.addLayout(test_layout)
        
        self._layout.addSpacing(10)
        
        # Test send UUT section - Advanced connection test with actual report
        test_uut_layout = QHBoxLayout()
        test_uut_layout.addWidget(QLabel("Test send UUT"))
        
        self._test_uut_btn = QPushButton("Send test report")
        self._test_uut_btn.setFixedWidth(130)
        self._test_uut_btn.setToolTip(
            "Creates and submits a comprehensive test UUT report to verify\n"
            "full connectivity and report submission functionality."
        )
        self._test_uut_btn.clicked.connect(self._on_test_send_uut)
        test_uut_layout.addWidget(self._test_uut_btn)
        test_uut_layout.addStretch()
        
        self._layout.addLayout(test_uut_layout)
        
        # Test UUT help text
        test_uut_help = QLabel(
            'Sends a test UUT report with various test types (numeric, string,\n'
            'boolean, charts) to verify full data submission capability.'
        )
        test_uut_help.setStyleSheet("color: #808080; font-size: 11px;")
        self._layout.addWidget(test_uut_help)
        
        self._layout.addSpacing(20)
        
        # Status section
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("WATS Client Status"))
        self._client_status_label = QLabel("Offline")
        self._client_status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self._client_status_label)
        status_layout.addStretch()
        self._layout.addLayout(status_layout)
        
        service_status_layout = QHBoxLayout()
        service_status_layout.addWidget(QLabel("WATS Client Service"))
        self._service_status_label = QLabel("Stopped")
        self._service_status_label.setStyleSheet("font-weight: bold;")
        service_status_layout.addWidget(self._service_status_label)
        service_status_layout.addStretch()
        self._layout.addLayout(service_status_layout)
        
        identifier_layout = QHBoxLayout()
        identifier_layout.addWidget(QLabel("Current Identifier"))
        self._identifier_label = QLabel()
        self._identifier_label.setStyleSheet("font-weight: bold;")
        identifier_layout.addWidget(self._identifier_label)
        identifier_layout.addStretch()
        self._layout.addLayout(identifier_layout)
        
        self._layout.addSpacing(20)
        
        # Advanced options (collapsible)
        self._advanced_group = QGroupBox("⊙ Advanced options")
        self._advanced_group.setCheckable(True)
        self._advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(self._advanced_group)
        
        # API Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("API Token:"))
        self._token_edit = QLineEdit()
        self._token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_edit.textChanged.connect(self._emit_changed)
        token_layout.addWidget(self._token_edit, 1)
        advanced_layout.addLayout(token_layout)
        
        # Sync interval
        sync_layout = QHBoxLayout()
        sync_layout.addWidget(QLabel("Sync interval (seconds):"))
        self._sync_interval_edit = QLineEdit()
        self._sync_interval_edit.setFixedWidth(100)
        self._sync_interval_edit.textChanged.connect(self._emit_changed)
        sync_layout.addWidget(self._sync_interval_edit)
        sync_layout.addStretch()
        advanced_layout.addLayout(sync_layout)
        
        self._layout.addWidget(self._advanced_group)
        
        # Add stretch to push content to top
        self._layout.addStretch()
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.service_address = self._address_edit.text()
        self.config.api_token = self._token_edit.text()
        
        try:
            self.config.sync_interval_seconds = int(self._sync_interval_edit.text())
        except ValueError:
            pass
    
    def load_config(self) -> None:
        """Load configuration"""
        self._address_edit.setText(self.config.service_address)
        self._token_edit.setText(self.config.api_token)
        self._sync_interval_edit.setText(str(self.config.sync_interval_seconds))
        self._identifier_label.setText(self.config.formatted_identifier)
    
    def update_status(self, status: str) -> None:
        """Update connection status display"""
        self._client_status_label.setText(status)
        
        if status == "Online":
            self._client_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
            self._service_status_label.setText("Running")
            self._service_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
        elif status == "Connecting":
            self._client_status_label.setStyleSheet("font-weight: bold; color: #dcdcaa;")
            self._service_status_label.setText("Starting")
            self._service_status_label.setStyleSheet("font-weight: bold; color: #dcdcaa;")
        else:
            self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
            self._service_status_label.setText("Stopped")
            self._service_status_label.setStyleSheet("font-weight: bold;")
    
    def _on_disconnect(self) -> None:
        """Handle disconnect button click"""
        if self._main_window:
            asyncio.create_task(self._main_window.disconnect())
    
    def _on_test_connection(self) -> None:
        """Handle test connection button click"""
        self._test_btn.setEnabled(False)
        self._test_btn.setText("Testing...")
        
        # Run test in background
        asyncio.create_task(self._run_test())
    
    async def _run_test(self) -> None:
        """Run connection test"""
        try:
            if self._main_window:
                result = await self._main_window.test_connection()
                if result:
                    self._client_status_label.setText("Online")
                    self._client_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
                else:
                    self._client_status_label.setText("Connection failed")
                    self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
        except Exception as e:
            self._client_status_label.setText(f"Error: {str(e)[:30]}")
            self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
        finally:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("Run test")

    def _on_test_send_uut(self) -> None:
        """Handle test send UUT button click"""
        self._test_uut_btn.setEnabled(False)
        self._test_uut_btn.setText("Sending...")
        
        # Run test in background
        asyncio.create_task(self._run_send_uut_test())
    
    async def _run_send_uut_test(self) -> None:
        """Run test UUT send operation"""
        try:
            if self._main_window:
                result = await self._main_window.send_test_uut()
                if result.get("success"):
                    report_id = result.get("report_id", "Unknown")
                    QMessageBox.information(
                        self,
                        "Test Report Sent",
                        f"Test UUT report submitted successfully!\n\n"
                        f"Report ID: {report_id}\n"
                        f"Serial: {result.get('serial_number', 'Unknown')}\n"
                        f"Part Number: {result.get('part_number', 'Unknown')}"
                    )
                    self._client_status_label.setText("Online - Test OK")
                    self._client_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
                else:
                    error = result.get("error", "Unknown error")
                    QMessageBox.warning(
                        self,
                        "Test Report Failed",
                        f"Failed to submit test UUT report.\n\nError: {error}"
                    )
                    self._client_status_label.setText("Send failed")
                    self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error sending test report:\n{str(e)}"
            )
            self._client_status_label.setText(f"Error: {str(e)[:20]}")
            self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
        finally:
            self._test_uut_btn.setEnabled(True)
            self._test_uut_btn.setText("Send test report")

    def _on_test_send_uut(self) -> None:
        """Handle test send UUT button click"""
        self._test_uut_btn.setEnabled(False)
        self._test_uut_btn.setText("Sending...")

        # Run test in background
        asyncio.create_task(self._run_send_uut_test())

    async def _run_send_uut_test(self) -> None:
        """Run send UUT test"""
        try:
            if self._main_window:
                result = await self._main_window.test_send_uut()
                if result:
                    QMessageBox.information(self, "Success", "Test UUT report sent successfully!")
                else:
                    QMessageBox.warning(self, "Failed", "Failed to send test UUT report.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error sending test UUT: {str(e)}")
        finally:
            self._test_uut_btn.setEnabled(True)
            self._test_uut_btn.setText("Send test report")