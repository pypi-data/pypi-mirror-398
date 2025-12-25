"""
Product Management Page

Manage products - part numbers, revisions, BOMs, and product state.
View and create products and their revisions.

Based on the WATS Product API:
- GET /api/Products - List all products
- GET /api/Product/{partNumber} - Get product details
- POST /api/Product - Create/update product
- GET /api/Product/{partNumber}/Revisions - Get revisions
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QDialogButtonBox, QSplitter,
    QCheckBox, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ProductDialog(QDialog):
    """Dialog for creating/editing products"""
    
    def __init__(
        self,
        product: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.product = product
        self._setup_ui()
        if product:
            self._populate_data(product)
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("New Product" if not self.product else "Edit Product")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.part_edit = QLineEdit()
        self.part_edit.setPlaceholderText("Unique part number (required)")
        form.addRow("Part Number:", self.part_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Product name")
        form.addRow("Name:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("Product description")
        form.addRow("Description:", self.desc_edit)
        
        # State
        self.state_combo = QComboBox()
        self.state_combo.addItems(["Active", "New", "Engineering", "Deprecated", "Obsolete"])
        form.addRow("State:", self.state_combo)
        
        # Non-serial checkbox
        self.non_serial_cb = QCheckBox("Non-serialized product")
        self.non_serial_cb.setToolTip("Check if this product cannot have individual units (e.g., bulk materials)")
        form.addRow("", self.non_serial_cb)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _populate_data(self, product: Dict[str, Any]) -> None:
        """Populate with existing product data"""
        self.part_edit.setText(product.get('partNumber', ''))
        self.part_edit.setEnabled(False)  # Can't change part number
        self.name_edit.setText(product.get('name', ''))
        self.desc_edit.setPlainText(product.get('description', ''))
        
        # State
        state = product.get('state', 'Active')
        index = self.state_combo.findText(state)
        if index >= 0:
            self.state_combo.setCurrentIndex(index)
        
        self.non_serial_cb.setChecked(product.get('nonSerial', False))
    
    def _validate_and_accept(self) -> None:
        """Validate input"""
        if not self.part_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Part number is required")
            return
        self.accept()
    
    def get_data(self) -> Dict[str, Any]:
        """Get product data"""
        return {
            'partNumber': self.part_edit.text().strip(),
            'name': self.name_edit.text().strip() or None,
            'description': self.desc_edit.toPlainText().strip() or None,
            'state': self.state_combo.currentText(),
            'nonSerial': self.non_serial_cb.isChecked(),
        }


class AddSubunitDialog(QDialog):
    """Dialog for adding a subunit to a box build template"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("Add Subunit")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.part_edit = QLineEdit()
        self.part_edit.setPlaceholderText("Child product part number (required)")
        form.addRow("Part Number:", self.part_edit)
        
        self.rev_edit = QLineEdit()
        self.rev_edit.setPlaceholderText("Child product revision (required)")
        form.addRow("Revision:", self.rev_edit)
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(999)
        self.qty_spin.setValue(1)
        form.addRow("Quantity:", self.qty_spin)
        
        self.item_edit = QLineEdit()
        self.item_edit.setPlaceholderText("Optional position/item number")
        form.addRow("Item Number:", self.item_edit)
        
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
        if not self.part_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Part number is required")
            return
        if not self.rev_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Revision is required")
            return
        self.accept()
    
    def get_data(self) -> Dict[str, Any]:
        """Get subunit data"""
        return {
            'part_number': self.part_edit.text().strip(),
            'revision': self.rev_edit.text().strip(),
            'quantity': self.qty_spin.value(),
            'item_number': self.item_edit.text().strip() or None,
        }


