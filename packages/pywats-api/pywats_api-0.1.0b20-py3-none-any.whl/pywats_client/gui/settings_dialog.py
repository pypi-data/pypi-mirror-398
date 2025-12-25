"""
Settings Dialog with TreeView Navigation

A comprehensive settings dialog inspired by VS Code's settings UI,
providing hierarchical navigation through API, Client, and GUI settings.
"""

import logging
from typing import Dict, Any, Optional, Callable, Tuple, List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QGroupBox, QFormLayout, QScrollArea, QFrame, QPushButton,
    QSplitter, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QCloseEvent

from ..core.config import ClientConfig

if TYPE_CHECKING:
    from pywats.core.config import APISettings

logger = logging.getLogger(__name__)


# ==============================================================================
# Settings Panel Base Classes
# ==============================================================================

class SettingsPanel(QWidget):
    """Base class for all settings panels."""
    
    # Signal emitted when settings change
    settings_changed = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._modified = False
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Override to set up the UI. Called during init."""
        pass
    
    def load_settings(self, config: Any) -> None:
        """Load settings from config into UI widgets."""
        raise NotImplementedError
    
    def save_settings(self, config: Any) -> None:
        """Save settings from UI widgets to config."""
        raise NotImplementedError
    
    def mark_modified(self) -> None:
        """Mark settings as modified."""
        self._modified = True
        self.settings_changed.emit()
    
    @property
    def is_modified(self) -> bool:
        return self._modified
    
    def clear_modified(self) -> None:
        self._modified = False
    
    def _create_scrollable_form(self) -> Tuple[QScrollArea, QFormLayout]:
        """Create a scrollable form layout."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QFormLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll.setWidget(container)
        return scroll, layout
    
    def _create_group(self, title: str) -> Tuple[QGroupBox, QFormLayout]:
        """Create a styled group box with form layout."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #f0a30a;
            }
        """)
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        return group, layout
    
    def _create_spinbox(self, min_val: int, max_val: int, suffix: str = "") -> QSpinBox:
        """Create a styled spin box."""
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSuffix(suffix)
        spin.setMinimumWidth(100)
        spin.valueChanged.connect(self.mark_modified)
        return spin
    
    def _create_checkbox(self, text: str = "") -> QCheckBox:
        """Create a styled checkbox."""
        check = QCheckBox(text)
        check.stateChanged.connect(self.mark_modified)
        return check
    
    def _create_lineedit(self, placeholder: str = "") -> QLineEdit:
        """Create a styled line edit."""
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(self.mark_modified)
        return edit
    
    def _create_combobox(self, items: List[str]) -> QComboBox:
        """Create a styled combo box."""
        combo = QComboBox()
        combo.addItems(items)
        combo.currentIndexChanged.connect(self.mark_modified)
        return combo
    
    def _create_description_label(self, text: str) -> QLabel:
        """Create a description label with muted styling."""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: #808080; font-size: 11px; margin-bottom: 5px;")
        return label


# ==============================================================================
# API Settings Panels
# ==============================================================================

