"""
Production Units Page

Manage production units - track serial numbers, assemblies, and unit status.
View unit history and verification status.

Based on the WATS Production API:
- GET /api/Unit/{serialNumber}/{partNumber} - Get unit
- POST /api/Units - Create/update units
- GET /api/Unit/Verification - Get unit verification status
- GET /api/Unit/Phases - Get available unit phases
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QDialogButtonBox, QSplitter,
    QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class UnitLookupDialog(QDialog):
    """Dialog for looking up a specific unit"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("Look Up Unit")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Unit serial number")
        form.addRow("Serial Number:", self.serial_edit)
        
        self.part_edit = QLineEdit()
        self.part_edit.setPlaceholderText("Product part number")
        form.addRow("Part Number:", self.part_edit)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _validate_and_accept(self) -> None:
        """Validate input"""
        if not self.serial_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Serial number is required")
            return
        if not self.part_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Part number is required")
            return
        self.accept()
    
    def get_data(self) -> Dict[str, str]:
        """Get lookup data"""
        return {
            "serial_number": self.serial_edit.text().strip(),
            "part_number": self.part_edit.text().strip()
        }


class UnitCreateDialog(QDialog):
    """Dialog for creating a new unit"""
    
    def __init__(
        self, 
        phases: List[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.phases = phases or []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("Create Unit")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Unit serial number (required)")
        form.addRow("Serial Number:", self.serial_edit)
        
        self.part_edit = QLineEdit()
        self.part_edit.setPlaceholderText("Product part number (required)")
        form.addRow("Part Number:", self.part_edit)
        
        self.revision_edit = QLineEdit()
        self.revision_edit.setPlaceholderText("Product revision (optional)")
        form.addRow("Revision:", self.revision_edit)
        
        # Phase
        self.phase_combo = QComboBox()
        self.phase_combo.addItem("Default", None)
        for phase in self.phases:
            name = phase.get('name') or phase.get('code', 'Unknown')
            self.phase_combo.addItem(name, phase.get('id'))
        form.addRow("Phase:", self.phase_combo)
        
        # Comment
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText("Optional comment")
        form.addRow("Comment:", self.comment_edit)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _validate_and_accept(self) -> None:
        """Validate input"""
        if not self.serial_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Serial number is required")
            return
        if not self.part_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Part number is required")
            return
        self.accept()
    
    def get_data(self) -> Dict[str, Any]:
        """Get unit data"""
        return {
            "serial_number": self.serial_edit.text().strip(),
            "part_number": self.part_edit.text().strip(),
            "revision": self.revision_edit.text().strip() or None,
            "phase_id": self.phase_combo.currentData(),
            "comment": self.comment_edit.toPlainText().strip() or None,
        }


class ProductionPage(BasePage):
    """Production Units page - track units and assemblies"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._units: List[Dict[str, Any]] = []
        self._phases: List[Dict[str, Any]] = []
        self._current_unit: Optional[Dict[str, Any]] = None
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Production Units"
    
    def _setup_ui(self) -> None:
        """Setup page UI for Production Units"""
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self._lookup_btn = QPushButton("🔍 Look Up Unit")
        self._lookup_btn.setToolTip("Look up a specific unit by serial and part number")
        self._lookup_btn.clicked.connect(self._on_lookup_unit)
        toolbar_layout.addWidget(self._lookup_btn)
        
        self._create_btn = QPushButton("+ Create Unit")
        self._create_btn.clicked.connect(self._on_create_unit)
        toolbar_layout.addWidget(self._create_btn)
        
        self._verify_btn = QPushButton("✓ Verify Unit")
        self._verify_btn.setToolTip("Check unit verification status")
        self._verify_btn.clicked.connect(self._on_verify_unit)
        toolbar_layout.addWidget(self._verify_btn)
        
        toolbar_layout.addStretch()
        
        self._layout.addLayout(toolbar_layout)
        
        # Main content - splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - unit lookup and recent units
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Quick lookup group
        lookup_group = QGroupBox("Quick Unit Lookup")
        lookup_layout = QVBoxLayout(lookup_group)
        
        sn_layout = QHBoxLayout()
        sn_layout.addWidget(QLabel("SN:"))
        self._quick_serial = QLineEdit()
        self._quick_serial.setPlaceholderText("Serial number")
        sn_layout.addWidget(self._quick_serial)
        lookup_layout.addLayout(sn_layout)
        
        pn_layout = QHBoxLayout()
        pn_layout.addWidget(QLabel("PN:"))
        self._quick_part = QLineEdit()
        self._quick_part.setPlaceholderText("Part number")
        pn_layout.addWidget(self._quick_part)
        lookup_layout.addLayout(pn_layout)
        
        self._quick_lookup_btn = QPushButton("Look Up")
        self._quick_lookup_btn.clicked.connect(self._on_quick_lookup)
        lookup_layout.addWidget(self._quick_lookup_btn)
        
        left_layout.addWidget(lookup_group)
        
        # Recent units table
        recent_group = QGroupBox("Recent Units Viewed")
        recent_layout = QVBoxLayout(recent_group)
        
        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(3)
        self._recent_table.setHorizontalHeaderLabels(["Serial", "Part Number", "Status"])
        self._recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._recent_table.setMaximumHeight(200)
        self._recent_table.doubleClicked.connect(self._on_recent_double_click)
        recent_layout.addWidget(self._recent_table)
        
        left_layout.addWidget(recent_group)
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # Right side - unit details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Unit details group
        details_group = QGroupBox("Unit Details")
        details_layout = QVBoxLayout(details_group)
        
        self._unit_info = QLabel("Look up a unit to view details")
        self._unit_info.setStyleSheet("color: #808080; font-style: italic;")
        self._unit_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unit_info.setWordWrap(True)
        details_layout.addWidget(self._unit_info)
        
        right_layout.addWidget(details_group)
        
        # Assembly tree (sub-units)
        assembly_group = QGroupBox("Assembly / Sub-Units")
        assembly_layout = QVBoxLayout(assembly_group)
        
        self._assembly_tree = QTreeWidget()
        self._assembly_tree.setColumnCount(3)
        self._assembly_tree.setHeaderLabels(["Serial Number", "Part Number", "Status"])
        self._assembly_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._assembly_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._assembly_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._assembly_tree.setStyleSheet("""
            QTreeWidget {
                font-size: 11pt;
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #3c3c3c;
                font-weight: bold;
            }
        """)
        assembly_layout.addWidget(self._assembly_tree)
        
        right_layout.addWidget(assembly_group)
        
        # Verification status
        verify_group = QGroupBox("Verification Status")
        verify_layout = QVBoxLayout(verify_group)
        
        self._verify_info = QLabel("No unit selected")
        self._verify_info.setStyleSheet("color: #808080; font-style: italic;")
        verify_layout.addWidget(self._verify_info)
        
        right_layout.addWidget(verify_group)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 550])
        
        self._layout.addWidget(splitter, 1)
        
        # Status label
        self._status_label = QLabel("Connect to WATS server to manage production units")
        self._status_label.setStyleSheet("color: #808080; font-style: italic;")
        self._layout.addWidget(self._status_label)
        
        # Load phases if connected
        if self._main_window and self._main_window.app.wats_client:
            self._load_phases()
    
    def _load_phases(self) -> None:
        """Load unit phases from server"""
        try:
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                phases = client.production.get_phases()
                self._phases = [self._phase_to_dict(p) for p in phases] if phases else []
        except Exception as e:
            print(f"[Production] Failed to load phases: {e}")
    
    def _phase_to_dict(self, phase: Any) -> Dict[str, Any]:
        """Convert UnitPhase to dict"""
        if hasattr(phase, '__dict__'):
            return {
                'id': getattr(phase, 'id', None),
                'code': getattr(phase, 'code', ''),
                'name': getattr(phase, 'name', ''),
            }
        return dict(phase) if isinstance(phase, dict) else {}
    
    def _on_lookup_unit(self) -> None:
        """Show lookup dialog"""
        dialog = UnitLookupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._lookup_unit(data['serial_number'], data['part_number'])
    
    def _on_quick_lookup(self) -> None:
        """Perform quick lookup"""
        serial = self._quick_serial.text().strip()
        part = self._quick_part.text().strip()
        
        if not serial or not part:
            QMessageBox.warning(self, "Validation", "Both serial number and part number are required")
            return
        
        self._lookup_unit(serial, part)
    
    def _on_recent_double_click(self) -> None:
        """Handle double-click on recent unit"""
        row = self._recent_table.currentRow()
        if row >= 0:
            serial = self._recent_table.item(row, 0).text()
            part = self._recent_table.item(row, 1).text()
            self._lookup_unit(serial, part)
    
    def _lookup_unit(self, serial_number: str, part_number: str) -> None:
        """Look up a unit and display details"""
        if not self._main_window or not self._main_window.app.wats_client:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
            return
        
        try:
            self._status_label.setText(f"Looking up unit {serial_number}...")
            
            client = self._main_window.app.wats_client
            unit = client.production.get_unit(serial_number, part_number)
            
            if unit:
                self._current_unit = self._unit_to_dict(unit)
                self._display_unit(self._current_unit)
                self._add_to_recent(serial_number, part_number, "Found")
                self._status_label.setText(f"Found unit: {serial_number}")
            else:
                self._unit_info.setText(f"Unit not found: {serial_number} / {part_number}")
                self._add_to_recent(serial_number, part_number, "Not Found")
                self._status_label.setText("Unit not found")
        except Exception as e:
            self._status_label.setText(f"Error: {str(e)[:50]}")
            QMessageBox.warning(self, "Error", f"Failed to look up unit: {e}")
    
    def _unit_to_dict(self, unit: Any) -> Dict[str, Any]:
        """Convert Unit model to dictionary"""
        if hasattr(unit, '__dict__'):
            return {
                'serialNumber': getattr(unit, 'serial_number', ''),
                'partNumber': getattr(unit, 'part_number', ''),
                'revision': getattr(unit, 'revision', ''),
                'phase': getattr(unit, 'phase', ''),
                'phaseId': getattr(unit, 'phase_id', None),
                'created': str(getattr(unit, 'created', ''))[:19],
                'modified': str(getattr(unit, 'modified', ''))[:19],
                'comment': getattr(unit, 'comment', ''),
                'subUnits': getattr(unit, 'sub_units', []),
                'changes': getattr(unit, 'changes', []),
            }
        return dict(unit) if isinstance(unit, dict) else {}
    
    def _display_unit(self, unit: Dict[str, Any]) -> None:
        """Display unit details"""
        info = f"""
<b>Serial Number:</b> {unit.get('serialNumber', 'N/A')}<br>
<b>Part Number:</b> {unit.get('partNumber', 'N/A')}<br>
<b>Revision:</b> {unit.get('revision', 'N/A')}<br>
<b>Phase:</b> {unit.get('phase', 'N/A')}<br>
<b>Created:</b> {unit.get('created', 'N/A')}<br>
<b>Modified:</b> {unit.get('modified', 'N/A')}<br>
<b>Comment:</b> {unit.get('comment', 'N/A')}<br>
"""
        self._unit_info.setText(info)
        self._unit_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Populate assembly tree
        self._assembly_tree.clear()
        
        # Add current unit as root
        root = QTreeWidgetItem([
            unit.get('serialNumber', ''),
            unit.get('partNumber', ''),
            "Main Unit"
        ])
        self._assembly_tree.addTopLevelItem(root)
        
        # Add sub-units
        for sub in unit.get('subUnits', []):
            if hasattr(sub, '__dict__'):
                sub = {
                    'serialNumber': getattr(sub, 'serial_number', ''),
                    'partNumber': getattr(sub, 'part_number', ''),
                }
            child = QTreeWidgetItem([
                sub.get('serialNumber', ''),
                sub.get('partNumber', ''),
                "Sub-Unit"
            ])
            root.addChild(child)
        
        root.setExpanded(True)
        
        # Get verification status
        self._load_verification(unit.get('serialNumber'), unit.get('partNumber'))
    
    def _load_verification(self, serial: str, part: str) -> None:
        """Load verification status for unit"""
        try:
            client = self._main_window.app.wats_client
            verification = client.production.verify_unit(serial, part)
            
            if verification:
                grade = getattr(verification, 'grade', 'Unknown') if hasattr(verification, 'grade') else verification.get('grade', 'Unknown')
                passed = getattr(verification, 'passed', False) if hasattr(verification, 'passed') else verification.get('passed', False)
                
                if passed:
                    self._verify_info.setText(f"<span style='color: #4CAF50'>✓ PASS</span> - Grade: {grade}")
                else:
                    self._verify_info.setText(f"<span style='color: #f44336'>✗ FAIL</span> - Grade: {grade}")
            else:
                self._verify_info.setText("No verification data available")
        except Exception as e:
            self._verify_info.setText(f"Could not load verification: {str(e)[:30]}")
    
    def _add_to_recent(self, serial: str, part: str, status: str) -> None:
        """Add unit to recent lookups table"""
        # Check if already in table
        for row in range(self._recent_table.rowCount()):
            if (self._recent_table.item(row, 0).text() == serial and
                self._recent_table.item(row, 1).text() == part):
                return
        
        # Add new row at top
        self._recent_table.insertRow(0)
        self._recent_table.setItem(0, 0, QTableWidgetItem(serial))
        self._recent_table.setItem(0, 1, QTableWidgetItem(part))
        
        status_item = QTableWidgetItem(status)
        if status == "Found":
            status_item.setForeground(QColor("#4CAF50"))
        else:
            status_item.setForeground(QColor("#f44336"))
        self._recent_table.setItem(0, 2, status_item)
        
        # Limit to 10 recent items
        while self._recent_table.rowCount() > 10:
            self._recent_table.removeRow(self._recent_table.rowCount() - 1)
    
    def _on_create_unit(self) -> None:
        """Show dialog to create new unit"""
        if not self._main_window or not self._main_window.app.wats_client:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
            return
        
        dialog = UnitCreateDialog(self._phases, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                client = self._main_window.app.wats_client
                
                # Create unit using the production service
                from pywats.domains.production.models import Unit
                unit = Unit(
                    serial_number=data['serial_number'],
                    part_number=data['part_number'],
                    revision=data.get('revision'),
                    phase_id=data.get('phase_id'),
                    comment=data.get('comment'),
                )
                
                result = client.production.create_units([unit])
                
                if result:
                    QMessageBox.information(self, "Success", "Unit created successfully")
                    self._lookup_unit(data['serial_number'], data['part_number'])
                else:
                    QMessageBox.warning(self, "Error", "Failed to create unit")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create unit: {e}")
    
    def _on_verify_unit(self) -> None:
        """Verify current unit"""
        if not self._current_unit:
            QMessageBox.information(self, "No Unit Selected", "Please look up a unit first")
            return
        
        serial = self._current_unit.get('serialNumber')
        part = self._current_unit.get('partNumber')
        
        if serial and part:
            self._load_verification(serial, part)
    
    def save_config(self) -> None:
        """Save configuration"""
        pass
    
    def load_config(self) -> None:
        """Load configuration"""
        pass