class ProductPage(BasePage):
    """Product Management page - manage products and revisions"""
    
    # Constants for tree item types
    ITEM_TYPE_PRODUCT = 0
    ITEM_TYPE_REVISION = 1
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._products: List[Dict[str, Any]] = []
        self._selected_product: Optional[Dict[str, Any]] = None
        self._selected_revision: Optional[str] = None
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Products"
    
    def _setup_ui(self) -> None:
        """Setup page UI for Product Management"""
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self._refresh_btn = QPushButton("⟳ Refresh")
        self._refresh_btn.setToolTip("Refresh products from server")
        self._refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self._refresh_btn)
        
        self._add_btn = QPushButton("+ Add Product")
        self._add_btn.clicked.connect(self._on_add_product)
        toolbar_layout.addWidget(self._add_btn)
        
        self._add_rev_btn = QPushButton("+ Add Revision")
        self._add_rev_btn.setEnabled(False)
        self._add_rev_btn.clicked.connect(self._on_add_revision)
        toolbar_layout.addWidget(self._add_rev_btn)
        
        toolbar_layout.addStretch()
        
        # Search
        toolbar_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter by part number or name...")
        self._search_edit.setMaximumWidth(250)
        self._search_edit.textChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._search_edit)
        
        # State filter
        toolbar_layout.addWidget(QLabel("State:"))
        self._state_filter = QComboBox()
        self._state_filter.addItems(["All", "Active", "New", "Engineering", "Deprecated", "Obsolete"])
        self._state_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._state_filter)
        
        self._layout.addLayout(toolbar_layout)
        
        # Main content - splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - hierarchical products/revisions tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_group = QGroupBox("Products & Revisions")
        tree_layout = QVBoxLayout(tree_group)
        
        self._products_tree = QTreeWidget()
        self._products_tree.setColumnCount(3)
        self._products_tree.setHeaderLabels(["Part Number / Revision", "Name / State", "State"])
        self._products_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._products_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._products_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._products_tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self._products_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._products_tree.setAlternatingRowColors(True)
        self._products_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self._products_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self._products_tree.itemExpanded.connect(self._on_item_expanded)
        
        # Apply dark theme styling
        self._products_tree.setStyleSheet("""
            QTreeWidget {
                font-size: 11pt;
                background-color: #1e1e1e;
                alternate-background-color: #2d2d2d;
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
        tree_layout.addWidget(self._products_tree)
        
        left_layout.addWidget(tree_group)
        splitter.addWidget(left_widget)
        
        # Right side - tabbed interface
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for Product Info / BOM / Box Build
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                border: 1px solid #3c3c3c;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3c3c3c;
            }
            QTabBar::tab:disabled {
                color: #555555;
                background-color: #252526;
            }
        """)
        
        # === Tab 1: Product Info ===
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        
        # Product info
        self._details_label = QLabel("Select a product or revision to view details")
        self._details_label.setStyleSheet("color: #808080; font-style: italic;")
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._details_label.setWordWrap(True)
        info_layout.addWidget(self._details_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self._edit_btn = QPushButton("Edit Product")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit_product)
        action_layout.addWidget(self._edit_btn)
        action_layout.addStretch()
        info_layout.addLayout(action_layout)
        
        info_layout.addStretch()
        
        self._tabs.addTab(info_tab, "📋 Product Info")
        
        # === Tab 2: BOM ===
        bom_tab = QWidget()
        bom_layout = QVBoxLayout(bom_tab)
        
        self._bom_info_label = QLabel("Select a revision to view BOM")
        self._bom_info_label.setStyleSheet("color: #808080; font-style: italic;")
        bom_layout.addWidget(self._bom_info_label)
        
        self._bom_tree = QTreeWidget()
        self._bom_tree.setColumnCount(4)
        self._bom_tree.setHeaderLabels(["Part Number", "Description", "Ref", "Qty"])
        self._bom_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._bom_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._bom_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._bom_tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._bom_tree.setStyleSheet(self._get_tree_style())
        bom_layout.addWidget(self._bom_tree)
        
        self._tabs.addTab(bom_tab, "📦 BOM")
        
        # === Tab 3: Box Build ===
        boxbuild_tab = QWidget()
        boxbuild_layout = QVBoxLayout(boxbuild_tab)
        
        self._boxbuild_info_label = QLabel("Select a revision to view/edit Box Build template")
        self._boxbuild_info_label.setStyleSheet("color: #808080; font-style: italic;")
        self._boxbuild_info_label.setWordWrap(True)
        boxbuild_layout.addWidget(self._boxbuild_info_label)
        
        self._boxbuild_tree = QTreeWidget()
        self._boxbuild_tree.setColumnCount(4)
        self._boxbuild_tree.setHeaderLabels(["Child Part Number", "Revision", "Item #", "Qty"])
        self._boxbuild_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._boxbuild_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._boxbuild_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._boxbuild_tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._boxbuild_tree.setStyleSheet(self._get_tree_style())
        boxbuild_layout.addWidget(self._boxbuild_tree)
        
        # Box build actions
        boxbuild_actions = QHBoxLayout()
        self._add_subunit_btn = QPushButton("+ Add Subunit")
        self._add_subunit_btn.setEnabled(False)
        self._add_subunit_btn.clicked.connect(self._on_add_subunit)
        boxbuild_actions.addWidget(self._add_subunit_btn)
        
        self._remove_subunit_btn = QPushButton("- Remove")
        self._remove_subunit_btn.setEnabled(False)
        self._remove_subunit_btn.clicked.connect(self._on_remove_subunit)
        boxbuild_actions.addWidget(self._remove_subunit_btn)
        
        boxbuild_actions.addStretch()
        boxbuild_layout.addLayout(boxbuild_actions)
        
        self._tabs.addTab(boxbuild_tab, "🔧 Box Build")
        
        # Initially disable BOM and Box Build tabs (enabled when revision selected)
        self._tabs.setTabEnabled(1, False)
        self._tabs.setTabEnabled(2, False)
        
        right_layout.addWidget(self._tabs)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])
        
        self._layout.addWidget(splitter, 1)
        
        # Status label
        self._status_label = QLabel("Connect to WATS server to view products")
        self._status_label.setStyleSheet("color: #808080; font-style: italic;")
        self._layout.addWidget(self._status_label)
        
        # Auto-load if connected
        if self._main_window and self._main_window.app.wats_client:
            self._load_products()
    
    def _get_tree_style(self) -> str:
        """Return consistent tree widget styling"""
        return """
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
        """
    
    def _on_tree_selection_changed(self) -> None:
        """Handle tree selection change - product or revision selected"""
        selected_items = self._products_tree.selectedItems()
        
        if not selected_items:
            self._clear_details()
            return
        
        item = selected_items[0]
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type == self.ITEM_TYPE_PRODUCT:
            # Product selected
            part_number = item.text(0)
            product = self._find_product_by_part_number(part_number)
            if product:
                self._selected_product = product
                self._selected_revision = None
                self._show_product_details(product)
                
                # Enable product actions, disable revision-specific
                self._edit_btn.setEnabled(True)
                self._add_rev_btn.setEnabled(True)
                self._add_subunit_btn.setEnabled(False)
                
                # Only Product Info tab enabled
                self._tabs.setTabEnabled(0, True)
                self._tabs.setTabEnabled(1, False)
                self._tabs.setTabEnabled(2, False)
                self._tabs.setCurrentIndex(0)
                
                # Update BOM/BoxBuild info labels
                self._bom_info_label.setText("Select a revision to view BOM")
                self._boxbuild_info_label.setText("Select a revision to view/edit Box Build template")
                
        elif item_type == self.ITEM_TYPE_REVISION:
            # Revision selected
            parent_item = item.parent()
            if parent_item:
                part_number = parent_item.text(0)
                revision = item.text(0)
                product = self._find_product_by_part_number(part_number)
                if product:
                    self._selected_product = product
                    self._selected_revision = revision
                    self._show_revision_details(product, revision)
                    
                    # Enable all actions
                    self._edit_btn.setEnabled(True)
                    self._add_rev_btn.setEnabled(True)
                    self._add_subunit_btn.setEnabled(True)
                    
                    # All tabs enabled
                    self._tabs.setTabEnabled(0, True)
                    self._tabs.setTabEnabled(1, True)
                    self._tabs.setTabEnabled(2, True)
                    
                    # Load BOM and Box Build
                    self._load_bom(product, revision)
                    self._load_box_build(product, revision)
                    
                    # Update info labels
                    self._bom_info_label.setText(f"Bill of Materials for {part_number} rev {revision}")
                    self._boxbuild_info_label.setText(f"Box Build Template for {part_number} rev {revision}")
    
    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on tree item"""
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        if item_type == self.ITEM_TYPE_PRODUCT:
            self._on_edit_product()
    
    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle item expansion - load revisions lazily"""
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        if item_type == self.ITEM_TYPE_PRODUCT:
            # Check if we have a placeholder child
            if item.childCount() == 1:
                child = item.child(0)
                if child and child.data(0, Qt.ItemDataRole.UserRole) == "placeholder":
                    # Load actual revisions
                    part_number = item.text(0)
                    self._load_revisions_for_item(item, part_number)
    
    def _find_product_by_part_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Find product in cache by part number"""
        for product in self._products:
            if product.get('partNumber') == part_number:
                return product
        return None
    
    def _show_product_details(self, product: Dict[str, Any]) -> None:
        """Display product details (product level, no revision)"""
        details = f"""