class APIGeneralSettingsPanel(SettingsPanel):
    """General API settings panel."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("API General Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Configure general API behavior settings. These settings affect all API operations."
        ))
        
        # Connection group
        conn_group, conn_layout = self._create_group("Connection")
        
        self.timeout_spin = self._create_spinbox(5, 300, " seconds")
        conn_layout.addRow("Request Timeout:", self.timeout_spin)
        conn_layout.addRow(self._create_description_label("Maximum time to wait for API responses"))
        
        self.max_retries_spin = self._create_spinbox(0, 10)
        conn_layout.addRow("Max Retries:", self.max_retries_spin)
        conn_layout.addRow(self._create_description_label("Number of retry attempts on failure"))
        
        self.retry_delay_spin = self._create_spinbox(1, 60, " seconds")
        conn_layout.addRow("Retry Delay:", self.retry_delay_spin)
        
        form_layout.addRow(conn_group)
        
        # Error Handling group
        error_group, error_layout = self._create_group("Error Handling")
        
        self.error_mode_combo = self._create_combobox(["Strict", "Lenient"])
        error_layout.addRow("Error Mode:", self.error_mode_combo)
        error_layout.addRow(self._create_description_label(
            "Strict: Raise exceptions on ambiguous responses. "
            "Lenient: Try to continue with best-effort handling."
        ))
        
        form_layout.addRow(error_group)
        
        # Logging group
        log_group, log_layout = self._create_group("API Logging")
        
        self.log_requests_check = self._create_checkbox("Log API requests")
        log_layout.addRow(self.log_requests_check)
        
        self.log_responses_check = self._create_checkbox("Log API responses")
        log_layout.addRow(self.log_responses_check)
        
        form_layout.addRow(log_group)
        
        # SSL group
        ssl_group, ssl_layout = self._create_group("Security")
        
        self.verify_ssl_check = self._create_checkbox("Verify SSL certificates")
        ssl_layout.addRow(self.verify_ssl_check)
        ssl_layout.addRow(self._create_description_label(
            "Disable only for testing with self-signed certificates"
        ))
        
        form_layout.addRow(ssl_group)
        
        # Add stretch to push content up
        form_layout.addRow(QWidget())
        
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: Any) -> None:
        """Load from APISettings."""
        self.timeout_spin.setValue(config.timeout_seconds)
        self.max_retries_spin.setValue(config.max_retries)
        self.retry_delay_spin.setValue(config.retry_delay_seconds)
        self.error_mode_combo.setCurrentText(config.error_mode.capitalize())
        self.log_requests_check.setChecked(config.log_requests)
        self.log_responses_check.setChecked(config.log_responses)
        self.verify_ssl_check.setChecked(config.verify_ssl)
        self.clear_modified()
    
    def save_settings(self, config: Any) -> None:
        """Save to APISettings."""
        config.timeout_seconds = self.timeout_spin.value()
        config.max_retries = self.max_retries_spin.value()
        config.retry_delay_seconds = self.retry_delay_spin.value()
        config.error_mode = self.error_mode_combo.currentText().lower()
        config.log_requests = self.log_requests_check.isChecked()
        config.log_responses = self.log_responses_check.isChecked()
        config.verify_ssl = self.verify_ssl_check.isChecked()


class DomainSettingsPanel(SettingsPanel):
    """Base panel for domain-specific settings."""
    
    domain_name: str = "Domain"
    domain_description: str = ""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, self.form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel(f"{self.domain_name} Domain Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        self.form_layout.addRow(header)
        
        if self.domain_description:
            self.form_layout.addRow(self._create_description_label(self.domain_description))
        
        # Base domain settings
        base_group, base_layout = self._create_group("General")
        
        self.enabled_check = self._create_checkbox("Enable domain")
        base_layout.addRow(self.enabled_check)
        
        self.cache_enabled_check = self._create_checkbox("Enable caching")
        base_layout.addRow(self.cache_enabled_check)
        
        self.cache_ttl_spin = self._create_spinbox(0, 3600, " seconds")
        base_layout.addRow("Cache TTL:", self.cache_ttl_spin)
        
        self.form_layout.addRow(base_group)
        
        # Add domain-specific settings
        self.setup_domain_specific_ui()
        
        # Add stretch
        self.form_layout.addRow(QWidget())
        
        main_layout.addWidget(scroll)
    
    def setup_domain_specific_ui(self) -> None:
        """Override to add domain-specific settings."""
        pass
    
    def load_settings(self, config: Any) -> None:
        """Load from domain settings."""
        self.enabled_check.setChecked(config.enabled)
        self.cache_enabled_check.setChecked(config.cache_enabled)
        self.cache_ttl_spin.setValue(config.cache_ttl_seconds)
        self.load_domain_specific_settings(config)
        self.clear_modified()
    
    def save_settings(self, config: Any) -> None:
        """Save to domain settings."""
        config.enabled = self.enabled_check.isChecked()
        config.cache_enabled = self.cache_enabled_check.isChecked()
        config.cache_ttl_seconds = self.cache_ttl_spin.value()
        self.save_domain_specific_settings(config)
    
    def load_domain_specific_settings(self, config: Any) -> None:
        """Override to load domain-specific settings."""
        pass
    
    def save_domain_specific_settings(self, config: Any) -> None:
        """Override to save domain-specific settings."""
        pass


class ProductDomainPanel(DomainSettingsPanel):
    """Product domain settings."""
    domain_name = "Product"
    domain_description = "Configure settings for product management operations."
    
    def setup_domain_specific_ui(self) -> None:
        group, layout = self._create_group("Product Settings")
        
        self.auto_create_check = self._create_checkbox("Auto-create products")
        layout.addRow(self.auto_create_check)
        layout.addRow(self._create_description_label(
            "Automatically create products if they don't exist"
        ))
        
        self.default_revision_edit = self._create_lineedit("A")
        layout.addRow("Default Revision:", self.default_revision_edit)
        
        self.form_layout.addRow(group)
    
    def load_domain_specific_settings(self, config: Any) -> None:
        self.auto_create_check.setChecked(config.auto_create_products)
        self.default_revision_edit.setText(config.default_revision)
    
    def save_domain_specific_settings(self, config: Any) -> None:
        config.auto_create_products = self.auto_create_check.isChecked()
        config.default_revision = self.default_revision_edit.text()


class ReportDomainPanel(DomainSettingsPanel):
    """Report domain settings."""
    domain_name = "Report"
    domain_description = "Configure settings for test report submissions."
    
    def setup_domain_specific_ui(self) -> None:
        group, layout = self._create_group("Report Settings")
        
        self.auto_submit_check = self._create_checkbox("Auto-submit reports")
        layout.addRow(self.auto_submit_check)
        
        self.validate_check = self._create_checkbox("Validate before submit")
        layout.addRow(self.validate_check)
        layout.addRow(self._create_description_label(
            "Validate report data before submission"
        ))
        
        self.include_attachments_check = self._create_checkbox("Include attachments")
        layout.addRow(self.include_attachments_check)
        
        self.max_attachment_spin = self._create_spinbox(1, 100, " MB")
        layout.addRow("Max Attachment Size:", self.max_attachment_spin)
        
        self.form_layout.addRow(group)
    
    def load_domain_specific_settings(self, config: Any) -> None:
        self.auto_submit_check.setChecked(config.auto_submit)
        self.validate_check.setChecked(config.validate_before_submit)
        self.include_attachments_check.setChecked(config.include_attachments)
        self.max_attachment_spin.setValue(config.max_attachment_size_mb)
    
    def save_domain_specific_settings(self, config: Any) -> None:
        config.auto_submit = self.auto_submit_check.isChecked()
        config.validate_before_submit = self.validate_check.isChecked()
        config.include_attachments = self.include_attachments_check.isChecked()
        config.max_attachment_size_mb = self.max_attachment_spin.value()


class ProductionDomainPanel(DomainSettingsPanel):
    """Production domain settings."""
    domain_name = "Production"
    domain_description = "Configure settings for production and serial number operations."
    
    def setup_domain_specific_ui(self) -> None:
        group, layout = self._create_group("Production Settings")
        
        self.auto_reserve_check = self._create_checkbox("Auto-reserve serials")
        layout.addRow(self.auto_reserve_check)
        layout.addRow(self._create_description_label(
            "Automatically reserve serial numbers when needed"
        ))
        
        self.reserve_count_spin = self._create_spinbox(1, 100)
        layout.addRow("Reserve Count:", self.reserve_count_spin)
        layout.addRow(self._create_description_label(
            "Number of serials to reserve at a time"
        ))
        
        self.validate_format_check = self._create_checkbox("Validate serial format")
        layout.addRow(self.validate_format_check)
        
        self.form_layout.addRow(group)
    
    def load_domain_specific_settings(self, config: Any) -> None:
        self.auto_reserve_check.setChecked(config.auto_reserve_serials)
        self.reserve_count_spin.setValue(config.serial_reserve_count)
        self.validate_format_check.setChecked(config.validate_serial_format)
    
    def save_domain_specific_settings(self, config: Any) -> None:
        config.auto_reserve_serials = self.auto_reserve_check.isChecked()
        config.serial_reserve_count = self.reserve_count_spin.value()
        config.validate_serial_format = self.validate_format_check.isChecked()


class ProcessDomainPanel(DomainSettingsPanel):
    """Process domain settings."""
    domain_name = "Process"
    domain_description = "Configure settings for process code management."
    
    def setup_domain_specific_ui(self) -> None:
        group, layout = self._create_group("Process Settings")
        
        self.auto_refresh_check = self._create_checkbox("Auto-refresh")
        layout.addRow(self.auto_refresh_check)
        layout.addRow(self._create_description_label(
            "Automatically refresh process code list"
        ))
        
        self.refresh_interval_spin = self._create_spinbox(60, 3600, " seconds")
        layout.addRow("Refresh Interval:", self.refresh_interval_spin)
        
        self.form_layout.addRow(group)
    
    def load_domain_specific_settings(self, config: Any) -> None:
        self.auto_refresh_check.setChecked(config.auto_refresh)
        self.refresh_interval_spin.setValue(config.refresh_interval_seconds)
    
    def save_domain_specific_settings(self, config: Any) -> None:
        config.auto_refresh = self.auto_refresh_check.isChecked()
        config.refresh_interval_seconds = self.refresh_interval_spin.value()


class SoftwareDomainPanel(DomainSettingsPanel):
    """Software domain settings."""
    domain_name = "Software"
    domain_description = "Configure settings for software download operations."
    
    def setup_domain_specific_ui(self) -> None:
        group, layout = self._create_group("Software Settings")
        
        self.auto_download_check = self._create_checkbox("Auto-download")
        layout.addRow(self.auto_download_check)
        layout.addRow(self._create_description_label(
            "Automatically download software when available"
        ))
        
        self.download_path_edit = self._create_lineedit("./downloads")
        layout.addRow("Download Path:", self.download_path_edit)
        
        self.form_layout.addRow(group)
    
    def load_domain_specific_settings(self, config: Any) -> None:
        self.auto_download_check.setChecked(config.auto_download)
        self.download_path_edit.setText(config.download_path)
    
    def save_domain_specific_settings(self, config: Any) -> None:
        config.auto_download = self.auto_download_check.isChecked()
        config.download_path = self.download_path_edit.text()


class AssetDomainPanel(DomainSettingsPanel):
    """Asset domain settings."""
    domain_name = "Asset"
    domain_description = "Configure settings for asset management operations."


class RootCauseDomainPanel(DomainSettingsPanel):
    """RootCause domain settings."""
    domain_name = "Root Cause"
    domain_description = "Configure settings for root cause analysis operations."


class AppDomainPanel(DomainSettingsPanel):
    """App/Statistics domain settings."""
    domain_name = "Statistics"
    domain_description = "Configure settings for statistics and app data retrieval."


# ==============================================================================
# Client Settings Panels
# ==============================================================================

class ClientConnectionPanel(SettingsPanel):
    """Client connection settings."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Connection Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Configure the connection to the WATS server."
        ))
        
        # Server group
        server_group, server_layout = self._create_group("Server")
        
        self.server_address_edit = self._create_lineedit("https://wats.example.com")
        server_layout.addRow("Server Address:", self.server_address_edit)
        
        self.api_token_edit = self._create_lineedit("API Token")
        self.api_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        server_layout.addRow("API Token:", self.api_token_edit)
        
        form_layout.addRow(server_group)
        
        # Instance group
        instance_group, instance_layout = self._create_group("Instance")
        
        self.instance_id_edit = self._create_lineedit("Instance ID")
        instance_layout.addRow("Instance ID:", self.instance_id_edit)
        
        form_layout.addRow(instance_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: ClientConfig) -> None:
        self.server_address_edit.setText(config.service_address or "")
        self.api_token_edit.setText(config.api_token or "")
        self.instance_id_edit.setText(config.instance_id or "")
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        config.service_address = self.server_address_edit.text()
        config.api_token = self.api_token_edit.text()
        config.instance_id = self.instance_id_edit.text()


