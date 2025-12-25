"""
Asset Management Page

Manage test station assets - equipment, instruments, fixtures, and tools.
Tracks calibration, maintenance schedules, and usage limits.

Based on the WATS Asset Management API:
- GET /api/Asset - List all assets
- GET /api/Asset/{id} - Get asset details
- POST /api/Asset - Create/update asset
- DELETE /api/Asset - Delete asset
- GET /api/Asset/Status - Get asset status/alarms
- GET /api/Asset/Types - Get asset types
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QSpinBox, QDateEdit, QDialogButtonBox,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class AssetDialog(QDialog):
    """Dialog for creating/editing assets"""
    
    def __init__(
        self, 
        asset_types: List[Dict[str, Any]] = None,
        asset: Dict[str, Any] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.asset_types = asset_types or []
        self.asset = asset
        self._setup_ui()
        if asset:
            self._populate_data(asset)
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("Asset" if not self.asset else "Edit Asset")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(10)
        
        # Serial Number
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Required - unique identifier")
        form.addRow("Serial Number:", self.serial_edit)
        
        # Asset Type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Select Type...", None)
        for asset_type in self.asset_types:
            self.type_combo.addItem(
                asset_type.get("name", "Unknown"),
                asset_type.get("typeId")
            )
        form.addRow("Asset Type:", self.type_combo)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Display name")
        form.addRow("Name:", self.name_edit)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("Optional description")
        form.addRow("Description:", self.desc_edit)
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Physical location")
        form.addRow("Location:", self.location_edit)
        
        # Calibration Due
        self.cal_date = QDateEdit()
        self.cal_date.setCalendarPopup(True)
        self.cal_date.setDate(QDate.currentDate().addYears(1))
        form.addRow("Calibration Due:", self.cal_date)
        
        # Usage Limit
        self.usage_limit = QSpinBox()
        self.usage_limit.setRange(0, 1000000)
        self.usage_limit.setSpecialValueText("No limit")
        form.addRow("Usage Limit:", self.usage_limit)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _populate_data(self, asset: Dict[str, Any]) -> None:
        """Populate form with existing asset data"""
        self.serial_edit.setText(asset.get("serialNumber", ""))
        self.serial_edit.setEnabled(False)  # Can't change serial number
        
        self.name_edit.setText(asset.get("assetName", ""))
        self.desc_edit.setPlainText(asset.get("description", ""))
        self.location_edit.setText(asset.get("location", ""))
        
        # Set type
        type_id = asset.get("typeId")
        if type_id:
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == type_id:
                    self.type_combo.setCurrentIndex(i)
                    break
    
    def _validate_and_accept(self) -> None:
        """Validate input before accepting"""
        if not self.serial_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Serial number is required")
            return
        
        if self.type_combo.currentData() is None:
            QMessageBox.warning(self, "Validation Error", "Please select an asset type")
            return
        
        self.accept()
    
    def get_asset_data(self) -> Dict[str, Any]:
        """Get asset data from form"""
        data = {
            "serialNumber": self.serial_edit.text().strip(),
            "typeId": self.type_combo.currentData(),
            "assetName": self.name_edit.text().strip() or None,
            "description": self.desc_edit.toPlainText().strip() or None,
            "location": self.location_edit.text().strip() or None,
        }
        
        if self.usage_limit.value() > 0:
            data["usageLimit"] = self.usage_limit.value()
        
        return data


class AssetPage(BasePage):
    """Asset Management page - track equipment, calibration, maintenance"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._assets: List[Dict[str, Any]] = []
        self._asset_types: List[Dict[str, Any]] = []
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Assets"
    
    def _setup_ui(self) -> None:
        """Setup page UI for Asset Management"""
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self._refresh_btn = QPushButton("⟳ Refresh")
        self._refresh_btn.setToolTip("Refresh assets from server")
        self._refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self._refresh_btn)
        
        self._add_btn = QPushButton("+ Add Asset")
        self._add_btn.clicked.connect(self._on_add_asset)
        toolbar_layout.addWidget(self._add_btn)
        
        toolbar_layout.addStretch()
        
        # Search
        toolbar_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter by serial or name...")
        self._search_edit.setMaximumWidth(250)
        self._search_edit.textChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._search_edit)
        
        # Status filter
        toolbar_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "OK", "Needs Calibration", "Needs Maintenance", "In Alarm"])
        self._status_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._status_filter)
        
        self._layout.addLayout(toolbar_layout)
        
        # Main content - splitter with table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Assets table
        table_group = QGroupBox("Assets")
        table_layout = QVBoxLayout(table_group)
        
        self._assets_table = QTableWidget()
        self._assets_table.setColumnCount(6)
        self._assets_table.setHorizontalHeaderLabels([
            "Serial Number", "Name", "Type", "Location", "Status", "Next Cal"
        ])
        self._assets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._assets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._assets_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._assets_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._assets_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._assets_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._assets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._assets_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._assets_table.setAlternatingRowColors(True)
        self._assets_table.itemSelectionChanged.connect(self._on_selection_changed)
        self._assets_table.doubleClicked.connect(self._on_edit_asset)
        
        # Apply dark theme styling
        self._assets_table.setStyleSheet("""
            QTableWidget {
                font-size: 11pt;
                background-color: #1e1e1e;
                alternate-background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #3c3c3c;
                font-weight: bold;
            }
        """)
        table_layout.addWidget(self._assets_table)
        
        splitter.addWidget(table_group)
        
        # Details panel
        details_group = QGroupBox("Asset Details")
        details_layout = QVBoxLayout(details_group)
        
        self._details_label = QLabel("Select an asset to view details")
        self._details_label.setStyleSheet("color: #808080; font-style: italic;")
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_layout.addWidget(self._details_label)
        
        # Action buttons for selected asset
        action_layout = QHBoxLayout()
        
        self._edit_btn = QPushButton("✏️ Edit")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit_asset)
        action_layout.addWidget(self._edit_btn)
        
        self._status_btn = QPushButton("📊 Check Status")
        self._status_btn.setEnabled(False)
        self._status_btn.clicked.connect(self._on_check_status)
        action_layout.addWidget(self._status_btn)
        
        # Note: Delete functionality removed as assets should be managed via WATS web interface
        
        action_layout.addStretch()
        details_layout.addLayout(action_layout)
        
        splitter.addWidget(details_group)
        splitter.setSizes([400, 150])
        
        self._layout.addWidget(splitter, 1)
        
        # Status label
        self._status_label = QLabel("Connect to WATS server to view assets")
        self._status_label.setStyleSheet("color: #808080; font-style: italic;")
        self._layout.addWidget(self._status_label)
        
        # Auto-load if connected
        if self._main_window and self._main_window.app.wats_client:
            self._load_assets()
    
    def _on_selection_changed(self) -> None:
        """Handle asset selection change"""
        selected = len(self._assets_table.selectedItems()) > 0
        self._edit_btn.setEnabled(selected)
        self._status_btn.setEnabled(selected)
        
        if selected:
            row = self._assets_table.currentRow()
            if 0 <= row < len(self._assets):
                asset = self._assets[row]
                self._show_asset_details(asset)
        else:
            self._details_label.setText("Select an asset to view details")
    
    def _show_asset_details(self, asset: Dict[str, Any]) -> None:
        """Show asset details in details panel"""
        details = f"""
<b>Serial Number:</b> {asset.get('serialNumber', 'N/A')}<br>
<b>Name:</b> {asset.get('assetName', 'N/A')}<br>
<b>Type:</b> {asset.get('typeName', 'N/A')}<br>
<b>Location:</b> {asset.get('location', 'N/A')}<br>
<b>Description:</b> {asset.get('description', 'N/A')}<br>
<b>State:</b> {asset.get('state', 'N/A')}<br>
<b>Usage Count:</b> {asset.get('usageCount', 0)} / {asset.get('usageLimit', '∞')}<br>
<b>Created:</b> {asset.get('created', 'N/A')}<br>
"""
        self._details_label.setText(details)
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    
    def _on_filter_changed(self) -> None:
        """Handle filter changes"""
        self._populate_table()
    
    def _on_refresh(self) -> None:
        """Refresh assets from server"""
        if self._main_window and self._main_window.app.wats_client:
            self._load_assets()
        else:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
    
    def _load_assets(self) -> None:
        """Load assets from WATS server"""
        try:
            self._status_label.setText("Loading assets...")
            
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                
                # Load asset types first
                try:
                    self._asset_types = client.asset.get_asset_types() or []
                except Exception:
                    self._asset_types = []
                
                # Load assets
                assets = client.asset.get_assets()
                self._assets = [self._asset_to_dict(a) for a in assets] if assets else []
                
                self._populate_table()
                self._status_label.setText(f"Loaded {len(self._assets)} assets")
            else:
                self._status_label.setText("Not connected to WATS server")
        except Exception as e:
            self._status_label.setText(f"Error: {str(e)[:50]}")
            QMessageBox.warning(self, "Error", f"Failed to load assets: {e}")
    
    def _asset_to_dict(self, asset: Any) -> Dict[str, Any]:
        """Convert Asset model to dictionary"""
        if hasattr(asset, '__dict__'):
            return {
                'assetId': getattr(asset, 'asset_id', None),
                'serialNumber': getattr(asset, 'serial_number', ''),
                'assetName': getattr(asset, 'asset_name', ''),
                'typeName': getattr(asset, 'type_name', ''),
                'typeId': getattr(asset, 'type_id', None),
                'location': getattr(asset, 'location', ''),
                'description': getattr(asset, 'description', ''),
                'state': getattr(asset, 'state', ''),
                'usageCount': getattr(asset, 'usage_count', 0),
                'usageLimit': getattr(asset, 'usage_limit', None),
                'created': getattr(asset, 'created', ''),
                'nextCalibration': getattr(asset, 'next_calibration', None),
                'alarmState': getattr(asset, 'alarm_state', 'OK'),
            }
        return dict(asset) if isinstance(asset, dict) else {}
    
    def _populate_table(self) -> None:
        """Populate the assets table with filtered data"""
        self._assets_table.setRowCount(0)
        
        search_text = self._search_edit.text().lower()
        status_filter = self._status_filter.currentText()
        
        for asset in self._assets:
            # Apply search filter
            if search_text:
                serial = asset.get('serialNumber', '').lower()
                name = asset.get('assetName', '').lower()
                if search_text not in serial and search_text not in name:
                    continue
            
            # Apply status filter
            alarm_state = asset.get('alarmState', 'OK')
            if status_filter != "All":
                if status_filter == "OK" and alarm_state != "OK":
                    continue
                elif status_filter == "Needs Calibration" and "calibration" not in alarm_state.lower():
                    continue
                elif status_filter == "Needs Maintenance" and "maintenance" not in alarm_state.lower():
                    continue
                elif status_filter == "In Alarm" and alarm_state == "OK":
                    continue
            
            row = self._assets_table.rowCount()
            self._assets_table.insertRow(row)
            
            self._assets_table.setItem(row, 0, QTableWidgetItem(asset.get('serialNumber', '')))
            self._assets_table.setItem(row, 1, QTableWidgetItem(asset.get('assetName', '')))
            self._assets_table.setItem(row, 2, QTableWidgetItem(asset.get('typeName', '')))
            self._assets_table.setItem(row, 3, QTableWidgetItem(asset.get('location', '')))
            
            # Status with color coding
            status_item = QTableWidgetItem(alarm_state)
            if alarm_state == "OK":
                status_item.setForeground(QColor("#4CAF50"))  # Green
            elif "alarm" in alarm_state.lower():
                status_item.setForeground(QColor("#f44336"))  # Red
            else:
                status_item.setForeground(QColor("#FF9800"))  # Orange
            self._assets_table.setItem(row, 4, status_item)
            
            # Next calibration date
            next_cal = asset.get('nextCalibration', '')
            if next_cal:
                next_cal = str(next_cal)[:10]  # Just the date part
            self._assets_table.setItem(row, 5, QTableWidgetItem(next_cal))
    
    def _on_add_asset(self) -> None:
        """Show dialog to add new asset"""
        if not self._main_window or not self._main_window.app.wats_client:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
            return
        
        dialog = AssetDialog(self._asset_types, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_asset_data()
                client = self._main_window.app.wats_client
                
                result = client.asset.create_asset(
                    serial_number=data['serialNumber'],
                    type_id=data['typeId'],
                    asset_name=data.get('assetName'),
                    description=data.get('description'),
                    location=data.get('location'),
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Asset created successfully")
                    self._load_assets()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create asset")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create asset: {e}")
    
    def _on_edit_asset(self) -> None:
        """Edit selected asset"""
        row = self._assets_table.currentRow()
        if row < 0 or row >= len(self._assets):
            return
        
        asset = self._assets[row]
        dialog = AssetDialog(self._asset_types, asset=asset, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_asset_data()
                client = self._main_window.app.wats_client
                
                # First get the full asset object
                full_asset = client.asset.get_asset(serial_number=data['serialNumber'])
                
                if full_asset:
                    # Update the fields
                    full_asset.asset_name = data.get('assetName') or full_asset.asset_name
                    full_asset.description = data.get('description') or full_asset.description
                    full_asset.location = data.get('location') or full_asset.location
                    
                    # Update via API
                    result = client.asset.update_asset(full_asset)
                    
                    if result:
                        QMessageBox.information(self, "Success", "Asset updated successfully")
                        self._load_assets()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to update asset - no result returned")
                else:
                    QMessageBox.warning(self, "Error", f"Could not find asset with serial number: {data['serialNumber']}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update asset: {e}")
    
    def _on_check_status(self) -> None:
        """Check status of selected asset"""
        row = self._assets_table.currentRow()
        if row < 0 or row >= len(self._assets):
            return
        
        asset = self._assets[row]
        serial = asset.get('serialNumber')
        
        try:
            client = self._main_window.app.wats_client
            status = client.asset.get_status(serial_number=serial)
            
            if status:
                msg = f"Asset: {serial}\n\n"
                msg += f"Alarm State: {status.get('alarmState', 'Unknown')}\n"
                msg += f"State: {status.get('state', 'Unknown')}\n"
                msg += f"Usage Count: {status.get('usageCount', 0)}\n"
                
                if status.get('messages'):
                    msg += f"\nMessages:\n"
                    for m in status.get('messages', []):
                        msg += f"  - {m}\n"
                
                QMessageBox.information(self, "Asset Status", msg)
            else:
                QMessageBox.information(self, "Asset Status", f"No status available for {serial}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get status: {e}")
    
    def save_config(self) -> None:
        """Save configuration"""
        pass
    
    def load_config(self) -> None:
        """Load configuration"""
        pass