<h3>{product.get('partNumber', 'N/A')}</h3>
<p><b>Name:</b> {product.get('name', 'N/A')}</p>
<p><b>Description:</b> {product.get('description', 'N/A')}</p>
<p><b>State:</b> {product.get('state', 'N/A')}</p>
<p><b>Non-Serial:</b> {'Yes' if product.get('nonSerial') else 'No'}</p>
<p><b>Created:</b> {product.get('created', 'N/A')}</p>
<hr>
<p style="color: #808080; font-style: italic;">
Expand the product node or select a revision to view BOM and Box Build.
</p>
"""
        self._details_label.setText(details)
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Clear BOM and BoxBuild
        self._bom_tree.clear()
        self._boxbuild_tree.clear()
    
    def _show_revision_details(self, product: Dict[str, Any], revision: str) -> None:
        """Display revision details"""
        details = f"""
<h3>{product.get('partNumber', 'N/A')} - Rev {revision}</h3>
<p><b>Name:</b> {product.get('name', 'N/A')}</p>
<p><b>Description:</b> {product.get('description', 'N/A')}</p>
<p><b>State:</b> {product.get('state', 'N/A')}</p>
<p><b>Non-Serial:</b> {'Yes' if product.get('nonSerial') else 'No'}</p>
<p><b>Revision:</b> <span style="color: #4ec9b0; font-weight: bold;">{revision}</span></p>
<hr>
<p style="color: #4ec9b0;">
BOM and Box Build tabs are now available for this revision.
</p>
"""
        self._details_label.setText(details)
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    
    def _clear_details(self) -> None:
        """Clear details panel"""
        self._selected_product = None
        self._selected_revision = None
        self._details_label.setText("Select a product or revision to view details")
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bom_tree.clear()
        self._boxbuild_tree.clear()
        self._edit_btn.setEnabled(False)
        self._add_rev_btn.setEnabled(False)
        self._add_subunit_btn.setEnabled(False)
        self._remove_subunit_btn.setEnabled(False)
        
        # Disable BOM and Box Build tabs
        self._tabs.setTabEnabled(1, False)
        self._tabs.setTabEnabled(2, False)
        self._tabs.setCurrentIndex(0)
    
    def _load_revisions_for_item(self, parent_item: QTreeWidgetItem, part_number: str) -> None:
        """Load revisions for a product tree item"""
        # Remove placeholder
        parent_item.takeChildren()
        
        try:
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                product = client.product.get_product(part_number)
                
                if product and hasattr(product, 'revisions') and product.revisions:
                    for rev in product.revisions:
                        rev_name = getattr(rev, 'revision', '') or 'Default'
                        rev_state = getattr(rev, 'state', '') or 'Active'
                        
                        rev_item = QTreeWidgetItem([rev_name, rev_state, ""])
                        rev_item.setData(0, Qt.ItemDataRole.UserRole, self.ITEM_TYPE_REVISION)
                        
                        # Color code state
                        if rev_state == "Active":
                            rev_item.setForeground(1, QColor("#4CAF50"))
                        elif rev_state == "Deprecated":
                            rev_item.setForeground(1, QColor("#FF9800"))
                        
                        parent_item.addChild(rev_item)
                else:
                    # No revisions
                    no_rev_item = QTreeWidgetItem(["(No revisions)", "", ""])
                    no_rev_item.setForeground(0, QColor("#808080"))
                    parent_item.addChild(no_rev_item)
        except Exception as e:
            print(f"[Product] Failed to load revisions: {e}")
            error_item = QTreeWidgetItem([f"(Error loading)", "", ""])
            error_item.setForeground(0, QColor("#f44336"))
            parent_item.addChild(error_item)
    
    def _load_bom(self, product: Dict[str, Any], revision: Optional[str] = None) -> None:
        """Load BOM for a product revision.
        
        Args:
            product: Product dictionary
            revision: Specific revision to load BOM for (default: first/active revision)
        """
        self._bom_tree.clear()
        
        try:
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                part_number = product.get('partNumber', '')
                
                # Get revision - either specified or first available
                if not revision:
                    full_product = client.product.get_product(part_number)
                    if full_product and hasattr(full_product, 'revisions') and full_product.revisions:
                        revision = full_product.revisions[0].revision
                
                if revision:
                    # Fetch BOM by part number and revision using the new method
                    bom_items = client.product.get_bom_items(part_number, revision)
                    
                    if bom_items:
                        for bom_item in bom_items:
                            item = QTreeWidgetItem([
                                getattr(bom_item, 'part_number', ''),
                                getattr(bom_item, 'description', '') or '',
                                getattr(bom_item, 'component_ref', '') or '',
                                str(getattr(bom_item, 'quantity', 1))
                            ])
                            self._bom_tree.addTopLevelItem(item)
                    else:
                        item = QTreeWidgetItem(["(No BOM items)", "", "", ""])
                        self._bom_tree.addTopLevelItem(item)
                else:
                    item = QTreeWidgetItem(["(No revision)", "", "", ""])
                    self._bom_tree.addTopLevelItem(item)
        except Exception as e:
            print(f"[Product] Failed to load BOM: {e}")
            item = QTreeWidgetItem([f"(Error: {str(e)[:30]})", "", "", ""])
            self._bom_tree.addTopLevelItem(item)
    
    def _load_box_build(self, product: Dict[str, Any], revision: Optional[str] = None) -> None:
        """Load Box Build template for a product revision.
        
        Args:
            product: Product dictionary
            revision: Specific revision to load (default: first/active revision)
        """
        self._boxbuild_tree.clear()
        self._remove_subunit_btn.setEnabled(False)
        
        try:
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                part_number = product.get('partNumber', '')
                
                # Get revision - either specified or first available
                if not revision:
                    full_product = client.product.get_product(part_number)
                    if full_product and hasattr(full_product, 'revisions') and full_product.revisions:
                        revision = full_product.revisions[0].revision
                
                if revision:
                    # Try to load box build template (uses internal API)
                    try:
                        template = client.product_internal.get_box_build(part_number, revision)
                        subunits = template.get_subunits() if template else []
                        
                        if subunits:
                            for rel in subunits:
                                item = QTreeWidgetItem([
                                    getattr(rel, 'child_part_number', '') or '',
                                    getattr(rel, 'child_revision', '') or '',
                                    getattr(rel, 'item_number', '') or '',
                                    str(getattr(rel, 'quantity', 1))
                                ])
                                self._boxbuild_tree.addTopLevelItem(item)
                            # Enable remove button when items exist
                            self._boxbuild_tree.itemSelectionChanged.connect(
                                lambda: self._remove_subunit_btn.setEnabled(
                                    len(self._boxbuild_tree.selectedItems()) > 0
                                )
                            )
                        else:
                            item = QTreeWidgetItem(["(No subunits defined)", "", "", ""])
                            self._boxbuild_tree.addTopLevelItem(item)
                    except Exception as e:
                        # Internal API may not be available
                        item = QTreeWidgetItem(["(Box Build requires internal API)", "", "", ""])
                        self._boxbuild_tree.addTopLevelItem(item)
                else:
                    item = QTreeWidgetItem(["(No revision)", "", "", ""])
                    self._boxbuild_tree.addTopLevelItem(item)
        except Exception as e:
            print(f"[Product] Failed to load Box Build: {e}")
            item = QTreeWidgetItem([f"(Error: {str(e)[:30]})", "", "", ""])
            self._boxbuild_tree.addTopLevelItem(item)
    
    def _on_filter_changed(self) -> None:
        """Handle filter changes"""
        self._populate_tree()
    
    def _on_refresh(self) -> None:
        """Refresh products from server"""
        if self._main_window and self._main_window.app.wats_client:
            self._load_products()
        else:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
    
    def _load_products(self) -> None:
        """Load products from WATS server"""
        try:
            self._status_label.setText("Loading products...")
            
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                
                # Get products
                products = client.product.get_products()
                self._products = [self._product_to_dict(p) for p in products] if products else []
                
                self._populate_tree()
                self._status_label.setText(f"Loaded {len(self._products)} products")
            else:
                self._status_label.setText("Not connected to WATS server")
        except Exception as e:
            self._status_label.setText(f"Error: {str(e)[:50]}")
            QMessageBox.warning(self, "Error", f"Failed to load products: {e}")
    
    def _product_to_dict(self, product: Any) -> Dict[str, Any]:
        """Convert Product model to dictionary"""
        if hasattr(product, '__dict__'):
            return {
                'partNumber': getattr(product, 'part_number', ''),
                'name': getattr(product, 'name', ''),
                'description': getattr(product, 'description', ''),
                'state': str(getattr(product, 'state', 'Active')),
                'nonSerial': getattr(product, 'non_serial', False),
                'created': str(getattr(product, 'created', ''))[:19],
            }
        return dict(product) if isinstance(product, dict) else {}
    
    def _populate_tree(self) -> None:
        """Populate the products tree with hierarchical data"""
        self._products_tree.clear()
        
        search_text = self._search_edit.text().lower()
        state_filter = self._state_filter.currentText()
        
        for product in self._products:
            # Apply search filter
            if search_text:
                part = product.get('partNumber', '').lower()
                name = product.get('name', '').lower()
                if search_text not in part and search_text not in name:
                    continue
            
            # Apply state filter
            if state_filter != "All":
                if product.get('state', '') != state_filter:
                    continue
            
            # Create product item (parent)
            part_number = product.get('partNumber', '')
            name = product.get('name', '')
            state = product.get('state', 'Active')
            
            product_item = QTreeWidgetItem([part_number, name, state])
            product_item.setData(0, Qt.ItemDataRole.UserRole, self.ITEM_TYPE_PRODUCT)
            
            # Style the product row
            product_item.setForeground(0, QColor("#4ec9b0"))  # Cyan for part number
            
            # Color code state
            if state == "Active":
                product_item.setForeground(2, QColor("#4CAF50"))
            elif state == "Deprecated":
                product_item.setForeground(2, QColor("#FF9800"))
            elif state == "Obsolete":
                product_item.setForeground(2, QColor("#f44336"))
            
            # Add a placeholder child so the item shows as expandable
            placeholder = QTreeWidgetItem(["Loading revisions...", "", ""])
            placeholder.setData(0, Qt.ItemDataRole.UserRole, "placeholder")
            placeholder.setForeground(0, QColor("#808080"))
            product_item.addChild(placeholder)
            
            self._products_tree.addTopLevelItem(product_item)
    
    def _on_add_product(self) -> None:
        """Show dialog to add new product"""
        if not self._main_window or not self._main_window.app.wats_client:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
            return
        
        dialog = ProductDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                client = self._main_window.app.wats_client
                
                # Map state string to enum
                state_map = {
                    "Active": 1,
                    "New": 0,
                    "Engineering": 2,
                    "Deprecated": 3,
                    "Obsolete": 4
                }
                
                result = client.product.create_product(
                    part_number=data['partNumber'],
                    name=data.get('name'),
                    description=data.get('description'),
                    non_serial=data.get('nonSerial', False),
                    state=state_map.get(data.get('state', 'Active'), 1),
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Product created successfully")
                    self._load_products()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create product")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create product: {e}")
    
    def _on_edit_product(self) -> None:
        """Edit selected product"""
        if not self._selected_product:
            return
        
        dialog = ProductDialog(product=self._selected_product, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                client = self._main_window.app.wats_client
                
                # Update product
                result = client.product.update_product(
                    part_number=data['partNumber'],
                    name=data.get('name'),
                    description=data.get('description'),
                    non_serial=data.get('nonSerial', False),
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Product updated successfully")
                    self._load_products()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update product: {e}")
    
    def _on_add_revision(self) -> None:
        """Add revision to selected product"""
        if not self._selected_product:
            return
        
        part_number = self._selected_product.get('partNumber')
        
        # Simple dialog for revision name
        from PySide6.QtWidgets import QInputDialog
        revision, ok = QInputDialog.getText(
            self, "Add Revision",
            f"Enter revision name for {part_number}:",
            QLineEdit.EchoMode.Normal, "A"
        )
        
        if ok and revision:
            try:
                client = self._main_window.app.wats_client
                result = client.product.create_revision(
                    part_number=part_number,
                    revision=revision,
                )
                
                if result:
                    QMessageBox.information(self, "Success", f"Revision '{revision}' created")
                    # Refresh the tree to show new revision
                    self._load_products()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create revision")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create revision: {e}")
    
    def _on_add_subunit(self) -> None:
        """Add subunit to box build template"""
        if not self._selected_product or not self._selected_revision:
            QMessageBox.warning(self, "No Revision", "Please select a revision first")
            return
        
        revision = self._selected_revision
        part_number = self._selected_product.get('partNumber')
        
        # Dialog for adding subunit
        dialog = AddSubunitDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                client = self._main_window.app.wats_client
                
                template = client.product_internal.get_box_build(part_number, revision)
                template.add_subunit(
                    child_part_number=data['part_number'],
                    child_revision=data['revision'],
                    quantity=data.get('quantity', 1),
                    item_number=data.get('item_number')
                )
                template.save()
                
                QMessageBox.information(self, "Success", "Subunit added to template")
                self._load_box_build(self._selected_product, revision)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add subunit: {e}")
    
    def _on_remove_subunit(self) -> None:
        """Remove selected subunit from box build template"""
        selected_items = self._boxbuild_tree.selectedItems()
        if not selected_items:
            return
        
        if not self._selected_product or not self._selected_revision:
            return
        
        revision = self._selected_revision
        part_number = self._selected_product.get('partNumber')
        
        # Get subunit info from selected row
        item = selected_items[0]
        child_part = item.text(0)
        child_rev = item.text(1)
        
        if child_part.startswith("("):
            return  # Skip placeholder items
        
        reply = QMessageBox.question(
            self, "Confirm Remove",
            f"Remove subunit {child_part} rev {child_rev} from template?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                client = self._main_window.app.wats_client
                template = client.product_internal.get_box_build(part_number, revision)
                template.remove_subunit(child_part, child_rev)
                template.save()
                
                QMessageBox.information(self, "Success", "Subunit removed from template")
                self._load_box_build(self._selected_product, revision)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove subunit: {e}")
    
    def save_config(self) -> None:
        """Save configuration"""
        pass
    
    def load_config(self) -> None:
        """Load configuration"""
        pass