class ClientProxyPanel(SettingsPanel):
    """Client proxy settings - full configuration matching WATS Client design."""
    
    def setup_ui(self) -> None:
        from PySide6.QtWidgets import QRadioButton, QButtonGroup
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Proxy Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Configure proxy settings for server connections."
        ))
        
        # Proxy mode selection
        mode_group, mode_layout = self._create_group("Proxy Mode")
        
        self._proxy_mode_group = QButtonGroup(self)
        
        self.no_proxy_radio = QRadioButton("No proxy")
        self.system_proxy_radio = QRadioButton("Use system proxy settings")
        self.manual_proxy_radio = QRadioButton("Manual proxy configuration")
        
        self._proxy_mode_group.addButton(self.no_proxy_radio, 0)
        self._proxy_mode_group.addButton(self.system_proxy_radio, 1)
        self._proxy_mode_group.addButton(self.manual_proxy_radio, 2)
        
        mode_layout.addRow(self.no_proxy_radio)
        mode_layout.addRow(self.system_proxy_radio)
        mode_layout.addRow(self.manual_proxy_radio)
        
        self._proxy_mode_group.buttonToggled.connect(self._on_proxy_mode_changed)
        
        form_layout.addRow(mode_group)
        
        # Manual proxy settings group
        self.manual_group, manual_layout = self._create_group("Manual Proxy Settings")
        
        self.proxy_host_edit = self._create_lineedit("proxy.example.com")
        manual_layout.addRow("Proxy Host:", self.proxy_host_edit)
        
        self.proxy_port_spin = self._create_spinbox(1, 65535)
        self.proxy_port_spin.setValue(8080)
        manual_layout.addRow("Proxy Port:", self.proxy_port_spin)
        
        # Authentication
        self.auth_check = self._create_checkbox("Proxy requires authentication")
        self.auth_check.stateChanged.connect(self._on_auth_toggled)
        manual_layout.addRow(self.auth_check)
        
        self.proxy_user_edit = self._create_lineedit("Username")
        manual_layout.addRow("Username:", self.proxy_user_edit)
        
        self.proxy_pass_edit = self._create_lineedit("Password")
        self.proxy_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        manual_layout.addRow("Password:", self.proxy_pass_edit)
        
        form_layout.addRow(self.manual_group)
        
        # Bypass list
        self.bypass_group, bypass_layout = self._create_group("Bypass Proxy")
        
        self.bypass_edit = self._create_lineedit("localhost, 127.0.0.1, *.local")
        bypass_layout.addRow("Bypass List:", self.bypass_edit)
        bypass_layout.addRow(self._create_description_label(
            "Comma-separated list of hosts that should bypass the proxy"
        ))
        
        form_layout.addRow(self.bypass_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
        
        # Set initial state
        self.system_proxy_radio.setChecked(True)
        self._update_manual_group_state()
        self._on_auth_toggled()
    
    def _on_proxy_mode_changed(self) -> None:
        """Handle proxy mode selection change."""
        self._update_manual_group_state()
        self.mark_modified()
    
    def _update_manual_group_state(self) -> None:
        """Enable/disable manual proxy settings based on mode."""
        is_manual = self.manual_proxy_radio.isChecked()
        self.manual_group.setEnabled(is_manual)
        self.bypass_group.setEnabled(is_manual)
    
    def _on_auth_toggled(self) -> None:
        """Enable/disable authentication fields."""
        checked = self.auth_check.isChecked()
        self.proxy_user_edit.setEnabled(checked)
        self.proxy_pass_edit.setEnabled(checked)
    
    def load_settings(self, config: ClientConfig) -> None:
        mode = getattr(config, 'proxy_mode', 'system')
        if mode == "none":
            self.no_proxy_radio.setChecked(True)
        elif mode == "system":
            self.system_proxy_radio.setChecked(True)
        else:
            self.manual_proxy_radio.setChecked(True)
        
        self.proxy_host_edit.setText(getattr(config, 'proxy_host', ''))
        self.proxy_port_spin.setValue(getattr(config, 'proxy_port', 8080))
        self.auth_check.setChecked(getattr(config, 'proxy_auth', False))
        self.proxy_user_edit.setText(getattr(config, 'proxy_username', ''))
        self.proxy_pass_edit.setText(getattr(config, 'proxy_password', ''))
        self.bypass_edit.setText(getattr(config, 'proxy_bypass', ''))
        
        self._update_manual_group_state()
        self._on_auth_toggled()
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        if self.no_proxy_radio.isChecked():
            config.proxy_mode = "none"
        elif self.system_proxy_radio.isChecked():
            config.proxy_mode = "system"
        else:
            config.proxy_mode = "manual"
        
        config.proxy_host = self.proxy_host_edit.text()
        config.proxy_port = self.proxy_port_spin.value()
        config.proxy_auth = self.auth_check.isChecked()
        config.proxy_username = self.proxy_user_edit.text()
        config.proxy_password = self.proxy_pass_edit.text()
        config.proxy_bypass = self.bypass_edit.text()


class ClientConverterPanel(SettingsPanel):
    """Client converter settings."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Converter Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Configure test report converter behavior."
        ))
        
        # Converter group
        conv_group, conv_layout = self._create_group("Conversion")
        
        self.converters_enabled_check = self._create_checkbox("Enable converters")
        conv_layout.addRow(self.converters_enabled_check)
        conv_layout.addRow(self._create_description_label(
            "Enable automatic conversion of test files"
        ))
        
        self.converters_folder_edit = self._create_lineedit("converters")
        conv_layout.addRow("Converters Folder:", self.converters_folder_edit)
        conv_layout.addRow(self._create_description_label(
            "Folder containing converter scripts"
        ))
        
        form_layout.addRow(conv_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: ClientConfig) -> None:
        self.converters_enabled_check.setChecked(config.converters_enabled)
        self.converters_folder_edit.setText(config.converters_folder)
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        config.converters_enabled = self.converters_enabled_check.isChecked()
        config.converters_folder = self.converters_folder_edit.text()


class ClientLocationPanel(SettingsPanel):
    """Client location services settings."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Location Services")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Configure location services for the WATS client."
        ))
        
        # Location Services group
        location_group, location_layout = self._create_group("Location Services")
        
        self.location_enabled_check = self._create_checkbox(
            "Allow this app to use location services"
        )
        location_layout.addRow(self.location_enabled_check)
        location_layout.addRow(self._create_description_label(
            "When enabled, the client can send location data with reports.\n"
            "This helps track where units are tested."
        ))
        
        form_layout.addRow(location_group)
        
        # Info section
        info_group, info_layout = self._create_group("Benefits")
        
        info_layout.addRow(self._create_description_label(
            "Location services allow the WATS client to include geographical\n"
            "coordinates when submitting test reports. This can help with:\n\n"
            "  • Tracking where units are manufactured or tested\n"
            "  • Identifying location-specific yield issues\n"
            "  • Compliance and traceability requirements"
        ))
        
        form_layout.addRow(info_group)
        
        # Privacy section
        privacy_group, privacy_layout = self._create_group("Privacy")
        
        privacy_layout.addRow(self._create_description_label(
            "When location services are enabled:\n\n"
            "  • Location data is only sent with test reports\n"
            "  • No background location tracking occurs\n"
            "  • Location accuracy depends on your network/GPS settings\n"
            "  • You can disable this at any time"
        ))
        
        form_layout.addRow(privacy_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: ClientConfig) -> None:
        self.location_enabled_check.setChecked(
            getattr(config, 'location_services_enabled', False)
        )
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        config.location_services_enabled = self.location_enabled_check.isChecked()


