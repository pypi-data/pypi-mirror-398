"""
Setup Page

Main setup page with:
- Client identification (instance name)
- Station configuration (name, location, purpose)
- Multi-station support (hub mode)
- Account/Server URL
- Token authentication
- Connect/Disconnect button
- Advanced options
"""

import socket
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QMessageBox, QComboBox,
    QGroupBox, QDialog, QListWidget, QListWidgetItem, QTextEdit,
    QSplitter, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from .base import BasePage
from ...core.config import ClientConfig, StationPreset

if TYPE_CHECKING:
    from ..main_window import MainWindow


class StationManagerDialog(QDialog):
    """Dialog for managing multiple station presets."""
    
    def __init__(self, config: ClientConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self._current_key: Optional[str] = None
        self._setup_ui()
        self._load_stations()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Station Manager")
        self.setMinimumSize(600, 400)
        self.resize(700, 450)
        
        layout = QVBoxLayout(self)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Station list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        list_label = QLabel("Stations")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)
        
        self._station_list = QListWidget()
        self._station_list.currentRowChanged.connect(self._on_station_selected)
        left_layout.addWidget(self._station_list, 1)
        
        # List buttons
        list_btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedWidth(30)
        self._add_btn.setToolTip("Add new station")
        self._add_btn.clicked.connect(self._on_add_station)
        list_btn_layout.addWidget(self._add_btn)
        
        self._remove_btn = QPushButton("-")
        self._remove_btn.setFixedWidth(30)
        self._remove_btn.setToolTip("Remove selected station")
        self._remove_btn.clicked.connect(self._on_remove_station)
        list_btn_layout.addWidget(self._remove_btn)
        
        list_btn_layout.addStretch()
        left_layout.addLayout(list_btn_layout)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Station details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        details_label = QLabel("Station Details")
        details_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(details_label)
        
        # Station form
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Key (read-only for existing)
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("Unique identifier")
        key_layout.addWidget(self._key_edit, 1)
        form_layout.addLayout(key_layout)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Station name for reports")
        name_layout.addWidget(self._name_edit, 1)
        form_layout.addLayout(name_layout)
        
        # Location
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(QLabel("Location:"))
        self._location_edit = QLineEdit()
        self._location_edit.setPlaceholderText("e.g., Building A, Floor 2")
        loc_layout.addWidget(self._location_edit, 1)
        form_layout.addLayout(loc_layout)
        
        # Purpose
        purpose_layout = QHBoxLayout()
        purpose_layout.addWidget(QLabel("Purpose:"))
        self._purpose_combo = QComboBox()
        self._purpose_combo.setEditable(True)
        self._purpose_combo.addItems(["Production", "Development", "Debug", "Verification", "Repair"])
        purpose_layout.addWidget(self._purpose_combo, 1)
        form_layout.addLayout(purpose_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Optional description...")
        self._description_edit.setMaximumHeight(80)
        desc_layout.addWidget(self._description_edit)
        form_layout.addLayout(desc_layout)
        
        # Default checkbox
        self._default_cb = QCheckBox("Set as default station")
        form_layout.addWidget(self._default_cb)
        
        # Apply button for current station
        self._apply_station_btn = QPushButton("Apply Changes")
        self._apply_station_btn.clicked.connect(self._on_apply_station)
        form_layout.addWidget(self._apply_station_btn)
        
        right_layout.addWidget(form_widget)
        right_layout.addStretch()
        
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter, 1)
        
        # Dialog buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
    
    def _load_stations(self) -> None:
        """Load stations from config into list."""
        self._station_list.clear()
        for preset in self.config.station_presets:
            item = QListWidgetItem(preset.name)
            item.setData(Qt.ItemDataRole.UserRole, preset.key)
            if preset.key == self.config.active_station_key:
                item.setText(f"► {preset.name}")
            self._station_list.addItem(item)
        
        if self._station_list.count() > 0:
            self._station_list.setCurrentRow(0)
        else:
            self._clear_form()
    
    def _clear_form(self) -> None:
        """Clear the station form."""
        self._current_key = None
        self._key_edit.clear()
        self._key_edit.setEnabled(True)
        self._name_edit.clear()
        self._location_edit.clear()
        self._purpose_combo.setCurrentText("Production")
        self._description_edit.clear()
        self._default_cb.setChecked(False)
    
    @Slot(int)
    def _on_station_selected(self, row: int) -> None:
        """Handle station selection."""
        if row < 0:
            self._clear_form()
            return
        
        item = self._station_list.item(row)
        key = item.data(Qt.ItemDataRole.UserRole)
        
        # Find preset
        for preset in self.config.station_presets:
            if preset.key == key:
                self._current_key = key
                self._key_edit.setText(preset.key)
                self._key_edit.setEnabled(False)  # Can't change key of existing
                self._name_edit.setText(preset.name)
                self._location_edit.setText(preset.location)
                self._purpose_combo.setCurrentText(preset.purpose)
                self._description_edit.setText(preset.description)
                self._default_cb.setChecked(preset.is_default)
                break
    
    @Slot()
    def _on_add_station(self) -> None:
        """Add a new station."""
        # Generate unique key
        base_key = "STATION"
        counter = 1
        while any(p.key == f"{base_key}-{counter}" for p in self.config.station_presets):
            counter += 1
        
        new_preset = StationPreset(
            key=f"{base_key}-{counter}",
            name=f"New Station {counter}",
            location="",
            purpose="Production",
            description="",
            is_default=len(self.config.station_presets) == 0
        )
        self.config.add_station_preset(new_preset)
        self._load_stations()
        
        # Select the new item
        for i in range(self._station_list.count()):
            item = self._station_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == new_preset.key:
                self._station_list.setCurrentRow(i)
                break
    
    @Slot()
    def _on_remove_station(self) -> None:
        """Remove selected station."""
        if self._current_key:
            reply = QMessageBox.question(
                self, "Remove Station",
                f"Remove station '{self._current_key}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.config.remove_station_preset(self._current_key)
                self._load_stations()
    
    @Slot()
    def _on_apply_station(self) -> None:
        """Apply changes to current station."""
        key = self._key_edit.text().strip()
        name = self._name_edit.text().strip()
        
        if not key or not name:
            QMessageBox.warning(self, "Validation Error", "Key and Name are required.")
            return
        
        # Update or create preset
        preset = StationPreset(
            key=key,
            name=name,
            location=self._location_edit.text().strip(),
            purpose=self._purpose_combo.currentText().strip(),
            description=self._description_edit.toPlainText().strip(),
            is_default=self._default_cb.isChecked()
        )
        
        # If setting as default, unset others
        if preset.is_default:
            for p in self.config.station_presets:
                p.is_default = False
        
        self.config.add_station_preset(preset)
        self._load_stations()
        
        # Re-select the current item
        for i in range(self._station_list.count()):
            item = self._station_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == key:
                self._station_list.setCurrentRow(i)
                break


class SetupPage(BasePage):
    """Setup/Connection settings page"""
    
    # Signal emitted when connection state changes
    connection_changed = Signal(bool)  # True = connected, False = disconnected
    # Signal emitted when station changes
    station_changed = Signal()
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._is_connected = False
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "General"
    
    def _setup_ui(self) -> None:
        """Setup page UI with station configuration"""
        # =========================================================================
        # Client Identification Section
        # =========================================================================
        client_group = QGroupBox("Client Identification")
        client_layout = QVBoxLayout(client_group)
        
        # Client name (the installation identity)
        client_name_layout = QHBoxLayout()
        client_name_label = QLabel("Client Name")
        client_name_label.setFixedWidth(120)
        client_name_layout.addWidget(client_name_label)
        
        self._client_name_edit = QLineEdit()
        self._client_name_edit.setPlaceholderText("e.g., Production Hub, Test Lab Client")
        self._client_name_edit.textChanged.connect(self._emit_changed)
        self._client_name_edit.setToolTip("Display name for this client installation")
        client_name_layout.addWidget(self._client_name_edit, 1)
        
        client_layout.addLayout(client_name_layout)
        
        # Client ID (read-only)
        client_id_layout = QHBoxLayout()
        client_id_label = QLabel("Client ID")
        client_id_label.setFixedWidth(120)
        client_id_layout.addWidget(client_id_label)
        
        self._client_id_edit = QLineEdit()
        self._client_id_edit.setReadOnly(True)
        self._client_id_edit.setStyleSheet("background-color: #3c3c3c;")
        self._client_id_edit.setToolTip("Unique identifier for this client instance")
        client_id_layout.addWidget(self._client_id_edit, 1)
        
        client_layout.addLayout(client_id_layout)
        
        self._layout.addWidget(client_group)
        self._layout.addSpacing(10)
        
        # =========================================================================
        # Station Configuration Section  
        # =========================================================================
        station_group = QGroupBox("Station Configuration")
        station_layout = QVBoxLayout(station_group)
        
        # Station name source selector
        source_layout = QHBoxLayout()
        source_label = QLabel("Station Name")
        source_label.setFixedWidth(120)
        source_layout.addWidget(source_label)
        
        self._station_name_edit = QLineEdit()
        self._station_name_edit.setPlaceholderText("Station name for reports")
        self._station_name_edit.textChanged.connect(self._emit_changed)
        self._station_name_edit.setToolTip("Station name that appears in test reports (machineName)")
        source_layout.addWidget(self._station_name_edit, 1)
        
        station_layout.addLayout(source_layout)
        
        # Use hostname checkbox
        hostname_layout = QHBoxLayout()
        hostname_layout.addSpacing(125)  # Align with fields
        
        self._use_hostname_cb = QCheckBox("Use computer hostname as station name")
        self._use_hostname_cb.stateChanged.connect(self._on_hostname_toggle)
        self._use_hostname_cb.setToolTip(f"Current hostname: {socket.gethostname().upper()}")
        hostname_layout.addWidget(self._use_hostname_cb)
        hostname_layout.addStretch()
        
        station_layout.addLayout(hostname_layout)
        
        station_layout.addSpacing(5)
        
        # Location
        location_layout = QHBoxLayout()
        location_label = QLabel("Location")
        location_label.setFixedWidth(120)
        location_layout.addWidget(location_label)
        
        self._location_edit = QLineEdit()
        self._location_edit.setPlaceholderText("e.g., Building A, Floor 2")
        self._location_edit.textChanged.connect(self._emit_changed)
        self._location_edit.setToolTip("Station location shown in reports and dashboards")
        location_layout.addWidget(self._location_edit, 1)
        
        station_layout.addLayout(location_layout)
        
        # Purpose
        purpose_layout = QHBoxLayout()
        purpose_label = QLabel("Purpose")
        purpose_label.setFixedWidth(120)
        purpose_layout.addWidget(purpose_label)
        
        self._purpose_combo = QComboBox()
        self._purpose_combo.setEditable(True)
        self._purpose_combo.addItems(["Production", "Development", "Debug", "Verification", "Repair"])
        self._purpose_combo.currentTextChanged.connect(self._emit_changed)
        self._purpose_combo.setToolTip("Station purpose shown in reports and dashboards")
        purpose_layout.addWidget(self._purpose_combo, 1)
        
        station_layout.addLayout(purpose_layout)
        
        self._layout.addWidget(station_group)
        self._layout.addSpacing(10)
        
        # =========================================================================
        # Multi-Station Mode Section
        # =========================================================================
        multi_group = QGroupBox("Multi-Station Mode (Hub)")
        multi_layout = QVBoxLayout(multi_group)
        
        # Enable multi-station
        self._multi_station_cb = QCheckBox("Enable multi-station mode")
        self._multi_station_cb.stateChanged.connect(self._on_multi_station_toggle)
        self._multi_station_cb.setToolTip(
            "Enable this client to manage multiple stations.\n"
            "Useful for database converters, centralized upload clients,\n"
            "or test cells with multiple fixtures."
        )
        multi_layout.addWidget(self._multi_station_cb)
        
        # Station selector (when multi-station enabled)
        self._station_selector_widget = QWidget()
        selector_layout = QHBoxLayout(self._station_selector_widget)
        selector_layout.setContentsMargins(0, 5, 0, 0)
        
        selector_label = QLabel("Active Station")
        selector_label.setFixedWidth(120)
        selector_layout.addWidget(selector_label)
        
        self._station_combo = QComboBox()
        self._station_combo.currentIndexChanged.connect(self._on_active_station_changed)
        self._station_combo.setToolTip("Select the active station for reports")
        selector_layout.addWidget(self._station_combo, 1)
        
        self._manage_stations_btn = QPushButton("Manage...")
        self._manage_stations_btn.setFixedWidth(80)
        self._manage_stations_btn.clicked.connect(self._on_manage_stations)
        self._manage_stations_btn.setToolTip("Open station manager dialog")
        selector_layout.addWidget(self._manage_stations_btn)
        
        multi_layout.addWidget(self._station_selector_widget)
        self._station_selector_widget.setVisible(False)
        
        self._layout.addWidget(multi_group)
        self._layout.addSpacing(10)
        
        # =========================================================================
        # Connection Status (read-only summary - full settings on Connection page)
        # =========================================================================
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        # Connected server display
        server_layout = QHBoxLayout()
        server_label = QLabel("Connected to")
        server_label.setFixedWidth(120)
        server_layout.addWidget(server_label)
        
        self._server_display = QLabel()
        self._server_display.setStyleSheet("color: #4ec9b0;")
        server_layout.addWidget(self._server_display, 1)
        status_layout.addLayout(server_layout)
        
        # Status display
        conn_status_layout = QHBoxLayout()
        conn_status_label = QLabel("Status")
        conn_status_label.setFixedWidth(120)
        conn_status_layout.addWidget(conn_status_label)
        
        self._connection_status = QLabel("Not connected")
        self._connection_status.setStyleSheet("color: #808080;")
        conn_status_layout.addWidget(self._connection_status, 1)
        status_layout.addLayout(conn_status_layout)
        
        # Info text
        info_label = QLabel("Go to Connection page for full connection settings.")
        info_label.setStyleSheet("color: #808080; font-size: 11px; font-style: italic;")
        status_layout.addWidget(info_label)
        
        self._layout.addWidget(status_group)
        self._layout.addSpacing(10)
        
        # =========================================================================
        # Advanced Options (collapsible)
        # =========================================================================
        self._create_advanced_section()
        
        # Add stretch to push content to top
        self._layout.addStretch()
    
    def _create_advanced_section(self) -> None:
        """Create advanced options section"""
        # Advanced options header (clickable)
        self._advanced_expanded = False
        
        advanced_header = QHBoxLayout()
        self._advanced_toggle = QLabel("▶ Advanced options")
        self._advanced_toggle.setStyleSheet("color: #cccccc; font-weight: bold;")
        self._advanced_toggle.mousePressEvent = lambda e: self._toggle_advanced()
        advanced_header.addWidget(self._advanced_toggle)
        advanced_header.addStretch()
        self._layout.addLayout(advanced_header)
        
        # Advanced options content
        self._advanced_frame = QFrame()
        self._advanced_frame.setVisible(False)
        advanced_layout = QVBoxLayout(self._advanced_frame)
        advanced_layout.setContentsMargins(20, 10, 0, 0)
        
        # Sync interval
        sync_layout = QHBoxLayout()
        sync_label = QLabel("Sync interval")
        sync_label.setFixedWidth(100)
        sync_layout.addWidget(sync_label)
        
        self._sync_edit = QLineEdit()
        self._sync_edit.setFixedWidth(80)
        self._sync_edit.textChanged.connect(self._emit_changed)
        sync_layout.addWidget(self._sync_edit)
        sync_layout.addWidget(QLabel("seconds"))
        sync_layout.addStretch()
        advanced_layout.addLayout(sync_layout)
        
        # Auto-start service
        self._auto_start_cb = QCheckBox("Start service automatically on login")
        self._auto_start_cb.stateChanged.connect(self._on_auto_start_changed)
        advanced_layout.addWidget(self._auto_start_cb)
        
        self._layout.addWidget(self._advanced_frame)
    
    def _on_auto_start_changed(self, state: int) -> None:
        """Handle auto-start checkbox change"""
        enabled = state == Qt.CheckState.Checked.value
        try:
            # Only available on Windows
            import sys
            if sys.platform == 'win32':
                from ...services.windows_service import set_auto_start
                success = set_auto_start(enabled)
                if not success:
                    # Revert checkbox if failed
                    self._auto_start_cb.blockSignals(True)
                    self._auto_start_cb.setChecked(not enabled)
                    self._auto_start_cb.blockSignals(False)
                    QMessageBox.warning(
                        self, "Error",
                        "Failed to update auto-start setting.\n"
                        "You may need to run as administrator."
                    )
        except ImportError:
            pass
        self._emit_changed()
    
    def _toggle_advanced(self) -> None:
        """Toggle advanced options visibility"""
        self._advanced_expanded = not self._advanced_expanded
        self._advanced_frame.setVisible(self._advanced_expanded)
        if self._advanced_expanded:
            self._advanced_toggle.setText("▼ Advanced options")
        else:
            self._advanced_toggle.setText("▶ Advanced options")
    
    @Slot(int)
    def _on_hostname_toggle(self, state: int) -> None:
        """Handle hostname checkbox toggle."""
        use_hostname = state == Qt.CheckState.Checked.value
        self._station_name_edit.setEnabled(not use_hostname)
        if use_hostname:
            self._station_name_edit.setText(socket.gethostname().upper())
            self._station_name_edit.setStyleSheet("background-color: #3c3c3c;")
            self.config.station_name_source = "hostname"
        else:
            self._station_name_edit.setStyleSheet("")
            self.config.station_name_source = "config"
        self._emit_changed()
    
    @Slot(int)
    def _on_multi_station_toggle(self, state: int) -> None:
        """Handle multi-station mode toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._station_selector_widget.setVisible(enabled)
        self.config.multi_station_enabled = enabled
        
        if enabled:
            self._refresh_station_combo()
        self._emit_changed()
    
    @Slot(int)
    def _on_active_station_changed(self, index: int) -> None:
        """Handle active station selection change."""
        if index >= 0:
            key = self._station_combo.itemData(index)
            if key:
                self.config.set_active_station(key)
                self.station_changed.emit()
                self._emit_changed()
    
    @Slot()
    def _on_manage_stations(self) -> None:
        """Open station manager dialog."""
        dialog = StationManagerDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_station_combo()
            self._emit_changed()
    
    def _refresh_station_combo(self) -> None:
        """Refresh the station selector combo box."""
        self._station_combo.blockSignals(True)
        self._station_combo.clear()
        
        for preset in self.config.station_presets:
            display = f"{preset.name}"
            if preset.location:
                display += f" ({preset.location})"
            self._station_combo.addItem(display, preset.key)
            
            if preset.key == self.config.active_station_key:
                self._station_combo.setCurrentIndex(self._station_combo.count() - 1)
        
        self._station_combo.blockSignals(False)
    
    def _set_fields_enabled(self, enabled: bool) -> None:
        """Enable or disable input fields (server and token always read-only)"""
        self._client_name_edit.setEnabled(enabled)
        self._station_name_edit.setEnabled(enabled and not self._use_hostname_cb.isChecked())
        self._use_hostname_cb.setEnabled(enabled)
        self._location_edit.setEnabled(enabled)
        self._purpose_combo.setEnabled(enabled)
        self._multi_station_cb.setEnabled(enabled)
        self._station_combo.setEnabled(enabled)
        self._manage_stations_btn.setEnabled(enabled)
        self._sync_edit.setEnabled(enabled)
        self._auto_start_cb.setEnabled(enabled)
    
    def set_connected(self, connected: bool) -> None:
        """Update UI for connected/disconnected state"""
        self._is_connected = connected
        self._set_fields_enabled(connected)
        
        # Update status display
        if connected:
            self._server_display.setText(self.config.service_address)
            self._connection_status.setText("Connected")
            self._connection_status.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        else:
            self._server_display.setText("")
            self._connection_status.setText("Not connected")
            self._connection_status.setStyleSheet("color: #808080;")
    
    @Slot()
    def _on_new_customer_clicked(self) -> None:
        """Open new customer registration page"""
        QDesktopServices.openUrl(QUrl("https://www.wats.com/register"))
    
    def save_config(self) -> None:
        """Save configuration"""
        # Client identification
        self.config.instance_name = self._client_name_edit.text().strip()
        
        # Station configuration
        if not self._use_hostname_cb.isChecked():
            self.config.station_name = self._station_name_edit.text().strip()
        else:
            self.config.station_name = ""  # Will use hostname
        
        self.config.station_name_source = "hostname" if self._use_hostname_cb.isChecked() else "config"
        self.config.location = self._location_edit.text().strip()
        self.config.purpose = self._purpose_combo.currentText().strip()
        
        # Multi-station mode
        self.config.multi_station_enabled = self._multi_station_cb.isChecked()
        
        # Advanced
        self.config.service_auto_start = self._auto_start_cb.isChecked()
        
        try:
            self.config.sync_interval_seconds = int(self._sync_edit.text())
        except (ValueError, TypeError):
            pass
        
        # Save to file
        if self.config._config_path:
            try:
                self.config.save()
            except Exception as e:
                print(f"Failed to save config: {e}")
    
    def load_config(self) -> None:
        """Load configuration"""
        # Client identification
        self._client_name_edit.setText(self.config.instance_name)
        self._client_id_edit.setText(self.config.formatted_identifier)
        
        # Station configuration
        use_hostname = self.config.station_name_source == "hostname"
        self._use_hostname_cb.blockSignals(True)
        self._use_hostname_cb.setChecked(use_hostname)
        self._use_hostname_cb.blockSignals(False)
        
        if use_hostname:
            self._station_name_edit.setText(socket.gethostname().upper())
            self._station_name_edit.setEnabled(False)
            self._station_name_edit.setStyleSheet("background-color: #3c3c3c;")
        else:
            self._station_name_edit.setText(self.config.station_name)
            self._station_name_edit.setEnabled(True)
            self._station_name_edit.setStyleSheet("")
        
        self._location_edit.setText(self.config.location)
        self._purpose_combo.setCurrentText(self.config.purpose or "Production")
        
        # Multi-station mode
        self._multi_station_cb.blockSignals(True)
        self._multi_station_cb.setChecked(self.config.multi_station_enabled)
        self._multi_station_cb.blockSignals(False)
        self._station_selector_widget.setVisible(self.config.multi_station_enabled)
        
        if self.config.multi_station_enabled:
            self._refresh_station_combo()
        
        # Connection status display
        if self.config.service_address:
            self._server_display.setText(self.config.service_address)
            self._connection_status.setText("Connected")
            self._connection_status.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        else:
            self._server_display.setText("Not configured")
            self._connection_status.setText("Not connected")
            self._connection_status.setStyleSheet("color: #808080;")
        
        # Advanced
        self._sync_edit.setText(str(self.config.sync_interval_seconds))
        
        # Check actual auto-start state from system (Windows only)
        auto_start_enabled = False
        try:
            import sys
            if sys.platform == 'win32':
                from ...services.windows_service import is_auto_start_enabled
                auto_start_enabled = is_auto_start_enabled()
        except ImportError:
            auto_start_enabled = getattr(self.config, 'service_auto_start', False)
        
        self._auto_start_cb.blockSignals(True)
        self._auto_start_cb.setChecked(auto_start_enabled)
        self._auto_start_cb.blockSignals(False)
        
        # Check if we should be connected (auto-connect on startup)
        if self.config.auto_connect and self.config.was_connected:
            if self.config.service_address and self.config.api_token:
                # Will be connected by main window
                pass
