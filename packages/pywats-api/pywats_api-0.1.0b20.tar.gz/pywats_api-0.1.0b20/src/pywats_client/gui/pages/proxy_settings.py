"""
Proxy Settings Page

Matches the WATS Client Proxy page layout.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QRadioButton, QButtonGroup, QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt

from .base import BasePage
from ...core.config import ClientConfig


class ProxySettingsPage(BasePage):
    """Proxy settings page"""
    
    def __init__(self, config: ClientConfig, parent: Optional[QWidget] = None):
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Proxy Settings"
    
    def _setup_ui(self) -> None:
        """Setup page UI matching WATS Client design"""
        # Proxy mode selection
        self._proxy_mode_group = QButtonGroup(self)
        
        self._no_proxy_radio = QRadioButton("No proxy")
        self._system_proxy_radio = QRadioButton("Use system proxy settings")
        self._manual_proxy_radio = QRadioButton("Manual proxy configuration")
        
        self._proxy_mode_group.addButton(self._no_proxy_radio, 0)
        self._proxy_mode_group.addButton(self._system_proxy_radio, 1)
        self._proxy_mode_group.addButton(self._manual_proxy_radio, 2)
        
        self._layout.addWidget(self._no_proxy_radio)
        self._layout.addWidget(self._system_proxy_radio)
        self._layout.addWidget(self._manual_proxy_radio)
        
        self._proxy_mode_group.buttonToggled.connect(self._on_proxy_mode_changed)
        
        self._layout.addSpacing(20)
        
        # Manual proxy settings group
        self._manual_group = QGroupBox("Manual proxy settings")
        manual_layout = QVBoxLayout(self._manual_group)
        
        # Proxy host
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Proxy host:"))
        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText("proxy.example.com")
        self._host_edit.textChanged.connect(self._emit_changed)
        host_layout.addWidget(self._host_edit, 1)
        manual_layout.addLayout(host_layout)
        
        # Proxy port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Proxy port:"))
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(8080)
        self._port_spin.setFixedWidth(100)
        self._port_spin.valueChanged.connect(self._emit_changed)
        port_layout.addWidget(self._port_spin)
        port_layout.addStretch()
        manual_layout.addLayout(port_layout)
        
        # Authentication
        self._auth_check = QCheckBox("Proxy requires authentication")
        self._auth_check.toggled.connect(self._on_auth_toggled)
        self._auth_check.toggled.connect(self._emit_changed)
        manual_layout.addWidget(self._auth_check)
        
        # Username
        user_layout = QHBoxLayout()
        self._user_label = QLabel("Username:")
        user_layout.addWidget(self._user_label)
        self._user_edit = QLineEdit()
        self._user_edit.textChanged.connect(self._emit_changed)
        user_layout.addWidget(self._user_edit, 1)
        manual_layout.addLayout(user_layout)
        
        # Password
        pass_layout = QHBoxLayout()
        self._pass_label = QLabel("Password:")
        pass_layout.addWidget(self._pass_label)
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_edit.textChanged.connect(self._emit_changed)
        pass_layout.addWidget(self._pass_edit, 1)
        manual_layout.addLayout(pass_layout)
        
        self._layout.addWidget(self._manual_group)
        
        # Bypass list
        self._bypass_group = QGroupBox("Bypass proxy for")
        bypass_layout = QVBoxLayout(self._bypass_group)
        
        self._bypass_edit = QLineEdit()
        self._bypass_edit.setPlaceholderText("localhost, 127.0.0.1, *.local")
        self._bypass_edit.textChanged.connect(self._emit_changed)
        bypass_layout.addWidget(self._bypass_edit)
        
        bypass_help = QLabel("Comma-separated list of hosts that should bypass the proxy.")
        bypass_help.setStyleSheet("color: #808080; font-size: 11px;")
        bypass_layout.addWidget(bypass_help)
        
        self._layout.addWidget(self._bypass_group)
        
        # Add stretch to push content to top
        self._layout.addStretch()
        
        # Set initial state
        self._update_manual_group_state()
        self._on_auth_toggled(False)
    
    def _on_proxy_mode_changed(self) -> None:
        """Handle proxy mode selection change"""
        self._update_manual_group_state()
        self._emit_changed()
    
    def _update_manual_group_state(self) -> None:
        """Enable/disable manual proxy settings based on mode"""
        is_manual = self._manual_proxy_radio.isChecked()
        self._manual_group.setEnabled(is_manual)
        self._bypass_group.setEnabled(is_manual)
    
    def _on_auth_toggled(self, checked: bool) -> None:
        """Enable/disable authentication fields"""
        self._user_label.setEnabled(checked)
        self._user_edit.setEnabled(checked)
        self._pass_label.setEnabled(checked)
        self._pass_edit.setEnabled(checked)
    
    def save_config(self) -> None:
        """Save configuration"""
        if self._no_proxy_radio.isChecked():
            self.config.proxy_mode = "none"
        elif self._system_proxy_radio.isChecked():
            self.config.proxy_mode = "system"
        else:
            self.config.proxy_mode = "manual"
        
        self.config.proxy_host = self._host_edit.text()
        self.config.proxy_port = self._port_spin.value()
        self.config.proxy_auth = self._auth_check.isChecked()
        self.config.proxy_username = self._user_edit.text()
        self.config.proxy_password = self._pass_edit.text()
        self.config.proxy_bypass = self._bypass_edit.text()
    
    def load_config(self) -> None:
        """Load configuration"""
        mode = getattr(self.config, 'proxy_mode', 'system')
        if mode == "none":
            self._no_proxy_radio.setChecked(True)
        elif mode == "system":
            self._system_proxy_radio.setChecked(True)
        else:
            self._manual_proxy_radio.setChecked(True)
        
        self._host_edit.setText(getattr(self.config, 'proxy_host', ''))
        self._port_spin.setValue(getattr(self.config, 'proxy_port', 8080))
        self._auth_check.setChecked(getattr(self.config, 'proxy_auth', False))
        self._user_edit.setText(getattr(self.config, 'proxy_username', ''))
        self._pass_edit.setText(getattr(self.config, 'proxy_password', ''))
        self._bypass_edit.setText(getattr(self.config, 'proxy_bypass', ''))
        
        self._update_manual_group_state()
        self._on_auth_toggled(self._auth_check.isChecked())