# ==============================================================================
# GUI Settings Panels
# ==============================================================================

class GUIStartupPanel(SettingsPanel):
    """GUI startup and window settings."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Startup & Window Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Configure application startup behavior and window settings."
        ))
        
        # Startup group
        startup_group, startup_layout = self._create_group("Startup")
        
        self.start_minimized_check = self._create_checkbox("Start minimized")
        startup_layout.addRow(self.start_minimized_check)
        startup_layout.addRow(self._create_description_label(
            "Start the application in minimized state"
        ))
        
        self.minimize_to_tray_check = self._create_checkbox("Minimize to system tray")
        startup_layout.addRow(self.minimize_to_tray_check)
        startup_layout.addRow(self._create_description_label(
            "Minimize to system tray instead of taskbar"
        ))
        
        form_layout.addRow(startup_group)
        
        # Instance group
        instance_group, instance_layout = self._create_group("Instance")
        
        self.instance_name_edit = self._create_lineedit("Client Instance Name")
        instance_layout.addRow("Instance Name:", self.instance_name_edit)
        instance_layout.addRow(self._create_description_label(
            "Display name for this client instance"
        ))
        
        form_layout.addRow(instance_group)
        
        # Logging group
        logging_group, logging_layout = self._create_group("Logging")
        
        self.log_level_combo = self._create_combobox(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("Log Level:", self.log_level_combo)
        logging_layout.addRow(self._create_description_label(
            "Minimum severity level for log messages"
        ))
        
        form_layout.addRow(logging_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: ClientConfig) -> None:
        self.start_minimized_check.setChecked(config.start_minimized)
        self.minimize_to_tray_check.setChecked(config.minimize_to_tray)
        self.instance_name_edit.setText(config.instance_name or "")
        index = self.log_level_combo.findText(config.log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        config.start_minimized = self.start_minimized_check.isChecked()
        config.minimize_to_tray = self.minimize_to_tray_check.isChecked()
        config.instance_name = self.instance_name_edit.text()
        config.log_level = self.log_level_combo.currentText()


class GUIAppearancePanel(SettingsPanel):
    """GUI appearance settings."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Appearance Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Customize the look and feel of the application."
        ))
        
        # Theme group
        theme_group, theme_layout = self._create_group("Theme")
        
        self.theme_combo = self._create_combobox(["Dark", "Light", "System"])
        theme_layout.addRow("Theme:", self.theme_combo)
        theme_layout.addRow(self._create_description_label(
            "Application color theme (restart required)"
        ))
        
        form_layout.addRow(theme_group)
        
        # Window group
        window_group, window_layout = self._create_group("Window")
        
        self.remember_size_check = self._create_checkbox("Remember window size")
        window_layout.addRow(self.remember_size_check)
        
        self.start_maximized_check = self._create_checkbox("Start maximized")
        window_layout.addRow(self.start_maximized_check)
        
        form_layout.addRow(window_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: ClientConfig) -> None:
        # These might need to be added to ClientConfig
        self.theme_combo.setCurrentText("Dark")
        self.remember_size_check.setChecked(True)
        self.start_maximized_check.setChecked(False)
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        # Save to config if fields exist
        pass


