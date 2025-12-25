"""
Converters Page

Displays and manages converter configurations with:
- Watch folder assignments
- Post-process actions (Move/Delete)
- Converter settings
"""

import re
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QPlainTextEdit,
    QFormLayout, QComboBox, QCheckBox, QGroupBox, QSpinBox,
    QDialogButtonBox, QTabWidget, QSplitter, QFrame, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .base import BasePage
from ...core.config import ClientConfig, ConverterConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ConverterSettingsDialog(QDialog):
    """Dialog for configuring a converter's watch folder and settings"""
    
    def __init__(
        self, 
        config: Optional[ConverterConfig] = None,
        converters_folder: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.converter_config = config
        self.converters_folder = converters_folder
        self.is_new = config is None
        
        self.setWindowTitle("Add Converter" if self.is_new else f"Configure: {config.name}")
        self.resize(600, 500)
        self.setModal(True)
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Tab widget for organized settings
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # === General Tab ===
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        general_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., CSV Test Converter")
        general_layout.addRow("Name:", self._name_edit)
        
        # Module path (converter class)
        module_layout = QHBoxLayout()
        self._module_edit = QLineEdit()
        self._module_edit.setPlaceholderText("e.g., csv_converter.CsvConverter")
        module_layout.addWidget(self._module_edit)
        self._browse_module_btn = QPushButton("...")
        self._browse_module_btn.setFixedWidth(30)
        self._browse_module_btn.clicked.connect(self._on_browse_module)
        module_layout.addWidget(self._browse_module_btn)
        general_layout.addRow("Module:", module_layout)
        
        # Enabled
        self._enabled_check = QCheckBox("Enabled")
        self._enabled_check.setChecked(True)
        general_layout.addRow("", self._enabled_check)
        
        # Converter type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["file", "folder", "scheduled"])
        general_layout.addRow("Type:", self._type_combo)
        
        # Description
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional description")
        general_layout.addRow("Description:", self._desc_edit)
        
        tabs.addTab(general_tab, "General")
        
        # === Folders Tab ===
        folders_tab = QWidget()
        folders_layout = QFormLayout(folders_tab)
        folders_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Watch folder
        watch_layout = QHBoxLayout()
        self._watch_edit = QLineEdit()
        self._watch_edit.setPlaceholderText("Folder to monitor for files")
        watch_layout.addWidget(self._watch_edit)
        self._browse_watch_btn = QPushButton("Browse...")
        self._browse_watch_btn.clicked.connect(lambda: self._browse_folder(self._watch_edit))
        watch_layout.addWidget(self._browse_watch_btn)
        folders_layout.addRow("Watch Folder:", watch_layout)
        
        # Done folder
        done_layout = QHBoxLayout()
        self._done_edit = QLineEdit()
        self._done_edit.setPlaceholderText("e.g., uploads/Done (or leave empty for auto)")
        done_layout.addWidget(self._done_edit)
        self._browse_done_btn = QPushButton("Browse...")
        self._browse_done_btn.clicked.connect(lambda: self._browse_folder(self._done_edit))
        done_layout.addWidget(self._browse_done_btn)
        folders_layout.addRow("Done Folder:", done_layout)
        
        # Error folder
        error_layout = QHBoxLayout()
        self._error_edit = QLineEdit()
        self._error_edit.setPlaceholderText("e.g., uploads/Error (or leave empty for auto)")
        error_layout.addWidget(self._error_edit)
        self._browse_error_btn = QPushButton("Browse...")
        self._browse_error_btn.clicked.connect(lambda: self._browse_folder(self._error_edit))
        error_layout.addWidget(self._browse_error_btn)
        folders_layout.addRow("Error Folder:", error_layout)
        
        # Pending folder
        pending_layout = QHBoxLayout()
        self._pending_edit = QLineEdit()
        self._pending_edit.setPlaceholderText("e.g., uploads/Pending (for retry)")
        pending_layout.addWidget(self._pending_edit)
        self._browse_pending_btn = QPushButton("Browse...")
        self._browse_pending_btn.clicked.connect(lambda: self._browse_folder(self._pending_edit))
        pending_layout.addWidget(self._browse_pending_btn)
        folders_layout.addRow("Pending Folder:", pending_layout)
        
        tabs.addTab(folders_tab, "Folders")
        
        # === Post-Process Tab ===
        postprocess_tab = QWidget()
        postprocess_layout = QFormLayout(postprocess_tab)
        
        # Post-process action
        self._action_combo = QComboBox()
        self._action_combo.addItems(["move", "delete", "archive", "keep"])
        self._action_combo.currentTextChanged.connect(self._on_action_changed)
        postprocess_layout.addRow("After Success:", self._action_combo)
        
        # Action descriptions
        action_desc = QLabel(
            "<b>move</b>: Move file to Done folder<br>"
            "<b>delete</b>: Permanently delete the file<br>"
            "<b>archive</b>: Move to archive folder (with date)<br>"
            "<b>keep</b>: Leave file in place (rename with suffix)"
        )
        action_desc.setStyleSheet("color: #808080; font-size: 11px;")
        action_desc.setWordWrap(True)
        postprocess_layout.addRow("", action_desc)
        
        # Archive folder (only for archive action)
        archive_layout = QHBoxLayout()
        self._archive_edit = QLineEdit()
        self._archive_edit.setPlaceholderText("Archive folder path")
        self._archive_edit.setEnabled(False)
        archive_layout.addWidget(self._archive_edit)
        self._browse_archive_btn = QPushButton("Browse...")
        self._browse_archive_btn.setEnabled(False)
        self._browse_archive_btn.clicked.connect(lambda: self._browse_folder(self._archive_edit))
        archive_layout.addWidget(self._browse_archive_btn)
        postprocess_layout.addRow("Archive Folder:", archive_layout)
        
        # Retry settings
        postprocess_layout.addRow(QLabel(""))  # Spacer
        postprocess_layout.addRow(QLabel("<b>Retry Settings</b>"))
        
        self._max_retries_spin = QSpinBox()
        self._max_retries_spin.setRange(0, 10)
        self._max_retries_spin.setValue(3)
        postprocess_layout.addRow("Max Retries:", self._max_retries_spin)
        
        self._retry_delay_spin = QSpinBox()
        self._retry_delay_spin.setRange(10, 3600)
        self._retry_delay_spin.setValue(60)
        self._retry_delay_spin.setSuffix(" seconds")
        postprocess_layout.addRow("Retry Delay:", self._retry_delay_spin)
        
        tabs.addTab(postprocess_tab, "Post-Process")
        
        # === File Patterns Tab ===
        patterns_tab = QWidget()
        patterns_layout = QFormLayout(patterns_tab)
        
        self._patterns_edit = QLineEdit()
        self._patterns_edit.setPlaceholderText("*.csv, *.txt, *.log")
        self._patterns_edit.setText("*.*")
        patterns_layout.addRow("File Patterns:", self._patterns_edit)
        
        patterns_help = QLabel(
            "Comma-separated list of file patterns to watch.\n"
            "Examples: *.csv, *.txt, test_*.log"
        )
        patterns_help.setStyleSheet("color: #808080; font-size: 11px;")
        patterns_layout.addRow("", patterns_help)
        
        # Validation thresholds
        patterns_layout.addRow(QLabel(""))
        patterns_layout.addRow(QLabel("<b>Validation Thresholds</b>"))
        
        self._alarm_spin = QSpinBox()
        self._alarm_spin.setRange(0, 100)
        self._alarm_spin.setValue(50)
        self._alarm_spin.setSuffix("%")
        patterns_layout.addRow("Alarm Below:", self._alarm_spin)
        
        self._reject_spin = QSpinBox()
        self._reject_spin.setRange(0, 100)
        self._reject_spin.setValue(20)
        self._reject_spin.setSuffix("%")
        patterns_layout.addRow("Reject Below:", self._reject_spin)
        
        threshold_help = QLabel(
            "Confidence scores below alarm threshold show warning.\n"
            "Scores below reject threshold are rejected."
        )
        threshold_help.setStyleSheet("color: #808080; font-size: 11px;")
        patterns_layout.addRow("", threshold_help)
        
        tabs.addTab(patterns_tab, "Patterns")
        
        # === Buttons ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_config(self) -> None:
        """Load existing configuration"""
        if not self.converter_config:
            return
        
        cfg = self.converter_config
        self._name_edit.setText(cfg.name)
        self._module_edit.setText(cfg.module_path)
        self._enabled_check.setChecked(cfg.enabled)
        self._type_combo.setCurrentText(cfg.converter_type)
        self._desc_edit.setText(cfg.description)
        
        self._watch_edit.setText(cfg.watch_folder)
        self._done_edit.setText(cfg.done_folder)
        self._error_edit.setText(cfg.error_folder)
        self._pending_edit.setText(cfg.pending_folder)
        
        self._action_combo.setCurrentText(cfg.post_action)
        self._archive_edit.setText(cfg.archive_folder)
        self._max_retries_spin.setValue(cfg.max_retries)
        self._retry_delay_spin.setValue(cfg.retry_delay_seconds)
        
        patterns = ", ".join(cfg.file_patterns) if cfg.file_patterns else "*.*"
        self._patterns_edit.setText(patterns)
        
        self._alarm_spin.setValue(int(cfg.alarm_threshold * 100))
        self._reject_spin.setValue(int(cfg.reject_threshold * 100))
    
    def _on_action_changed(self, action: str) -> None:
        """Handle post-action change"""
        is_archive = action == "archive"
        self._archive_edit.setEnabled(is_archive)
        self._browse_archive_btn.setEnabled(is_archive)
    
    def _browse_folder(self, line_edit: QLineEdit) -> None:
        """Browse for a folder"""
        current = line_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", current)
        if folder:
            line_edit.setText(folder)
    
    def _on_browse_module(self) -> None:
        """Browse for converter module"""
        if not self.converters_folder:
            QMessageBox.warning(self, "No Converters Folder", 
                               "Configure the converters folder first.")
            return
        
        folder = Path(self.converters_folder)
        if not folder.exists():
            QMessageBox.warning(self, "Folder Not Found", 
                               f"Converters folder not found:\n{folder}")
            return
        
        # Find available converter classes
        converters = []
        for py_file in folder.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                # Find class definitions that inherit from FileConverter or ConverterBase
                class_matches = re.findall(
                    r'class\s+(\w+)\s*\(\s*(?:FileConverter|ConverterBase)', 
                    content
                )
                for cls_name in class_matches:
                    module_name = py_file.stem
                    converters.append(f"{module_name}.{cls_name}")
            except Exception:
                pass
        
        if not converters:
            QMessageBox.information(self, "No Converters Found",
                                   "No valid converter classes found in the converters folder.")
            return
        
        # Show selection dialog
        item, ok = QInputDialog.getItem(
            self, "Select Converter", "Available converters:", 
            converters, 0, False
        )
        if ok and item:
            self._module_edit.setText(item)
    
    def _on_accept(self) -> None:
        """Validate and accept"""
        name = self._name_edit.text().strip()
        module = self._module_edit.text().strip()
        watch = self._watch_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return
        
        if not module:
            QMessageBox.warning(self, "Validation Error", "Module path is required.")
            return
        
        if not watch:
            QMessageBox.warning(self, "Validation Error", "Watch folder is required.")
            return
        
        self.accept()
    
    def get_config(self) -> ConverterConfig:
        """Get the configured ConverterConfig"""
        patterns = [p.strip() for p in self._patterns_edit.text().split(",") if p.strip()]
        
        return ConverterConfig(
            name=self._name_edit.text().strip(),
            module_path=self._module_edit.text().strip(),
            converter_type=self._type_combo.currentText(),
            enabled=self._enabled_check.isChecked(),
            watch_folder=self._watch_edit.text().strip(),
            done_folder=self._done_edit.text().strip(),
            error_folder=self._error_edit.text().strip(),
            pending_folder=self._pending_edit.text().strip(),
            post_action=self._action_combo.currentText(),
            archive_folder=self._archive_edit.text().strip(),
            max_retries=self._max_retries_spin.value(),
            retry_delay_seconds=self._retry_delay_spin.value(),
            file_patterns=patterns if patterns else ["*.*"],
            alarm_threshold=self._alarm_spin.value() / 100.0,
            reject_threshold=self._reject_spin.value() / 100.0,
            description=self._desc_edit.text().strip(),
        )


class ConverterEditorDialog(QDialog):
    """
    Dialog for viewing/editing converter source code.
    
    Uses the advanced ScriptEditorWidget with:
    - Tree view showing class structure
    - Function-by-function editing
    - Syntax highlighting
    - Base class method detection
    """
    
    def __init__(self, file_path: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.setWindowTitle(f"Converter Editor: {self.file_path.stem}")
        self.resize(1100, 800)
        
        self._setup_ui()
        self._load_converter()
    
    def _setup_ui(self) -> None:
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # File info header
        header_layout = QHBoxLayout()
        
        file_label = QLabel("File:")
        file_label.setStyleSheet("color: #808080;")
        header_layout.addWidget(file_label)
        
        self._path_label = QLabel(str(self.file_path))
        self._path_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        header_layout.addWidget(self._path_label)
        
        header_layout.addStretch()
        
        self._status_label = QLabel()
        header_layout.addWidget(self._status_label)
        
        layout.addLayout(header_layout)
        
        # Script editor widget (with tree view)
        from ..widgets import ScriptEditorWidget
        self._script_editor = ScriptEditorWidget()
        self._script_editor.content_changed.connect(self._on_content_changed)
        layout.addWidget(self._script_editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._save_btn = QPushButton("Save && Close")
        self._save_btn.clicked.connect(self._save_converter)
        self._save_btn.setEnabled(False)
        button_layout.addWidget(self._save_btn)
        
        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self._on_close)
        button_layout.addWidget(self._close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_converter(self) -> None:
        """Load converter from file"""
        try:
            if self._script_editor.load_file(str(self.file_path)):
                content = self._script_editor.get_source()
                
                # Check validity
                if "FileConverter" in content:
                    self._status_label.setText("✓ Valid FileConverter")
                    self._status_label.setStyleSheet("color: #4ec9b0;")
                elif "FolderConverter" in content:
                    self._status_label.setText("✓ Valid FolderConverter")
                    self._status_label.setStyleSheet("color: #4ec9b0;")
                elif "ScheduledConverter" in content:
                    self._status_label.setText("✓ Valid ScheduledConverter")
                    self._status_label.setStyleSheet("color: #4ec9b0;")
                elif "ConverterBase" in content:
                    self._status_label.setText("✓ Valid ConverterBase (legacy)")
                    self._status_label.setStyleSheet("color: #dcdcaa;")
                else:
                    self._status_label.setText("⚠ Not a valid converter class")
                    self._status_label.setStyleSheet("color: #dcdcaa;")
            else:
                self._status_label.setText("✗ Failed to load file")
                self._status_label.setStyleSheet("color: #f14c4c;")
                
        except Exception as e:
            self._status_label.setText(f"✗ Error: {str(e)}")
            self._status_label.setStyleSheet("color: #f14c4c;")
    
    def _on_content_changed(self) -> None:
        """Handle content change"""
        self._save_btn.setEnabled(True)
        self.setWindowTitle(f"Converter Editor: {self.file_path.stem} *")
    
    def _save_converter(self) -> None:
        """Save converter to file"""
        try:
            if self._script_editor.save():
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Converter saved to:\n{self.file_path}"
                )
                self._save_btn.setEnabled(False)
                self.setWindowTitle(f"Converter Editor: {self.file_path.stem}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save converter:\n{str(e)}"
            )
    
    def _on_close(self) -> None:
        """Handle close button"""
        if self._script_editor.is_modified():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._save_converter()
                self.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                self.reject()
            # Cancel does nothing
        else:
            self.reject()


class ConvertersPage(BasePage):
    """Converters management page with configuration support"""
    
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
        return "Converters"
    
    def _setup_ui(self) -> None:
        """Setup page UI"""
        # === Converters folder section ===
        folder_group = QGroupBox("Converters Folder")
        folder_layout = QHBoxLayout(folder_group)
        
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText("Path to folder containing converter .py files")
        self._folder_edit.textChanged.connect(self._emit_changed)
        folder_layout.addWidget(self._folder_edit, 1)
        
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._on_browse_folder)
        folder_layout.addWidget(self._browse_btn)
        
        self._layout.addWidget(folder_group)
        
        help_label = QLabel(
            "Place Python modules (.py files) implementing FileConverter in this folder.\n"
            "Then add configurations below to assign watch folders and settings."
        )
        help_label.setStyleSheet("color: #808080; font-size: 11px;")
        self._layout.addWidget(help_label)
        
        self._layout.addSpacing(10)
        
        # === Converter Configurations Table ===
        config_group = QGroupBox("Converter Configurations")
        config_layout = QVBoxLayout(config_group)
        
        self._config_table = QTableWidget()
        self._config_table.setColumnCount(6)
        self._config_table.setHorizontalHeaderLabels([
            "Enabled", "Name", "Watch Folder", "Post-Action", "Module", "Status"
        ])
        
        # Column sizes
        header = self._config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self._config_table.setColumnWidth(1, 150)
        self._config_table.setColumnWidth(4, 200)
        
        self._config_table.verticalHeader().setVisible(False)
        self._config_table.setAlternatingRowColors(True)
        self._config_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._config_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._config_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._config_table.doubleClicked.connect(self._on_configure)
        self._config_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        config_layout.addWidget(self._config_table)
        
        # Buttons for configurations
        config_btn_layout = QHBoxLayout()
        
        self._add_btn = QPushButton("Add...")
        self._add_btn.clicked.connect(self._on_add)
        config_btn_layout.addWidget(self._add_btn)
        
        self._configure_btn = QPushButton("Configure...")
        self._configure_btn.setEnabled(False)
        self._configure_btn.clicked.connect(self._on_configure)
        config_btn_layout.addWidget(self._configure_btn)
        
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._on_remove)
        config_btn_layout.addWidget(self._remove_btn)
        
        config_btn_layout.addStretch()
        
        self._edit_code_btn = QPushButton("Edit Code...")
        self._edit_code_btn.setEnabled(False)
        self._edit_code_btn.clicked.connect(self._on_view_code)
        config_btn_layout.addWidget(self._edit_code_btn)
        
        config_layout.addLayout(config_btn_layout)
        
        self._layout.addWidget(config_group, 1)
        
        # === Available Converters (from folder) ===
        available_group = QGroupBox("Available Converters (in folder)")
        available_layout = QVBoxLayout(available_group)
        
        self._available_table = QTableWidget()
        self._available_table.setColumnCount(4)
        self._available_table.setHorizontalHeaderLabels([
            "Module", "Class", "Status", "File"
        ])
        
        avail_header = self._available_table.horizontalHeader()
        avail_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        avail_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        avail_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        avail_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self._available_table.setColumnWidth(0, 150)
        self._available_table.setColumnWidth(1, 150)
        
        self._available_table.verticalHeader().setVisible(False)
        self._available_table.setAlternatingRowColors(True)
        self._available_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._available_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._available_table.setMaximumHeight(150)
        
        available_layout.addWidget(self._available_table)
        
        # Buttons for available converters
        avail_btn_layout = QHBoxLayout()
        
        self._new_converter_btn = QPushButton("New Converter...")
        self._new_converter_btn.clicked.connect(self._on_new_converter)
        avail_btn_layout.addWidget(self._new_converter_btn)
        
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_available)
        avail_btn_layout.addWidget(self._refresh_btn)
        
        avail_btn_layout.addStretch()
        available_layout.addLayout(avail_btn_layout)
        
        self._layout.addWidget(available_group)
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.converters_folder = self._folder_edit.text()
        # Converters are already updated in _on_add, _on_configure, _on_remove
    
    def load_config(self) -> None:
        """Load configuration"""
        self._folder_edit.setText(self.config.converters_folder)
        self._refresh_config_table()
        self._refresh_available()
    
    def _on_browse_folder(self) -> None:
        """Browse for converters folder"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Converters Folder",
            self._folder_edit.text() or str(Path.home())
        )
        if folder:
            self._folder_edit.setText(folder)
            self._emit_changed()
            self._refresh_available()
    
    def _on_selection_changed(self) -> None:
        """Handle table selection change"""
        has_selection = len(self._config_table.selectedItems()) > 0
        self._configure_btn.setEnabled(has_selection)
        self._remove_btn.setEnabled(has_selection)
        self._edit_code_btn.setEnabled(has_selection)
    
    def _on_new_converter(self) -> None:
        """Create a new converter from template"""
        folder = self._folder_edit.text()
        if not folder:
            QMessageBox.warning(
                self, "No Folder",
                "Please configure a converters folder first."
            )
            return
        
        folder_path = Path(folder)
        if not folder_path.exists():
            reply = QMessageBox.question(
                self, "Create Folder?",
                f"Folder does not exist:\n{folder}\n\nCreate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                folder_path.mkdir(parents=True, exist_ok=True)
            else:
                return
        
        from ..widgets import NewConverterDialog
        dialog = NewConverterDialog(
            converters_folder=folder,
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.created_path:
            # Refresh the available converters list
            self._refresh_available()
            
            # Open the new converter in the editor
            editor_dialog = ConverterEditorDialog(str(dialog.created_path), self)
            editor_dialog.exec()
    
    def _on_add(self) -> None:
        """Add new converter configuration"""
        dialog = ConverterSettingsDialog(
            config=None,
            converters_folder=self._folder_edit.text(),
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            
            # Check for duplicate names
            for cfg in self.config.converters:
                if cfg.name == new_config.name:
                    QMessageBox.warning(
                        self, "Duplicate Name",
                        f"A converter named '{new_config.name}' already exists."
                    )
                    return
            
            self.config.converters.append(new_config)
            self._refresh_config_table()
            self._emit_changed()
    
    def _on_configure(self) -> None:
        """Configure selected converter"""
        row = self._get_selected_row()
        if row < 0:
            return
        
        cfg = self.config.converters[row]
        dialog = ConverterSettingsDialog(
            config=cfg,
            converters_folder=self._folder_edit.text(),
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config.converters[row] = dialog.get_config()
            self._refresh_config_table()
            self._emit_changed()
    
    def _on_remove(self) -> None:
        """Remove selected converter configuration"""
        row = self._get_selected_row()
        if row < 0:
            return
        
        cfg = self.config.converters[row]
        reply = QMessageBox.question(
            self, "Confirm Remove",
            f"Remove converter configuration '{cfg.name}'?\n\n"
            "This only removes the configuration, not the converter file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.config.converters[row]
            self._refresh_config_table()
            self._emit_changed()
    
    def _on_view_code(self) -> None:
        """View converter source code"""
        row = self._get_selected_row()
        if row < 0:
            return
        
        cfg = self.config.converters[row]
        
        # Find the converter file
        folder = Path(self._folder_edit.text())
        module_name = cfg.module_path.split(".")[0] if "." in cfg.module_path else cfg.module_path
        file_path = folder / f"{module_name}.py"
        
        if not file_path.exists():
            QMessageBox.warning(
                self, "File Not Found",
                f"Converter file not found:\n{file_path}"
            )
            return
        
        dialog = ConverterEditorDialog(str(file_path), self)
        dialog.exec()
    
    def _get_selected_row(self) -> int:
        """Get selected row index"""
        selected = self._config_table.selectedItems()
        if not selected:
            return -1
        return selected[0].row()
    
    def _refresh_config_table(self) -> None:
        """Refresh the converter configurations table"""
        self._config_table.setRowCount(0)
        
        for row, cfg in enumerate(self.config.converters):
            self._config_table.insertRow(row)
            
            # Enabled checkbox
            enabled_item = QTableWidgetItem()
            enabled_item.setCheckState(
                Qt.CheckState.Checked if cfg.enabled else Qt.CheckState.Unchecked
            )
            self._config_table.setItem(row, 0, enabled_item)
            
            # Name
            self._config_table.setItem(row, 1, QTableWidgetItem(cfg.name))
            
            # Watch folder
            self._config_table.setItem(row, 2, QTableWidgetItem(cfg.watch_folder))
            
            # Post-action
            action_item = QTableWidgetItem(cfg.post_action.capitalize())
            if cfg.post_action == "delete":
                action_item.setForeground(QColor("#f14c4c"))
            elif cfg.post_action == "move":
                action_item.setForeground(QColor("#4ec9b0"))
            self._config_table.setItem(row, 3, action_item)
            
            # Module
            self._config_table.setItem(row, 4, QTableWidgetItem(cfg.module_path))
            
            # Status (check if module exists)
            status = self._check_converter_status(cfg)
            status_item = QTableWidgetItem(status)
            if "OK" in status:
                status_item.setForeground(QColor("#4ec9b0"))
            elif "Error" in status or "Not Found" in status:
                status_item.setForeground(QColor("#f14c4c"))
            else:
                status_item.setForeground(QColor("#dcdcaa"))
            self._config_table.setItem(row, 5, status_item)
    
    def _check_converter_status(self, cfg: ConverterConfig) -> str:
        """Check if converter module exists and is valid"""
        folder = Path(self._folder_edit.text())
        if not folder.exists():
            return "Folder not found"
        
        module_name = cfg.module_path.split(".")[0] if "." in cfg.module_path else cfg.module_path
        file_path = folder / f"{module_name}.py"
        
        if not file_path.exists():
            return "Not Found"
        
        try:
            content = file_path.read_text(encoding='utf-8')
            if "FileConverter" in content or "ConverterBase" in content:
                return "OK"
            else:
                return "Invalid"
        except Exception as e:
            return f"Error: {e}"
    
    def _refresh_available(self) -> None:
        """Refresh the available converters table"""
        self._available_table.setRowCount(0)
        
        folder = self._folder_edit.text()
        if not folder:
            return
        
        folder_path = Path(folder)
        if not folder_path.exists():
            return
        
        row = 0
        for py_file in folder_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Find class definitions
                class_matches = re.findall(
                    r'class\s+(\w+)\s*\(\s*(?:FileConverter|ConverterBase)',
                    content
                )
                
                if not class_matches:
                    # Still show the file but mark as invalid
                    self._available_table.insertRow(row)
                    self._available_table.setItem(row, 0, QTableWidgetItem(py_file.stem))
                    self._available_table.setItem(row, 1, QTableWidgetItem("-"))
                    
                    status_item = QTableWidgetItem("No converter class")
                    status_item.setForeground(QColor("#dcdcaa"))
                    self._available_table.setItem(row, 2, status_item)
                    self._available_table.setItem(row, 3, QTableWidgetItem(str(py_file)))
                    row += 1
                else:
                    for cls_name in class_matches:
                        self._available_table.insertRow(row)
                        self._available_table.setItem(row, 0, QTableWidgetItem(py_file.stem))
                        self._available_table.setItem(row, 1, QTableWidgetItem(cls_name))
                        
                        status_item = QTableWidgetItem("Valid")
                        status_item.setForeground(QColor("#4ec9b0"))
                        self._available_table.setItem(row, 2, status_item)
                        self._available_table.setItem(row, 3, QTableWidgetItem(str(py_file)))
                        row += 1
                        
            except Exception as e:
                self._available_table.insertRow(row)
                self._available_table.setItem(row, 0, QTableWidgetItem(py_file.stem))
                self._available_table.setItem(row, 1, QTableWidgetItem("-"))
                
                status_item = QTableWidgetItem(f"Error: {e}")
                status_item.setForeground(QColor("#f14c4c"))
                self._available_table.setItem(row, 2, status_item)
                self._available_table.setItem(row, 3, QTableWidgetItem(str(py_file)))
                row += 1
