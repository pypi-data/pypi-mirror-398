"""
Software Page

Software Distribution page for downloading and managing software packages
from the WATS server. This allows test stations to receive updates to
test sequences, configurations, and other software.

Based on the WATS Software Distribution API:
- GET /api/Software/Packages - List all packages
- GET /api/Software/Package/{id} - Get package details
- GET /api/Software/PackagesByTag - Filter packages by tag
- POST /api/Software/Package - Create new package
- POST /api/Software/Package/{id}/Release - Release a package
- POST /api/Software/File - Upload file to package
"""

import asyncio
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QProgressBar, QMessageBox,
    QCheckBox, QTreeWidget, QTreeWidgetItem, QDialog,
    QFormLayout, QTextEdit, QDialogButtonBox, QFileDialog,
    QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class PackageDialog(QDialog):
    """Dialog for creating/editing software packages"""
    
    def __init__(
        self,
        package: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.package = package
        self._setup_ui()
        if package:
            self._populate_data(package)
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("New Package" if not self.package else "Edit Package")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Package name (required)")
        form.addRow("Name:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("Package description")
        form.addRow("Description:", self.desc_edit)
        
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Virtual folder for organization (optional)")
        form.addRow("Folder:", self.folder_edit)
        
        self.root_dir_edit = QLineEdit()
        self.root_dir_edit.setPlaceholderText("Installation root directory (optional)")
        form.addRow("Root Directory:", self.root_dir_edit)
        
        self.install_root_cb = QCheckBox("Install on root")
        form.addRow("", self.install_root_cb)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _populate_data(self, package: Dict[str, Any]) -> None:
        """Populate with existing package data"""
        self.name_edit.setText(package.get('name', ''))
        self.name_edit.setEnabled(False)  # Can't change name
        self.desc_edit.setPlainText(package.get('description', ''))
        self.root_dir_edit.setText(package.get('rootDirectory', ''))
        self.install_root_cb.setChecked(package.get('installOnRoot', False))
    
    def _validate_and_accept(self) -> None:
        """Validate input"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Package name is required")
            return
        self.accept()
    
    def get_data(self) -> Dict[str, Any]:
        """Get package data"""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip() or None,
            'folder': self.folder_edit.text().strip() or None,
            'rootDirectory': self.root_dir_edit.text().strip() or None,
            'installOnRoot': self.install_root_cb.isChecked(),
        }


class SoftwarePage(BasePage):
    """Software Distribution page - manage packages from WATS server"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._packages: List[Dict[str, Any]] = []
        self._selected_package: Optional[Any] = None
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Software"
    
    def _setup_ui(self) -> None:
        """Setup page UI for Software Distribution"""
        # Software Distribution Settings
        settings_group = QGroupBox("Software Distribution Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Enable auto-update
        self._auto_update_cb = QCheckBox("Enable automatic software updates")
        self._auto_update_cb.setToolTip(
            "Automatically check for and download software updates from WATS"
        )
        self._auto_update_cb.stateChanged.connect(self._emit_changed)
        settings_layout.addWidget(self._auto_update_cb)
        
        self._layout.addWidget(settings_group)
        
        self._layout.addSpacing(10)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - packages list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Available Packages
        packages_group = QGroupBox("Available Packages")
        packages_layout = QVBoxLayout(packages_group)
        
        # Toolbar row
        toolbar_layout = QHBoxLayout()
        
        self._refresh_btn = QPushButton("⟳ Refresh")
        self._refresh_btn.setToolTip("Refresh packages from server")
        self._refresh_btn.clicked.connect(self._on_refresh_packages)
        toolbar_layout.addWidget(self._refresh_btn)
        
        self._create_btn = QPushButton("+ Create")
        self._create_btn.setToolTip("Create new package")
        self._create_btn.clicked.connect(self._on_create_package)
        toolbar_layout.addWidget(self._create_btn)
        
        toolbar_layout.addStretch()
        packages_layout.addLayout(toolbar_layout)
        
        # Filter row
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        
        self._status_combo = QComboBox()
        self._status_combo.addItems(["Released", "All", "Draft", "Pending", "Revoked"])
        self._status_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._status_combo)
        
        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Search:"))
        
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search packages...")
        self._search_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._search_edit, 1)
        packages_layout.addLayout(filter_layout)
        
        # Packages tree view (organized by virtual folders)
        self._packages_tree = QTreeWidget()
        self._packages_tree.setColumnCount(4)
        self._packages_tree.setHeaderLabels([
            "Package / Folder", "Version", "Status", "Updated"
        ])
        self._packages_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._packages_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._packages_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._packages_tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._packages_tree.setAlternatingRowColors(True)
        self._packages_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._packages_tree.setIndentation(20)
        self._packages_tree.setColumnWidth(0, 300)
        # Apply styling to match other grids in the app
        self._packages_tree.setStyleSheet("""
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
            QTreeWidget::item:hover {
                background-color: #2d2d2d;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #3c3c3c;
                font-weight: bold;
            }
        """)
        packages_layout.addWidget(self._packages_tree)
        
        left_layout.addWidget(packages_group)
        splitter.addWidget(left_widget)
        
        # Right side - package details and actions
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Package Details
        details_group = QGroupBox("Package Details")
        details_layout = QVBoxLayout(details_group)
        
        self._details_label = QLabel("Select a package to view details")
        self._details_label.setStyleSheet("color: #808080; font-style: italic;")
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._details_label.setWordWrap(True)
        details_layout.addWidget(self._details_label)
        
        right_layout.addWidget(details_group)
        
        # Files list
        files_group = QGroupBox("Package Files")
        files_layout = QVBoxLayout(files_group)
        
        self._files_list = QListWidget()
        self._files_list.setMaximumHeight(150)
        files_layout.addWidget(self._files_list)
        
        # Upload button
        self._upload_btn = QPushButton("📤 Upload File")
        self._upload_btn.setEnabled(False)
        self._upload_btn.clicked.connect(self._on_upload_file)
        files_layout.addWidget(self._upload_btn)
        
        right_layout.addWidget(files_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self._release_btn = QPushButton("✓ Release Package")
        self._release_btn.setEnabled(False)
        self._release_btn.setToolTip("Release this package for distribution")
        self._release_btn.clicked.connect(self._on_release_package)
        actions_layout.addWidget(self._release_btn)
        
        self._revoke_btn = QPushButton("✗ Revoke Package")
        self._revoke_btn.setEnabled(False)
        self._revoke_btn.setToolTip("Revoke this package from distribution")
        self._revoke_btn.clicked.connect(self._on_revoke_package)
        actions_layout.addWidget(self._revoke_btn)
        
        self._delete_btn = QPushButton("🗑 Delete Package")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete_package)
        actions_layout.addWidget(self._delete_btn)
        
        right_layout.addWidget(actions_group)
        right_layout.addStretch()
        
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 300])
        
        self._layout.addWidget(splitter, 1)
        
        # Progress indicator
        progress_layout = QHBoxLayout()
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumWidth(200)
        progress_layout.addWidget(self._progress_bar)
        progress_layout.addStretch()
        self._layout.addLayout(progress_layout)
        
        # Status message
        self._status_label = QLabel("Connect to WATS server to view available packages")
        self._status_label.setStyleSheet("color: #808080; font-style: italic;")
        self._layout.addWidget(self._status_label)
        
        # Connect tree selection
        self._packages_tree.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Auto-load packages if connected
        if self._main_window and self._main_window.app.wats_client:
            print("[Software] Auto-loading packages on initialization")
            self._load_packages()
    
    def _on_selection_changed(self) -> None:
        """Handle package selection change"""
        selected_items = self._packages_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            package = item.data(0, Qt.ItemDataRole.UserRole)
            if package:
                self._selected_package = package
                self._show_package_details(package)
                
                # Enable/disable buttons based on package status
                status_str = str(package.status.value) if hasattr(package.status, 'value') else str(package.status)
                is_draft = status_str.lower() == 'draft'
                is_released = status_str.lower() == 'released'
                
                self._upload_btn.setEnabled(is_draft)
                self._release_btn.setEnabled(is_draft)
                self._revoke_btn.setEnabled(is_released)
                self._delete_btn.setEnabled(is_draft)
            else:
                self._selected_package = None
                self._clear_details()
        else:
            self._selected_package = None
            self._clear_details()
    
    def _show_package_details(self, package: Any) -> None:
        """Display package details"""
        status_str = str(package.status.value) if hasattr(package.status, 'value') else str(package.status)
        
        details = f"""
<b>Name:</b> {package.name or 'N/A'}<br>
<b>Version:</b> {package.version or 'N/A'}<br>
<b>Status:</b> {status_str}<br>
<b>Description:</b> {package.description or 'N/A'}<br>
<b>Root Directory:</b> {package.root_directory or 'N/A'}<br>
<b>Created:</b> {str(package.created_utc)[:19] if package.created_utc else 'N/A'}<br>
<b>Modified:</b> {str(package.modified_utc)[:19] if package.modified_utc else 'N/A'}<br>
"""
        self._details_label.setText(details)
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Populate files list
        self._files_list.clear()
        if hasattr(package, 'files') and package.files:
            for f in package.files:
                name = f.file_name if hasattr(f, 'file_name') else str(f)
                self._files_list.addItem(f"📄 {name}")
        else:
            self._files_list.addItem("(No files)")
    
    def _clear_details(self) -> None:
        """Clear the details panel"""
        self._details_label.setText("Select a package to view details")
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._files_list.clear()
        self._upload_btn.setEnabled(False)
        self._release_btn.setEnabled(False)
        self._revoke_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)
    
    def _on_filter_changed(self) -> None:
        """Handle filter changes - refresh displayed packages"""
        self._populate_packages_tree()
    
    def _on_create_package(self) -> None:
        """Show dialog to create new package"""
        if not self._main_window or not self._main_window.app.wats_client:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
            return
        
        dialog = PackageDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                client = self._main_window.app.wats_client
                
                # Create package
                result = client.software.create_package(
                    name=data['name'],
                    description=data.get('description'),
                    root_directory=data.get('rootDirectory'),
                    install_on_root=data.get('installOnRoot', False),
                )
                
                if result:
                    QMessageBox.information(self, "Success", f"Package '{data['name']}' created successfully in Draft status")
                    self._load_packages()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create package")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create package: {e}")
    
    def _on_upload_file(self) -> None:
        """Upload file to selected package as a zip"""
        if not self._selected_package:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Upload", "",
            "ZIP Files (*.zip);;All Files (*.*)"
        )
        
        if file_path:
            try:
                import zipfile
                import tempfile
                from pathlib import Path
                
                client = self._main_window.app.wats_client
                pkg_id = self._selected_package.package_id
                
                file_path_obj = Path(file_path)
                
                # Check if already a zip file
                if file_path_obj.suffix.lower() == '.zip':
                    # Use zip file directly
                    with open(file_path, 'rb') as f:
                        zip_content = f.read()
                else:
                    # Wrap single file in a zip
                    # Note: WATS requires files to be in a folder, not at root
                    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                        tmp_path = tmp.name
                    
                    try:
                        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                            # Put file in a subfolder (required by WATS API)
                            folder_name = "uploaded_files"
                            zf.write(file_path, f"{folder_name}/{file_path_obj.name}")
                        
                        with open(tmp_path, 'rb') as f:
                            zip_content = f.read()
                    finally:
                        Path(tmp_path).unlink(missing_ok=True)
                
                result = client.software.upload_zip(pkg_id, zip_content)
                
                if result:
                    QMessageBox.information(self, "Success", "File uploaded successfully")
                    self._load_packages()
                else:
                    QMessageBox.warning(self, "Error", "Failed to upload file")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload file: {e}")
    
    def _on_release_package(self) -> None:
        """Release the selected package"""
        if not self._selected_package:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Release",
            f"Are you sure you want to release package '{self._selected_package.name}'?\n\nThis will make it available for distribution.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                client = self._main_window.app.wats_client
                result = client.software.release_package(self._selected_package.package_id)
                
                if result:
                    QMessageBox.information(self, "Success", "Package released successfully")
                    self._load_packages()
                else:
                    QMessageBox.warning(self, "Error", "Failed to release package")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to release package: {e}")
    
    def _on_revoke_package(self) -> None:
        """Revoke the selected package"""
        if not self._selected_package:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Revoke",
            f"Are you sure you want to revoke package '{self._selected_package.name}'?\n\nThis will remove it from distribution.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                client = self._main_window.app.wats_client
                result = client.software.revoke_package(self._selected_package.package_id)
                
                if result:
                    QMessageBox.information(self, "Success", "Package revoked successfully")
                    self._load_packages()
                else:
                    QMessageBox.warning(self, "Error", "Failed to revoke package")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revoke package: {e}")
    
    def _on_delete_package(self) -> None:
        """Delete the selected package"""
        if not self._selected_package:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete package '{self._selected_package.name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                client = self._main_window.app.wats_client
                result = client.software.delete_package(self._selected_package.package_id)
                
                if result:
                    QMessageBox.information(self, "Success", "Package deleted successfully")
                    self._load_packages()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete package")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete package: {e}")
    def _on_refresh_packages(self) -> None:
        """Refresh packages from server"""
        if self._main_window and self._main_window.app.wats_client:
            self._load_packages()
        else:
            QMessageBox.warning(
                self, "Not Connected",
                "Please connect to WATS server first."
            )
    

    

    
    def _load_packages(self) -> None:
        """Load packages from WATS server"""
        try:
            self._status_label.setText("Loading packages...")
            self._progress_bar.setVisible(True)
            self._progress_bar.setRange(0, 0)  # Indeterminate
            print("[Software] Starting to load packages...")
            
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                print(f"[Software] WATS client available: {client}")
                # Get software packages from API
                packages = client.software.get_packages()
                print(f"[Software] Received {len(packages) if packages else 0} packages from API")
                if packages:
                    self._packages = packages
                    print(f"[Software] First package: {packages[0].name if packages else 'N/A'}")
                else:
                    self._packages = []
            else:
                print(f"[Software] No client - main_window: {self._main_window}, wats_client: {self._main_window.app.wats_client if self._main_window else None}")
                self._packages = []
            
            print(f"[Software] Populating tree with {len(self._packages)} packages")
            self._populate_packages_tree()
            self._progress_bar.setVisible(False)
            self._status_label.setText(f"Found {len(self._packages)} packages")
            
        except Exception as e:
            print(f"[Software] Error: {e}")
            import traceback
            traceback.print_exc()
            self._progress_bar.setVisible(False)
            self._status_label.setText(f"Error loading packages: {str(e)}")
    
    def _populate_packages_tree(self) -> None:
        """Populate packages tree with folders and filtered results"""
        search_text = self._search_edit.text().lower()
        status_filter = self._status_combo.currentText()
        
        self._packages_tree.clear()
        
        # Organize packages by virtual folder
        folders: Dict[str, List[Any]] = {}
        
        for pkg in self._packages:
            # Status filter
            if status_filter != "All":
                # Status might be enum or string
                if hasattr(pkg.status, 'value'):
                    pkg_status = str(pkg.status.value)
                else:
                    pkg_status = str(pkg.status) if pkg.status else ""
                if pkg_status.lower() != status_filter.lower():
                    continue
            
            # Search filter
            if search_text:
                name = (pkg.name or "").lower()
                desc = (pkg.description or "").lower()
                if search_text not in name and search_text not in desc:
                    continue
            
            # Get folder from tags or use "Uncategorized"
            folder_name = "Uncategorized"
            if pkg.tags:
                for tag in pkg.tags:
                    if hasattr(tag, 'key') and tag.key == "Folder":
                        folder_name = tag.value or "Uncategorized"
                        break
            
            if folder_name not in folders:
                folders[folder_name] = []
            folders[folder_name].append(pkg)
        
        # Create tree structure
        for folder_name in sorted(folders.keys()):
            # Create folder item
            folder_item = QTreeWidgetItem(self._packages_tree)
            folder_item.setText(0, f"📁 {folder_name}")
            folder_item.setExpanded(True)
            
            # Add packages to folder
            for pkg in folders[folder_name]:
                pkg_item = QTreeWidgetItem(folder_item)
                pkg_item.setText(0, pkg.name or "")
                pkg_item.setText(1, str(pkg.version) if pkg.version else "")
                
                # Status might be enum or string
                if hasattr(pkg.status, 'value'):
                    status_str = str(pkg.status.value)
                else:
                    status_str = str(pkg.status) if pkg.status else ""
                pkg_item.setText(2, status_str)
                
                modified = str(pkg.modified_utc)[:10] if pkg.modified_utc else ""
                pkg_item.setText(3, modified)
                
                # Store package data
                pkg_item.setData(0, Qt.ItemDataRole.UserRole, pkg)
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.software_auto_update = self._auto_update_cb.isChecked()
    
    def load_config(self) -> None:
        """Load configuration"""
        self._auto_update_cb.setChecked(
            getattr(self.config, 'software_auto_update', False)
        )