class GUITabsPanel(SettingsPanel):
    """GUI tabs visibility settings."""
    
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll, form_layout = self._create_scrollable_form()
        
        # Header
        header = QLabel("Tab Visibility Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0a30a;")
        form_layout.addRow(header)
        form_layout.addRow(self._create_description_label(
            "Control which tabs are visible in the main window sidebar."
        ))
        
        # Tabs group
        tabs_group, tabs_layout = self._create_group("Visible Tabs")
        
        self.show_location_check = self._create_checkbox("Location")
        tabs_layout.addRow(self.show_location_check)
        tabs_layout.addRow(self._create_description_label("Station location settings"))
        
        self.show_converters_check = self._create_checkbox("Converters")
        tabs_layout.addRow(self.show_converters_check)
        tabs_layout.addRow(self._create_description_label("Test report converter management"))
        
        self.show_sn_handler_check = self._create_checkbox("SN Handler")
        tabs_layout.addRow(self.show_sn_handler_check)
        tabs_layout.addRow(self._create_description_label("Serial number configuration"))
        
        self.show_proxy_check = self._create_checkbox("Proxy Settings")
        tabs_layout.addRow(self.show_proxy_check)
        tabs_layout.addRow(self._create_description_label("Network proxy configuration"))
        
        self.show_software_check = self._create_checkbox("Software")
        tabs_layout.addRow(self.show_software_check)
        tabs_layout.addRow(self._create_description_label("Software distribution and updates"))
        
        self.show_asset_check = self._create_checkbox("Assets")
        tabs_layout.addRow(self.show_asset_check)
        tabs_layout.addRow(self._create_description_label("Asset management and tracking"))
        
        self.show_rootcause_check = self._create_checkbox("RootCause")
        tabs_layout.addRow(self.show_rootcause_check)
        tabs_layout.addRow(self._create_description_label("Root cause analysis and tracking"))
        
        self.show_production_check = self._create_checkbox("Production")
        tabs_layout.addRow(self.show_production_check)
        tabs_layout.addRow(self._create_description_label("Production and manufacturing data"))
        
        self.show_product_check = self._create_checkbox("Products")
        tabs_layout.addRow(self.show_product_check)
        tabs_layout.addRow(self._create_description_label("Product and revision management"))
        
        # Note about restart
        restart_note = self._create_description_label(
            "Note: Changes to tab visibility require an application restart to take effect."
        )
        restart_note.setStyleSheet("color: #f0a30a; font-size: 11px; margin-top: 10px;")
        tabs_layout.addRow(restart_note)
        
        form_layout.addRow(tabs_group)
        
        form_layout.addRow(QWidget())
        main_layout.addWidget(scroll)
    
    def load_settings(self, config: ClientConfig) -> None:
        self.show_location_check.setChecked(config.show_location_tab)
        self.show_converters_check.setChecked(config.show_converters_tab)
        self.show_sn_handler_check.setChecked(config.show_sn_handler_tab)
        self.show_proxy_check.setChecked(config.show_proxy_tab)
        self.show_software_check.setChecked(config.show_software_tab)
        self.show_asset_check.setChecked(config.show_asset_tab)
        self.show_rootcause_check.setChecked(config.show_rootcause_tab)
        self.show_production_check.setChecked(config.show_production_tab)
        self.show_product_check.setChecked(config.show_product_tab)
        self.clear_modified()
    
    def save_settings(self, config: ClientConfig) -> None:
        config.show_location_tab = self.show_location_check.isChecked()
        config.show_converters_tab = self.show_converters_check.isChecked()
        config.show_sn_handler_tab = self.show_sn_handler_check.isChecked()
        config.show_proxy_tab = self.show_proxy_check.isChecked()
        config.show_software_tab = self.show_software_check.isChecked()
        config.show_asset_tab = self.show_asset_check.isChecked()
        config.show_rootcause_tab = self.show_rootcause_check.isChecked()
        config.show_production_tab = self.show_production_check.isChecked()
        config.show_product_tab = self.show_product_check.isChecked()


