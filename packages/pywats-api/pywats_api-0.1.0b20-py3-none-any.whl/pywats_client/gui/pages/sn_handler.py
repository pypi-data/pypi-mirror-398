"""
SN Handler Page

Serial Number Handler page for managing serial numbers through the WATS server.
This page allows users to:
- View available serial number types configured on the server
- Take/reserve serial numbers for testing
- View serial number usage history in a grid

Based on the WATS Production API:
- GET /api/Production/SerialNumbers/Types - List available types
- POST /api/Production/SerialNumbers/Take - Take serial numbers

Note on Reserve vs Take:
- The internal API has GetAndReserveNewSerialNumbers which is used by WATS Client
  for pre-allocating serial numbers (reserve count controlled by config)
- The public API uses /Take endpoint which immediately assigns serial numbers
- Both effectively "consume" serial numbers from the pool
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QMessageBox, QSplitter,
    QDialog, QDialogButtonBox, QFrame, QApplication
)
from PySide6.QtCore import Qt

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class TakeSerialNumbersDialog(QDialog):
    """Dialog for taking serial numbers"""
    
    def __init__(self, type_name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.type_name = type_name
        self.setWindowTitle(f"Take Serial Numbers - {type_name}")
        self.setMinimumWidth(450)
        
        self.count = 1
        self.ref_sn = ""
        self.ref_pn = ""
        self.ref_station = ""
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Type (read-only)
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        type_label = QLabel(self.type_name)
        type_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        type_layout.addWidget(type_label)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        layout.addSpacing(10)
        
        # Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Count:"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 1000)
        self._count_spin.setValue(1)
        self._count_spin.setFixedWidth(100)
        count_layout.addWidget(self._count_spin)
        count_layout.addStretch()
        layout.addLayout(count_layout)
        
        layout.addSpacing(10)
        
        # Reference section
        ref_group = QGroupBox("Reference (Optional)")
        ref_layout = QVBoxLayout(ref_group)
        
        # Reference Serial Number
        ref_sn_layout = QHBoxLayout()
        ref_sn_label = QLabel("Serial Number:")
        ref_sn_label.setFixedWidth(100)
        ref_sn_layout.addWidget(ref_sn_label)
        self._ref_sn_edit = QLineEdit()
        self._ref_sn_edit.setPlaceholderText("Reference serial number")
        ref_sn_layout.addWidget(self._ref_sn_edit)
        ref_layout.addLayout(ref_sn_layout)
        
        # Reference Part Number
        ref_pn_layout = QHBoxLayout()
        ref_pn_label = QLabel("Part Number:")
        ref_pn_label.setFixedWidth(100)
        ref_pn_layout.addWidget(ref_pn_label)
        self._ref_pn_edit = QLineEdit()
        self._ref_pn_edit.setPlaceholderText("Reference part number")
        ref_pn_layout.addWidget(self._ref_pn_edit)
        ref_layout.addLayout(ref_pn_layout)
        
        # Reference Station
        ref_station_layout = QHBoxLayout()
        ref_station_label = QLabel("Station:")
        ref_station_label.setFixedWidth(100)
        ref_station_layout.addWidget(ref_station_label)
        self._ref_station_edit = QLineEdit()
        self._ref_station_edit.setPlaceholderText("Station name")
        ref_station_layout.addWidget(self._ref_station_edit)
        ref_layout.addLayout(ref_station_layout)
        
        layout.addWidget(ref_group)
        
        layout.addSpacing(10)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_values(self) -> dict:
        """Get the values from the dialog"""
        return {
            'count': self._count_spin.value(),
            'ref_sn': self._ref_sn_edit.text().strip(),
            'ref_pn': self._ref_pn_edit.text().strip(),
            'ref_station': self._ref_station_edit.text().strip()
        }


class SNHandlerPage(BasePage):
    """Serial Number Handler page - manage serial numbers from WATS server"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._sn_types: List = []
        self._taken_serials: List[dict] = []  # History of taken serials
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "SN Handler"
    
    def _setup_ui(self) -> None:
        """Setup page UI for Serial Number handling"""
        # Main splitter to divide types and results
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # =========================================================================
        # Top Section: Serial Number Types
        # =========================================================================
        types_widget = QWidget()
        types_main_layout = QVBoxLayout(types_widget)
        types_main_layout.setContentsMargins(0, 0, 0, 0)
        
        types_group = QGroupBox("Serial Number Types")
        types_layout = QVBoxLayout(types_group)
        
        # Types table
        self._types_table = QTableWidget()
        self._types_table.setColumnCount(4)
        self._types_table.setHorizontalHeaderLabels([
            "Type Name", "Prefix", "Suffix", "Description"
        ])
        self._types_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._types_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._types_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._types_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._types_table.verticalHeader().setVisible(False)
        self._types_table.setAlternatingRowColors(True)
        self._types_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._types_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._types_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._types_table.setColumnWidth(0, 150)
        self._types_table.itemSelectionChanged.connect(self._on_type_selected)
        types_layout.addWidget(self._types_table, 1)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self._refresh_btn = QPushButton("🔄 Refresh")
        self._refresh_btn.clicked.connect(self._on_refresh_types)
        action_layout.addWidget(self._refresh_btn)
        
        self._take_btn = QPushButton("📥 Take Serial Numbers")
        self._take_btn.setEnabled(False)
        self._take_btn.setObjectName("primaryButton")
        self._take_btn.clicked.connect(self._on_take_serials)
        action_layout.addWidget(self._take_btn)
        
        action_layout.addStretch()
        types_layout.addLayout(action_layout)
        
        types_main_layout.addWidget(types_group)
        splitter.addWidget(types_widget)
        
        # =========================================================================
        # Bottom Section: Results Grid (larger area)
        # =========================================================================
        results_widget = QWidget()
        results_main_layout = QVBoxLayout(results_widget)
        results_main_layout.setContentsMargins(0, 0, 0, 0)
        
        results_group = QGroupBox("Taken Serial Numbers")
        results_layout = QVBoxLayout(results_group)
        
        # Results grid table
        self._results_table = QTableWidget()
        self._results_table.setColumnCount(6)
        self._results_table.setHorizontalHeaderLabels([
            "Serial Number", "Type", "Ref SN", "Ref PN", "Station", "Timestamp"
        ])
        self._results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self._results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self._results_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._results_table.verticalHeader().setVisible(False)
        self._results_table.setAlternatingRowColors(True)
        self._results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._results_table.setColumnWidth(0, 180)
        self._results_table.setColumnWidth(2, 100)
        self._results_table.setColumnWidth(3, 100)
        self._results_table.setColumnWidth(4, 100)
        results_layout.addWidget(self._results_table, 1)
        
        # Results action buttons
        results_action_layout = QHBoxLayout()
        
        self._copy_btn = QPushButton("📋 Copy Selected")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._on_copy_selected)
        results_action_layout.addWidget(self._copy_btn)
        
        self._copy_all_btn = QPushButton("📋 Copy All Serial Numbers")
        self._copy_all_btn.setEnabled(False)
        self._copy_all_btn.clicked.connect(self._on_copy_all)
        results_action_layout.addWidget(self._copy_all_btn)
        
        self._clear_btn = QPushButton("🗑️ Clear")
        self._clear_btn.clicked.connect(self._on_clear_results)
        results_action_layout.addWidget(self._clear_btn)
        
        results_action_layout.addStretch()
        results_layout.addLayout(results_action_layout)
        
        results_main_layout.addWidget(results_group)
        splitter.addWidget(results_widget)
        
        # Set initial splitter sizes (types: 35%, results: 65%)
        splitter.setSizes([250, 450])
        
        self._layout.addWidget(splitter, 1)
        
        # Status bar
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        self._status_label = QLabel("Connect to WATS server to manage serial numbers")
        self._status_label.setStyleSheet("color: #808080; font-style: italic;")
        status_layout.addWidget(self._status_label)
        
        status_layout.addStretch()
        
        self._count_label = QLabel("Total taken: 0")
        self._count_label.setStyleSheet("color: #4ec9b0;")
        status_layout.addWidget(self._count_label)
        
        self._layout.addWidget(status_frame)
        
        # Connect selection change to enable copy button
        self._results_table.itemSelectionChanged.connect(self._on_result_selection_changed)
        
        # Auto-load types if connected
        if self._main_window and self._main_window.app.wats_client:
            print("[SN Handler] Auto-loading types on initialization")
            self._load_sn_types()
    
    def _on_type_selected(self) -> None:
        """Handle serial number type selection in table"""
        selected = self._types_table.selectedItems()
        self._take_btn.setEnabled(len(selected) > 0)
    
    def _on_result_selection_changed(self) -> None:
        """Handle result selection change"""
        selected = self._results_table.selectedItems()
        self._copy_btn.setEnabled(len(selected) > 0)
    
    def _on_refresh_types(self) -> None:
        """Refresh serial number types from server"""
        if self._main_window and self._main_window.app.wats_client:
            self._load_sn_types()
        else:
            QMessageBox.warning(
                self, "Not Connected",
                "Please connect to WATS server first."
            )
    
    def _on_take_serials(self) -> None:
        """Take serial numbers from server"""
        # Get selected type from table
        selected = self._types_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a serial number type.")
            return
        
        row = selected[0].row()
        type_item = self._types_table.item(row, 0)
        if not type_item:
            return
        
        type_name = type_item.text()
        
        # Show dialog
        dialog = TakeSerialNumbersDialog(type_name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            self._take_serial_numbers(
                type_name=type_name,
                count=values['count'],
                ref_sn=values['ref_sn'] or None,
                ref_pn=values['ref_pn'] or None,
                ref_station=values['ref_station'] or None
            )
    
    def _take_serial_numbers(
        self,
        type_name: str,
        count: int = 1,
        ref_sn: Optional[str] = None,
        ref_pn: Optional[str] = None,
        ref_station: Optional[str] = None
    ) -> None:
        """Take serial numbers from the WATS server"""
        try:
            self._status_label.setText(f"Taking {count} serial number(s)...")
            
            if not self._main_window or not self._main_window.app.wats_client:
                QMessageBox.warning(self, "Error", "Not connected to WATS server")
                return
            
            client = self._main_window.app.wats_client
            
            # Call the API to allocate/take serial numbers
            serials = client.production.allocate_serial_numbers(
                type_name=type_name,
                count=count,
                reference_sn=ref_sn,
                reference_pn=ref_pn,
                station_name=ref_station
            )
            
            if serials:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add each serial to the results table
                for serial in serials:
                    row_data = {
                        'serial': serial,
                        'type': type_name,
                        'ref_sn': ref_sn or '',
                        'ref_pn': ref_pn or '',
                        'station': ref_station or '',
                        'timestamp': timestamp
                    }
                    self._taken_serials.append(row_data)
                    self._add_result_row(row_data)
                
                self._status_label.setText(f"Successfully took {len(serials)} serial number(s)")
                self._update_count()
                self._copy_all_btn.setEnabled(True)
                
                QMessageBox.information(
                    self, "Success",
                    f"Successfully took {len(serials)} serial number(s):\n" + 
                    "\n".join(serials[:10]) + 
                    (f"\n... and {len(serials) - 10} more" if len(serials) > 10 else "")
                )
            else:
                self._status_label.setText("No serial numbers returned")
                QMessageBox.warning(self, "Warning", "No serial numbers were returned from the server.")
                
        except Exception as e:
            self._status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to take serial numbers:\n{str(e)}")
    
    def _add_result_row(self, row_data: dict) -> None:
        """Add a row to the results table"""
        row = self._results_table.rowCount()
        self._results_table.insertRow(row)
        
        # Serial number (highlight in green)
        serial_item = QTableWidgetItem(row_data['serial'])
        serial_item.setForeground(Qt.GlobalColor.green)
        self._results_table.setItem(row, 0, serial_item)
        
        self._results_table.setItem(row, 1, QTableWidgetItem(row_data['type']))
        self._results_table.setItem(row, 2, QTableWidgetItem(row_data['ref_sn']))
        self._results_table.setItem(row, 3, QTableWidgetItem(row_data['ref_pn']))
        self._results_table.setItem(row, 4, QTableWidgetItem(row_data['station']))
        self._results_table.setItem(row, 5, QTableWidgetItem(row_data['timestamp']))
        
        # Scroll to the new row
        self._results_table.scrollToBottom()
    
    def _update_count(self) -> None:
        """Update the count label"""
        self._count_label.setText(f"Total taken: {len(self._taken_serials)}")
    
    def _on_copy_selected(self) -> None:
        """Copy selected serial numbers to clipboard"""
        selected_rows = set()
        for item in self._results_table.selectedItems():
            selected_rows.add(item.row())
        
        serials = []
        for row in sorted(selected_rows):
            item = self._results_table.item(row, 0)
            if item:
                serials.append(item.text())
        
        if serials:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(serials))
            self._status_label.setText(f"Copied {len(serials)} serial number(s) to clipboard")
    
    def _on_copy_all(self) -> None:
        """Copy all serial numbers to clipboard"""
        serials = [data['serial'] for data in self._taken_serials]
        if serials:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(serials))
            self._status_label.setText(f"Copied {len(serials)} serial number(s) to clipboard")
    
    def _on_clear_results(self) -> None:
        """Clear the results table"""
        self._results_table.setRowCount(0)
        self._taken_serials.clear()
        self._update_count()
        self._copy_btn.setEnabled(False)
        self._copy_all_btn.setEnabled(False)
        self._status_label.setText("Results cleared")
    
    def _load_sn_types(self) -> None:
        """Load serial number types from WATS server"""
        try:
            self._status_label.setText("Loading serial number types...")
            print("[SN Handler] Starting to load serial number types...")
            
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                print(f"[SN Handler] WATS client available: {client}")
                # Get serial number types from production API
                types = client.production.get_serial_number_types()
                print(f"[SN Handler] Received {len(types) if types else 0} types from API")
                if types:
                    self._sn_types = types
                    print(f"[SN Handler] First type: {types[0].name if types else 'N/A'}")
                else:
                    self._sn_types = []
            else:
                print(f"[SN Handler] No client - main_window: {self._main_window}")
                self._sn_types = []
                self._status_label.setText("Not connected to WATS server")
                return
            
            print(f"[SN Handler] Populating table with {len(self._sn_types)} types")
            self._populate_types_table()
            self._status_label.setText(f"Found {len(self._sn_types)} serial number types")
            
        except Exception as e:
            print(f"[SN Handler] Error: {e}")
            import traceback
            traceback.print_exc()
            self._status_label.setText(f"Error: {str(e)}")
    
    def _populate_types_table(self) -> None:
        """Populate serial number types table"""
        self._types_table.setRowCount(len(self._sn_types))
        for row, sn_type in enumerate(self._sn_types):
            self._types_table.setItem(row, 0, QTableWidgetItem(sn_type.name or ""))
            self._types_table.setItem(row, 1, QTableWidgetItem(getattr(sn_type, 'prefix', '') or ""))
            self._types_table.setItem(row, 2, QTableWidgetItem(getattr(sn_type, 'suffix', '') or ""))
            self._types_table.setItem(row, 3, QTableWidgetItem(sn_type.description or ""))
    
    def save_config(self) -> None:
        """No configuration to save for this page"""
        pass
    
    def load_config(self) -> None:
        """No configuration to load for this page"""
        pass