# ==============================================================================
# Main Settings Dialog
# ==============================================================================

class SettingsDialog(QDialog):
    """
    Settings dialog with TreeView navigation.
    
    Provides a VS Code-style settings interface with hierarchical navigation
    through API, Client, and GUI settings categories.
    """
    
    settings_changed = Signal()
    
    def __init__(
        self,
        client_config: ClientConfig,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.client_config = client_config
        self._api_config: Optional["APISettings"] = None
        self._panels: Dict[str, SettingsPanel] = {}
        self._modified = False
        
        self.setWindowTitle("Settings")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        self._setup_ui()
        self._load_all_settings()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)
        
        # Tree navigation
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(220)
        self.tree.setMaximumWidth(300)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                border: none;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 8px 10px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #37373d;
                color: #f0a30a;
            }
        """)
        self.tree.currentItemChanged.connect(self._on_tree_selection_changed)
        
        # Content stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background-color: #1e1e1e;
            }
        """)
        
        # Build tree and panels
        self._build_tree_and_panels()
        
        splitter.addWidget(self.tree)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Button bar
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)
        
        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Apply button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        button_layout.addWidget(self.apply_btn)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._on_ok_clicked)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        # Button container
        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setStyleSheet("""
            QWidget {
                background-color: #252526;
                border-top: 1px solid #3c3c3c;
            }
            QPushButton {
                padding: 6px 16px;
                min-width: 80px;
            }
        """)
        
        layout.addWidget(button_container)
        
        # Select first item
        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            if first_item is not None:
                if first_item.childCount() > 0:
                    first_child = first_item.child(0)
                    if first_child is not None:
                        self.tree.setCurrentItem(first_child)
                else:
                    self.tree.setCurrentItem(first_item)
                first_item.setExpanded(True)
    
    def _build_tree_and_panels(self) -> None:
        """Build the navigation tree and corresponding panels."""
        
        # API Settings
        api_item = QTreeWidgetItem(["API Settings"])
        api_item.setExpanded(True)
        font = api_item.font(0)
        font.setBold(True)
        api_item.setFont(0, font)
        self.tree.addTopLevelItem(api_item)
        
        # API General
        api_general_item = QTreeWidgetItem(["General"])
        api_item.addChild(api_general_item)
        api_general_panel = APIGeneralSettingsPanel()
        api_general_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("api_general", api_general_item, api_general_panel)
        
        # Domain settings
        domains = [
            ("Product", "product", ProductDomainPanel),
            ("Report", "report", ReportDomainPanel),
            ("Production", "production", ProductionDomainPanel),
            ("Process", "process", ProcessDomainPanel),
            ("Software", "software", SoftwareDomainPanel),
            ("Asset", "asset", AssetDomainPanel),
            ("Root Cause", "rootcause", RootCauseDomainPanel),
            ("Statistics", "app", AppDomainPanel),
        ]
        
        domains_item = QTreeWidgetItem(["Domains"])
        api_item.addChild(domains_item)
        
        for name, key, panel_class in domains:
            item = QTreeWidgetItem([name])
            domains_item.addChild(item)
            panel = panel_class()
            panel.settings_changed.connect(self._on_panel_modified)
            self._add_panel(f"domain_{key}", item, panel)
        
        # Client Settings
        client_item = QTreeWidgetItem(["Client Settings"])
        font = client_item.font(0)
        font.setBold(True)
        client_item.setFont(0, font)
        self.tree.addTopLevelItem(client_item)
        
        # Client Connection
        conn_item = QTreeWidgetItem(["Connection"])
        client_item.addChild(conn_item)
        conn_panel = ClientConnectionPanel()
        conn_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("client_connection", conn_item, conn_panel)
        
        # Client Proxy
        proxy_item = QTreeWidgetItem(["Proxy"])
        client_item.addChild(proxy_item)
        proxy_panel = ClientProxyPanel()
        proxy_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("client_proxy", proxy_item, proxy_panel)
        
        # Client Converter
        conv_item = QTreeWidgetItem(["Converter"])
        client_item.addChild(conv_item)
        conv_panel = ClientConverterPanel()
        conv_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("client_converter", conv_item, conv_panel)
        
        # Client Location
        location_item = QTreeWidgetItem(["Location"])
        client_item.addChild(location_item)
        location_panel = ClientLocationPanel()
        location_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("client_location", location_item, location_panel)
        
        # GUI Settings
        gui_item = QTreeWidgetItem(["GUI Settings"])
        font = gui_item.font(0)
        font.setBold(True)
        gui_item.setFont(0, font)
        self.tree.addTopLevelItem(gui_item)
        
        # GUI Startup & Window
        startup_item = QTreeWidgetItem(["Startup"])
        gui_item.addChild(startup_item)
        startup_panel = GUIStartupPanel()
        startup_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("gui_startup", startup_item, startup_panel)
        
        # GUI Appearance
        appearance_item = QTreeWidgetItem(["Appearance"])
        gui_item.addChild(appearance_item)
        appearance_panel = GUIAppearancePanel()
        appearance_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("gui_appearance", appearance_item, appearance_panel)
        
        # GUI Tabs
        tabs_item = QTreeWidgetItem(["Visible Tabs"])
        gui_item.addChild(tabs_item)
        tabs_panel = GUITabsPanel()
        tabs_panel.settings_changed.connect(self._on_panel_modified)
        self._add_panel("gui_tabs", tabs_item, tabs_panel)
        
        # Expand all top-level items
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is not None:
                item.setExpanded(True)
    
    def _add_panel(self, key: str, tree_item: QTreeWidgetItem, panel: SettingsPanel) -> None:
        """Add a panel to the stack and map it to a tree item."""
        index = self.stack.addWidget(panel)
        tree_item.setData(0, Qt.ItemDataRole.UserRole, key)
        self._panels[key] = panel
    
    def _on_tree_selection_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem) -> None:
        """Handle tree selection change."""
        if current is None:
            return
        
        key = current.data(0, Qt.ItemDataRole.UserRole)
        if key and key in self._panels:
            panel = self._panels[key]
            self.stack.setCurrentWidget(panel)
        elif current.childCount() > 0:
            # Select first child if parent is selected
            self.tree.setCurrentItem(current.child(0))
    
    def _on_panel_modified(self) -> None:
        """Handle panel modification."""
        self._modified = True
        self.apply_btn.setEnabled(True)
    
    def _load_all_settings(self) -> None:
        """Load all settings into panels."""
        # Load API settings
        try:
            from pywats.core.config import get_api_settings
            self._api_config = get_api_settings()
        except ImportError:
            # Create default if import fails
            from pywats.core.config import APISettings
            self._api_config = APISettings()
        
        # Load API general
        if "api_general" in self._panels:
            self._panels["api_general"].load_settings(self._api_config)
        
        # Load domain settings
        domain_map = {
            "domain_product": "product",
            "domain_report": "report",
            "domain_production": "production",
            "domain_process": "process",
            "domain_software": "software",
            "domain_asset": "asset",
            "domain_rootcause": "rootcause",
            "domain_app": "app",
        }
        
        for panel_key, domain_attr in domain_map.items():
            if panel_key in self._panels:
                domain_config = getattr(self._api_config, domain_attr, None)
                if domain_config:
                    self._panels[panel_key].load_settings(domain_config)
        
        # Load client settings
        if "client_connection" in self._panels:
            self._panels["client_connection"].load_settings(self.client_config)
        if "client_proxy" in self._panels:
            self._panels["client_proxy"].load_settings(self.client_config)
        if "client_converter" in self._panels:
            self._panels["client_converter"].load_settings(self.client_config)
        if "client_location" in self._panels:
            self._panels["client_location"].load_settings(self.client_config)
        
        # Load GUI settings
        if "gui_startup" in self._panels:
            self._panels["gui_startup"].load_settings(self.client_config)
        if "gui_appearance" in self._panels:
            self._panels["gui_appearance"].load_settings(self.client_config)
        if "gui_tabs" in self._panels:
            self._panels["gui_tabs"].load_settings(self.client_config)
        
        self._modified = False
        self.apply_btn.setEnabled(False)
    
    def _save_all_settings(self) -> None:
        """Save all settings from panels."""
        # Save API general
        if "api_general" in self._panels:
            self._panels["api_general"].save_settings(self._api_config)
        
        # Save domain settings
        domain_map = {
            "domain_product": "product",
            "domain_report": "report",
            "domain_production": "production",
            "domain_process": "process",
            "domain_software": "software",
            "domain_asset": "asset",
            "domain_rootcause": "rootcause",
            "domain_app": "app",
        }
        
        for panel_key, domain_attr in domain_map.items():
            if panel_key in self._panels:
                domain_config = getattr(self._api_config, domain_attr, None)
                if domain_config:
                    self._panels[panel_key].save_settings(domain_config)
        
        # Save API config to file
        try:
            from pywats.core.config import get_api_config_manager
            get_api_config_manager().save(self._api_config)
        except Exception as e:
            logger.error(f"Failed to save API config: {e}")
        
        # Save client settings
        if "client_connection" in self._panels:
            self._panels["client_connection"].save_settings(self.client_config)
        if "client_proxy" in self._panels:
            self._panels["client_proxy"].save_settings(self.client_config)
        if "client_converter" in self._panels:
            self._panels["client_converter"].save_settings(self.client_config)
        if "client_location" in self._panels:
            self._panels["client_location"].save_settings(self.client_config)
        
        # Save GUI settings
        if "gui_startup" in self._panels:
            self._panels["gui_startup"].save_settings(self.client_config)
        if "gui_appearance" in self._panels:
            self._panels["gui_appearance"].save_settings(self.client_config)
        if "gui_tabs" in self._panels:
            self._panels["gui_tabs"].save_settings(self.client_config)
        
        self._modified = False
        self.apply_btn.setEnabled(False)
        self.settings_changed.emit()
    
    def _on_apply_clicked(self) -> None:
        """Handle Apply button click."""
        self._save_all_settings()
    
    def _on_ok_clicked(self) -> None:
        """Handle OK button click."""
        self._save_all_settings()
        self.accept()
    
    def _on_reset_clicked(self) -> None:
        """Handle Reset button click."""
        result = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Reset API config
            try:
                from pywats.core.config import APISettings
                self._api_config = APISettings()
            except ImportError:
                pass
            
            # Reload all panels
            self._load_all_settings()
            self._modified = True
            self.apply_btn.setEnabled(True)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle dialog close."""
        if self._modified:
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if result == QMessageBox.StandardButton.Save:
                self._save_all_settings()
                event.accept()
            elif result == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
