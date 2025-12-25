"""
Converters Page V2

Unified converter management with:
- Single list showing both system and user converters
- System converters are read-only but can be customized (forked)
- Versioning support for converters
- Auto-generated folder structure based on watch folder
"""

import re
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QPlainTextEdit,
    QFormLayout, QComboBox, QCheckBox, QGroupBox, QSpinBox,
    QDialogButtonBox, QTabWidget, QSplitter, QFrame, QInputDialog,
    QMenu, QToolButton, QStyle
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction, QIcon

from .base import BasePage
from ...core.config import ClientConfig, ConverterConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ConverterSource(Enum):
    """Where the converter comes from"""
    SYSTEM = "system"      # Installed with package (read-only)
    USER = "user"          # User-created converter
    CUSTOMIZED = "custom"  # User customization of system converter


@dataclass
class ConverterInfo:
    """Information about an available converter"""
    name: str
    class_name: str
    module_path: str       # Full module path for import
    file_path: Path        # Actual file location
    source: ConverterSource
    version: str = "1.0.0"
    description: str = ""
    file_patterns: List[str] = None
    is_configured: bool = False  # Has active configuration
    config: Optional[ConverterConfig] = None
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.*"]


def get_system_converters() -> List[ConverterInfo]:
    """Get list of system converters installed with the package"""
    converters = []
    
    try:
        from ...converters.standard import (
            KitronSeicaXMLConverter,
            TeradyneICTConverter,
            TerradyneSpectrumICTConverter,
            WATSStandardTextConverter,
            WATSStandardJsonConverter,
            WATSStandardXMLConverter,
        )
        
        # Get the actual module path
        import pywats_client.converters.standard as std_module
        std_path = Path(std_module.__file__).parent
        
        system_converters = [
            ("Kitron/Seica XML", "KitronSeicaXMLConverter", "kitron_seica_xml_converter", 
             "1.0.0", "Kitron/Seica Flying Probe XML format", ["*.xml"]),
            ("Teradyne ICT", "TeradyneICTConverter", "teradyne_ict_converter",
             "1.0.0", "Teradyne i3070 ICT format", ["*.txt", "*.log"]),
            ("Teradyne Spectrum ICT", "TerradyneSpectrumICTConverter", "teradyne_spectrum_ict_converter",
             "1.0.0", "Teradyne Spectrum ICT format", ["*.txt", "*.log"]),
            ("WATS Standard Text", "WATSStandardTextConverter", "wats_standard_text_converter",
             "1.0.0", "WATS Standard Text Format (tab-delimited)", ["*.txt"]),
            ("WATS Standard JSON", "WATSStandardJsonConverter", "wats_standard_json_converter",
             "1.0.0", "WATS Standard JSON Format (WSJF)", ["*.json"]),
            ("WATS Standard XML", "WATSStandardXMLConverter", "wats_standard_xml_converter",
             "1.0.0", "WATS Standard XML Format (WSXF/WRML)", ["*.xml"]),
        ]
        
        for name, cls_name, module_name, version, desc, patterns in system_converters:
            file_path = std_path / f"{module_name}.py"
            if file_path.exists():
                converters.append(ConverterInfo(
                    name=name,
                    class_name=cls_name,
                    module_path=f"pywats_client.converters.standard.{module_name}.{cls_name}",
                    file_path=file_path,
                    source=ConverterSource.SYSTEM,
                    version=version,
                    description=desc,
                    file_patterns=patterns,
                ))
    except ImportError:
        pass
    
    return converters


def get_user_converters(user_folder: Path) -> List[ConverterInfo]:
    """Get list of user converters from the converters folder"""
    converters = []
    
    if not user_folder or not user_folder.exists():
        return converters
    
    for py_file in user_folder.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            
            # Find converter classes
            class_matches = re.findall(
                r'class\s+(\w+)\s*\(\s*(?:FileConverter|FolderConverter|ScheduledConverter|ConverterBase)',
                content
            )
            
            # Extract version from docstring or property
            version_match = re.search(r'version\s*[=:]\s*["\']([^"\']+)["\']', content)
            version = version_match.group(1) if version_match else "1.0.0"
            
            # Extract description
            desc_match = re.search(r'"""([^"]+)"""', content)
            desc = desc_match.group(1).strip().split('\n')[0] if desc_match else ""
            
            # Check if it's a customized system converter
            is_custom = "# Customized from:" in content or "# Based on:" in content
            
            for cls_name in class_matches:
                converters.append(ConverterInfo(
                    name=cls_name.replace("Converter", " Converter"),
                    class_name=cls_name,
                    module_path=f"{py_file.stem}.{cls_name}",
                    file_path=py_file,
                    source=ConverterSource.CUSTOMIZED if is_custom else ConverterSource.USER,
                    version=version,
                    description=desc,
                ))
                
        except Exception:
            pass
    
    return converters


class ConverterSettingsDialogV2(QDialog):
    """
    Dialog for configuring a converter instance.
    
    Features:
    - Auto-generates folder structure based on watch folder
    - Shows converter source (system/user/custom)
    - Version display
    """
    
    def __init__(
        self, 
        converter_info: Optional[ConverterInfo] = None,
        config: Optional[ConverterConfig] = None,
        user_folder: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.converter_info = converter_info
        self.converter_config = config
        self.user_folder = Path(user_folder) if user_folder else None
        self.is_new = config is None
        
        title = "Add Converter Configuration"
        if converter_info:
            title = f"Configure: {converter_info.name}"
        elif config:
            title = f"Configure: {config.name}"
        
        self.setWindowTitle(title)
        self.resize(650, 550)
        self.setModal(True)
        
        self._setup_ui()
        self._load_config()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Converter info header (if we have converter_info)
        if self.converter_info:
            info_group = QGroupBox("Converter")
            info_layout = QFormLayout(info_group)
            
            # Name and source
            source_text = {
                ConverterSource.SYSTEM: "📦 System (read-only)",
                ConverterSource.USER: "👤 User",
                ConverterSource.CUSTOMIZED: "🔧 Customized",
            }.get(self.converter_info.source, "Unknown")
            
            name_label = QLabel(f"<b>{self.converter_info.name}</b>  <span style='color:#808080'>{source_text}</span>")
            info_layout.addRow("Converter:", name_label)
            
            version_label = QLabel(self.converter_info.version)
            info_layout.addRow("Version:", version_label)
            
            if self.converter_info.description:
                desc_label = QLabel(self.converter_info.description)
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("color: #808080;")
                info_layout.addRow("", desc_label)
            
            layout.addWidget(info_group)
        
        # Tab widget for settings
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # === General Tab ===
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        general_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Configuration name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Production Line 1 CSV")
        if self.converter_info:
            self._name_edit.setText(self.converter_info.name)
        general_layout.addRow("Configuration Name:", self._name_edit)
        
        # Enabled
        self._enabled_check = QCheckBox("Enabled")
        self._enabled_check.setChecked(True)
        general_layout.addRow("", self._enabled_check)
        
        # Module (read-only if from converter_info)
        self._module_edit = QLineEdit()
        if self.converter_info:
            self._module_edit.setText(self.converter_info.module_path)
            self._module_edit.setReadOnly(True)
            self._module_edit.setStyleSheet("background-color: #2d2d2d;")
        else:
            self._module_edit.setPlaceholderText("e.g., my_converter.MyConverter")
        general_layout.addRow("Module:", self._module_edit)
        
        # Converter type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["file", "folder", "scheduled"])
        general_layout.addRow("Type:", self._type_combo)
        
        # Description
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional description for this configuration")
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
        self._watch_edit.textChanged.connect(self._on_watch_folder_changed)
        watch_layout.addWidget(self._watch_edit)
        self._browse_watch_btn = QPushButton("Browse...")
        self._browse_watch_btn.clicked.connect(lambda: self._browse_folder(self._watch_edit))
        watch_layout.addWidget(self._browse_watch_btn)
        folders_layout.addRow("Watch Folder:", watch_layout)
        
        # Auto-generate checkbox
        self._auto_folders_check = QCheckBox("Auto-generate subfolders (Done, Error, Pending)")
        self._auto_folders_check.setChecked(True)
        self._auto_folders_check.stateChanged.connect(self._on_auto_folders_changed)
        folders_layout.addRow("", self._auto_folders_check)
        
        # Folder preview
        self._folder_preview = QLabel()
        self._folder_preview.setStyleSheet("color: #4ec9b0; font-size: 11px;")
        self._folder_preview.setWordWrap(True)
        folders_layout.addRow("", self._folder_preview)
        
        folders_layout.addRow(QLabel(""))  # Spacer
        folders_layout.addRow(QLabel("<b>Custom Folders</b> (override auto-generate)"))
        
        # Done folder
        done_layout = QHBoxLayout()
        self._done_edit = QLineEdit()
        self._done_edit.setPlaceholderText("Leave empty to use Watch/Done")
        done_layout.addWidget(self._done_edit)
        self._browse_done_btn = QPushButton("...")
        self._browse_done_btn.setFixedWidth(30)
        self._browse_done_btn.clicked.connect(lambda: self._browse_folder(self._done_edit))
        done_layout.addWidget(self._browse_done_btn)
        folders_layout.addRow("Done:", done_layout)
        
        # Error folder
        error_layout = QHBoxLayout()
        self._error_edit = QLineEdit()
        self._error_edit.setPlaceholderText("Leave empty to use Watch/Error")
        error_layout.addWidget(self._error_edit)
        self._browse_error_btn = QPushButton("...")
        self._browse_error_btn.setFixedWidth(30)
        self._browse_error_btn.clicked.connect(lambda: self._browse_folder(self._error_edit))
        error_layout.addWidget(self._browse_error_btn)
        folders_layout.addRow("Error:", error_layout)
        
        # Pending folder
        pending_layout = QHBoxLayout()
        self._pending_edit = QLineEdit()
        self._pending_edit.setPlaceholderText("Leave empty to use Watch/Pending")
        pending_layout.addWidget(self._pending_edit)
        self._browse_pending_btn = QPushButton("...")
        self._browse_pending_btn.setFixedWidth(30)
        self._browse_pending_btn.clicked.connect(lambda: self._browse_folder(self._pending_edit))
        pending_layout.addWidget(self._browse_pending_btn)
        folders_layout.addRow("Pending:", pending_layout)
        
        tabs.addTab(folders_tab, "Folders")
        
        # === Post-Process Tab ===
        postprocess_tab = QWidget()
        postprocess_layout = QFormLayout(postprocess_tab)
        
        self._action_combo = QComboBox()
        self._action_combo.addItems(["move", "delete", "archive", "keep"])
        postprocess_layout.addRow("After Success:", self._action_combo)
        
        action_desc = QLabel(
            "<b>move</b>: Move file to Done folder<br>"
            "<b>delete</b>: Permanently delete the file<br>"
            "<b>archive</b>: Move to archive folder (with date)<br>"
            "<b>keep</b>: Leave file in place (rename with suffix)"
        )
        action_desc.setStyleSheet("color: #808080; font-size: 11px;")
        action_desc.setWordWrap(True)
        postprocess_layout.addRow("", action_desc)
        
        postprocess_layout.addRow(QLabel(""))
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
        
        # === Patterns Tab ===
        patterns_tab = QWidget()
        patterns_layout = QFormLayout(patterns_tab)
        
        self._patterns_edit = QLineEdit()
        if self.converter_info and self.converter_info.file_patterns:
            self._patterns_edit.setText(", ".join(self.converter_info.file_patterns))
        else:
            self._patterns_edit.setText("*.*")
        patterns_layout.addRow("File Patterns:", self._patterns_edit)
        
        patterns_help = QLabel(
            "Comma-separated list of file patterns.\n"
            "Examples: *.csv, *.txt, test_*.log"
        )
        patterns_help.setStyleSheet("color: #808080; font-size: 11px;")
        patterns_layout.addRow("", patterns_help)
        
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
        
        tabs.addTab(patterns_tab, "Patterns")
        
        # === Buttons ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _connect_signals(self) -> None:
        """Connect signals"""
        self._on_auto_folders_changed(self._auto_folders_check.checkState())
    
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
        
        # Check if folders are custom or auto-generated
        watch = Path(cfg.watch_folder) if cfg.watch_folder else None
        is_auto = True
        if watch and cfg.done_folder:
            expected_done = str(watch / "Done")
            if cfg.done_folder != expected_done:
                is_auto = False
        
        self._auto_folders_check.setChecked(is_auto)
        
        if not is_auto:
            self._done_edit.setText(cfg.done_folder)
            self._error_edit.setText(cfg.error_folder)
            self._pending_edit.setText(cfg.pending_folder)
        
        self._action_combo.setCurrentText(cfg.post_action)
        self._max_retries_spin.setValue(cfg.max_retries)
        self._retry_delay_spin.setValue(cfg.retry_delay_seconds)
        
        patterns = ", ".join(cfg.file_patterns) if cfg.file_patterns else "*.*"
        self._patterns_edit.setText(patterns)
        
        self._alarm_spin.setValue(int(cfg.alarm_threshold * 100))
        self._reject_spin.setValue(int(cfg.reject_threshold * 100))
    
    def _browse_folder(self, line_edit: QLineEdit) -> None:
        """Browse for a folder"""
        current = line_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", current)
        if folder:
            line_edit.setText(folder)
    
    def _on_watch_folder_changed(self, text: str) -> None:
        """Update folder preview when watch folder changes"""
        self._update_folder_preview()
    
    def _on_auto_folders_changed(self, state) -> None:
        """Toggle custom folder fields"""
        is_auto = self._auto_folders_check.isChecked()
        self._done_edit.setEnabled(not is_auto)
        self._error_edit.setEnabled(not is_auto)
        self._pending_edit.setEnabled(not is_auto)
        self._browse_done_btn.setEnabled(not is_auto)
        self._browse_error_btn.setEnabled(not is_auto)
        self._browse_pending_btn.setEnabled(not is_auto)
        
        if is_auto:
            self._done_edit.clear()
            self._error_edit.clear()
            self._pending_edit.clear()
        
        self._update_folder_preview()
    
    def _update_folder_preview(self) -> None:
        """Update folder structure preview"""
        watch = self._watch_edit.text().strip()
        if not watch:
            self._folder_preview.setText("")
            return
        
        if self._auto_folders_check.isChecked():
            preview = (
                f"📁 {watch}\n"
                f"   ├── 📁 Done\n"
                f"   ├── 📁 Error\n"
                f"   └── 📁 Pending"
            )
            self._folder_preview.setText(preview)
        else:
            done = self._done_edit.text() or f"{watch}/Done"
            error = self._error_edit.text() or f"{watch}/Error"
            pending = self._pending_edit.text() or f"{watch}/Pending"
            preview = f"Done: {done}\nError: {error}\nPending: {pending}"
            self._folder_preview.setText(preview)
    
    def _on_accept(self) -> None:
        """Validate and accept"""
        name = self._name_edit.text().strip()
        module = self._module_edit.text().strip()
        watch = self._watch_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation", "Configuration name is required.")
            return
        
        if not module:
            QMessageBox.warning(self, "Validation", "Module path is required.")
            return
        
        converter_type = self._type_combo.currentText()
        if converter_type in ("file", "folder") and not watch:
            QMessageBox.warning(self, "Validation", "Watch folder is required.")
            return
        
        # Create folders
        if watch:
            watch_path = Path(watch)
            try:
                watch_path.mkdir(parents=True, exist_ok=True)
                
                if self._auto_folders_check.isChecked():
                    (watch_path / "Done").mkdir(exist_ok=True)
                    (watch_path / "Error").mkdir(exist_ok=True)
                    (watch_path / "Pending").mkdir(exist_ok=True)
                else:
                    # Create custom folders
                    for edit in [self._done_edit, self._error_edit, self._pending_edit]:
                        folder = edit.text().strip()
                        if folder:
                            Path(folder).mkdir(parents=True, exist_ok=True)
                
            except Exception as e:
                QMessageBox.warning(
                    self, "Folder Error",
                    f"Failed to create folders:\n{e}"
                )
                return
        
        self.accept()
    
    def get_config(self) -> ConverterConfig:
        """Get the configured ConverterConfig"""
        watch = self._watch_edit.text().strip()
        watch_path = Path(watch) if watch else None
        
        # Determine folder paths
        if self._auto_folders_check.isChecked() and watch_path:
            done = str(watch_path / "Done")
            error = str(watch_path / "Error")
            pending = str(watch_path / "Pending")
        else:
            done = self._done_edit.text().strip() or (str(watch_path / "Done") if watch_path else "")
            error = self._error_edit.text().strip() or (str(watch_path / "Error") if watch_path else "")
            pending = self._pending_edit.text().strip() or (str(watch_path / "Pending") if watch_path else "")
        
        patterns = [p.strip() for p in self._patterns_edit.text().split(",") if p.strip()]
        
        return ConverterConfig(
            name=self._name_edit.text().strip(),
            module_path=self._module_edit.text().strip(),
            converter_type=self._type_combo.currentText(),
            enabled=self._enabled_check.isChecked(),
            watch_folder=watch,
            done_folder=done,
            error_folder=error,
            pending_folder=pending,
            post_action=self._action_combo.currentText(),
            max_retries=self._max_retries_spin.value(),
            retry_delay_seconds=self._retry_delay_spin.value(),
            file_patterns=patterns if patterns else ["*.*"],
            alarm_threshold=self._alarm_spin.value() / 100.0,
            reject_threshold=self._reject_spin.value() / 100.0,
            description=self._desc_edit.text().strip(),
            version=self.converter_info.version if self.converter_info else "1.0.0",
        )


class ConverterEditorDialogV2(QDialog):
    """
    Dialog for viewing/editing converter source code.
    
    Uses the advanced ScriptEditorWidget with:
    - Tree view showing class structure
    - Function-by-function editing
    - Syntax highlighting
    - Version tracking
    """
    
    def __init__(
        self, 
        converter_info: ConverterInfo,
        user_folder: Path,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.converter_info = converter_info
        self.user_folder = user_folder
        self.is_system = converter_info.source == ConverterSource.SYSTEM
        
        title = f"{'View' if self.is_system else 'Edit'}: {converter_info.name}"
        if converter_info.version:
            title += f" v{converter_info.version}"
        
        self.setWindowTitle(title)
        self.resize(1100, 800)
        
        self._setup_ui()
        self._load_converter()
    
    def _setup_ui(self) -> None:
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with converter info
        header_layout = QHBoxLayout()
        
        # Source indicator
        source_icons = {
            ConverterSource.SYSTEM: ("📦", "#569cd6", "System Converter (read-only)"),
            ConverterSource.USER: ("👤", "#4ec9b0", "User Converter"),
            ConverterSource.CUSTOMIZED: ("🔧", "#dcdcaa", "Customized Converter"),
        }
        icon, color, tooltip = source_icons.get(
            self.converter_info.source, 
            ("?", "#808080", "Unknown")
        )
        
        source_label = QLabel(f"{icon} <b>{self.converter_info.name}</b>")
        source_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        source_label.setToolTip(tooltip)
        header_layout.addWidget(source_label)
        
        header_layout.addStretch()
        
        # Version
        version_label = QLabel(f"v{self.converter_info.version}")
        version_label.setStyleSheet("color: #808080;")
        header_layout.addWidget(version_label)
        
        layout.addLayout(header_layout)
        
        # Info banner for system converters
        if self.is_system:
            banner = QLabel(
                "⚠️ This is a system converter and cannot be edited directly. "
                "Click 'Customize...' to create an editable copy."
            )
            banner.setStyleSheet(
                "background-color: #3d3d00; color: #dcdcaa; "
                "padding: 10px; border-radius: 4px;"
            )
            banner.setWordWrap(True)
            layout.addWidget(banner)
        
        # Script editor
        from ..widgets import ScriptEditorWidget
        self._script_editor = ScriptEditorWidget()
        self._script_editor.content_changed.connect(self._on_content_changed)
        layout.addWidget(self._script_editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        if self.is_system:
            self._customize_btn = QPushButton("Customize...")
            self._customize_btn.setToolTip("Create an editable copy of this converter")
            self._customize_btn.clicked.connect(self._on_customize)
            button_layout.addWidget(self._customize_btn)
        
        button_layout.addStretch()
        
        if not self.is_system:
            self._save_btn = QPushButton("Save")
            self._save_btn.clicked.connect(self._on_save)
            self._save_btn.setEnabled(False)
            button_layout.addWidget(self._save_btn)
            
            self._save_version_btn = QPushButton("Save as New Version...")
            self._save_version_btn.clicked.connect(self._on_save_new_version)
            button_layout.addWidget(self._save_version_btn)
        
        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self._on_close)
        button_layout.addWidget(self._close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_converter(self) -> None:
        """Load converter source"""
        if self._script_editor.load_file(str(self.converter_info.file_path)):
            if self.is_system:
                # Make editor read-only for system converters
                self._script_editor._code_editor.setReadOnly(True)
    
    def _on_content_changed(self) -> None:
        """Handle content change"""
        if hasattr(self, '_save_btn'):
            self._save_btn.setEnabled(True)
            self.setWindowTitle(f"Edit: {self.converter_info.name} *")
    
    def _on_save(self) -> None:
        """Save changes"""
        if self._script_editor.save():
            self._save_btn.setEnabled(False)
            self.setWindowTitle(f"Edit: {self.converter_info.name}")
            QMessageBox.information(self, "Saved", "Changes saved successfully.")
    
    def _on_save_new_version(self) -> None:
        """Save as new version"""
        current_version = self.converter_info.version
        
        # Parse version
        try:
            parts = current_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            major, minor, patch = 1, 0, 0
        
        # Suggest next version
        suggested = f"{major}.{minor}.{patch + 1}"
        
        new_version, ok = QInputDialog.getText(
            self, "New Version",
            f"Current version: {current_version}\nEnter new version:",
            text=suggested
        )
        
        if ok and new_version:
            # Update version in source
            source = self._script_editor.get_source()
            
            # Try to update version property
            updated = re.sub(
                r'(version\s*[=:]\s*["\'])([^"\']+)(["\'])',
                f'\\g<1>{new_version}\\g<3>',
                source
            )
            
            if updated == source:
                # Version not found, add it
                QMessageBox.warning(
                    self, "Version Update",
                    "Could not find version property in source. "
                    "Please update the version manually."
                )
                return
            
            # Save with new version
            self._script_editor.load_source(updated, str(self.converter_info.file_path))
            if self._script_editor.save():
                self.converter_info.version = new_version
                self.setWindowTitle(f"Edit: {self.converter_info.name} v{new_version}")
                QMessageBox.information(
                    self, "Version Updated",
                    f"Saved as version {new_version}"
                )
    
    def _on_customize(self) -> None:
        """Create customized copy of system converter"""
        if not self.user_folder:
            QMessageBox.warning(
                self, "No Folder",
                "Please configure a user converters folder first."
            )
            return
        
        # Suggest name
        original_name = self.converter_info.file_path.stem
        suggested_name = f"{original_name}_custom"
        
        new_name, ok = QInputDialog.getText(
            self, "Customize Converter",
            f"Create customized copy as:\n(Will be saved in {self.user_folder})",
            text=suggested_name
        )
        
        if ok and new_name:
            # Create the customized file
            new_path = self.user_folder / f"{new_name}.py"
            
            if new_path.exists():
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"File {new_name}.py already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            try:
                # Read original
                source = self.converter_info.file_path.read_text(encoding='utf-8')
                
                # Add customization header
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                header = f'''"""
{self.converter_info.name} (Customized)

# Based on: {self.converter_info.file_path.name}
# Customized: {timestamp}
# Original Version: {self.converter_info.version}

"""
'''
                # Update class name if needed
                old_class = self.converter_info.class_name
                new_class = "".join(word.capitalize() for word in new_name.split("_"))
                if not new_class.endswith("Converter"):
                    new_class += "Converter"
                
                # Replace class name
                source = re.sub(
                    f'class {old_class}',
                    f'class {new_class}',
                    source
                )
                
                # Update version to 1.0.0 for the custom version
                source = re.sub(
                    r'(version\s*[=:]\s*["\'])([^"\']+)(["\'])',
                    '\\g<1>1.0.0\\g<3>',
                    source
                )
                
                # Remove original docstring and add new header
                source = re.sub(r'^"""[\s\S]*?"""', '', source, count=1)
                source = header + source.lstrip()
                
                # Write file
                self.user_folder.mkdir(parents=True, exist_ok=True)
                new_path.write_text(source, encoding='utf-8')
                
                QMessageBox.information(
                    self, "Customized",
                    f"Created customized converter:\n{new_path}\n\n"
                    f"Class name: {new_class}\n"
                    "You can now edit this converter."
                )
                
                self.accept()
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to create customized converter:\n{e}"
                )
    
    def _on_close(self) -> None:
        """Close dialog"""
        if not self.is_system and self._script_editor.is_modified():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._on_save()
                self.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                self.reject()
        else:
            self.reject()


class ConvertersPageV2(BasePage):
    """
    Converters management page with unified list.
    
    Features:
    - Single list showing all converters (system + user)
    - System converters are read-only but can be customized
    - User converters can be edited directly
    - Version tracking
    - Auto-generated folder structure
    """
    
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
        # User converters folder
        folder_group = QGroupBox("User Converters Folder")
        folder_layout = QHBoxLayout(folder_group)
        
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText("Path for custom/user converters")
        self._folder_edit.textChanged.connect(self._emit_changed)
        folder_layout.addWidget(self._folder_edit, 1)
        
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._on_browse_folder)
        folder_layout.addWidget(self._browse_btn)
        
        self._layout.addWidget(folder_group)
        
        help_label = QLabel(
            "System converters are installed with the package and shown as read-only.\n"
            "You can customize them to create editable copies in your user folder."
        )
        help_label.setStyleSheet("color: #808080; font-size: 11px;")
        self._layout.addWidget(help_label)
        
        # Unified converter list
        list_group = QGroupBox("Converters")
        list_layout = QVBoxLayout(list_group)
        
        self._converter_table = QTableWidget()
        self._converter_table.setColumnCount(7)
        self._converter_table.setHorizontalHeaderLabels([
            "", "Name", "Source", "Version", "Watch Folder", "Status", "Actions"
        ])
        
        header = self._converter_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Enabled
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)       # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Source
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Version
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Watch Folder
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)             # Actions
        
        self._converter_table.setColumnWidth(1, 200)
        self._converter_table.setColumnWidth(6, 120)
        
        self._converter_table.verticalHeader().setVisible(False)
        self._converter_table.setAlternatingRowColors(True)
        self._converter_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._converter_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._converter_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._converter_table.doubleClicked.connect(self._on_row_double_clicked)
        
        list_layout.addWidget(self._converter_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self._new_btn = QPushButton("New Converter...")
        self._new_btn.clicked.connect(self._on_new_converter)
        btn_layout.addWidget(self._new_btn)
        
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_list)
        btn_layout.addWidget(self._refresh_btn)
        
        btn_layout.addStretch()
        
        list_layout.addLayout(btn_layout)
        
        self._layout.addWidget(list_group, 1)
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.converters_folder = self._folder_edit.text()
    
    def load_config(self) -> None:
        """Load configuration"""
        self._folder_edit.setText(self.config.converters_folder)
        self._refresh_list()
    
    def _on_browse_folder(self) -> None:
        """Browse for user converters folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select User Converters Folder",
            self._folder_edit.text() or str(Path.home())
        )
        if folder:
            self._folder_edit.setText(folder)
            self._emit_changed()
            self._refresh_list()
    
    def _refresh_list(self) -> None:
        """Refresh the unified converter list"""
        self._converter_table.setRowCount(0)
        
        # Get all converters
        system_converters = get_system_converters()
        user_folder = Path(self._folder_edit.text()) if self._folder_edit.text() else None
        user_converters = get_user_converters(user_folder) if user_folder else []
        
        # Build map of configured converters
        configured_modules = {cfg.module_path: cfg for cfg in self.config.converters}
        
        # Combine lists: system first, then user
        all_converters = system_converters + user_converters
        
        for row, conv in enumerate(all_converters):
            self._converter_table.insertRow(row)
            
            # Check if this converter has a configuration
            config = configured_modules.get(conv.module_path)
            conv.is_configured = config is not None
            conv.config = config
            
            # Enabled checkbox (only for configured converters)
            enabled_item = QTableWidgetItem()
            if config:
                enabled_item.setCheckState(
                    Qt.CheckState.Checked if config.enabled else Qt.CheckState.Unchecked
                )
            else:
                enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self._converter_table.setItem(row, 0, enabled_item)
            
            # Name
            name_item = QTableWidgetItem(conv.name)
            if conv.source == ConverterSource.SYSTEM:
                name_item.setForeground(QColor("#569cd6"))
            elif conv.source == ConverterSource.CUSTOMIZED:
                name_item.setForeground(QColor("#dcdcaa"))
            else:
                name_item.setForeground(QColor("#4ec9b0"))
            self._converter_table.setItem(row, 1, name_item)
            
            # Source
            source_icons = {
                ConverterSource.SYSTEM: "📦 System",
                ConverterSource.USER: "👤 User",
                ConverterSource.CUSTOMIZED: "🔧 Custom",
            }
            source_item = QTableWidgetItem(source_icons.get(conv.source, "?"))
            self._converter_table.setItem(row, 2, source_item)
            
            # Version
            version_item = QTableWidgetItem(conv.version)
            version_item.setForeground(QColor("#808080"))
            self._converter_table.setItem(row, 3, version_item)
            
            # Watch folder (from config)
            watch_item = QTableWidgetItem(config.watch_folder if config else "Not configured")
            if not config:
                watch_item.setForeground(QColor("#808080"))
            self._converter_table.setItem(row, 4, watch_item)
            
            # Status
            if config:
                status = "✓ Active" if config.enabled else "⏸ Disabled"
                status_color = "#4ec9b0" if config.enabled else "#808080"
            else:
                status = "—"
                status_color = "#808080"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(status_color))
            self._converter_table.setItem(row, 5, status_item)
            
            # Actions button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            
            # Main action button with menu
            action_btn = QToolButton()
            action_btn.setText("⚙")
            action_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            
            menu = QMenu(action_btn)
            
            # Add configuration actions
            if config:
                configure_action = menu.addAction("Configure...")
                configure_action.triggered.connect(
                    lambda checked, c=conv: self._on_configure(c)
                )
                
                menu.addSeparator()
                
                remove_action = menu.addAction("Remove Configuration")
                remove_action.triggered.connect(
                    lambda checked, c=conv: self._on_remove_config(c)
                )
            else:
                add_action = menu.addAction("Add Configuration...")
                add_action.triggered.connect(
                    lambda checked, c=conv: self._on_add_config(c)
                )
            
            menu.addSeparator()
            
            # View/Edit code
            if conv.source == ConverterSource.SYSTEM:
                view_action = menu.addAction("View Code...")
                view_action.triggered.connect(
                    lambda checked, c=conv: self._on_view_code(c)
                )
                
                customize_action = menu.addAction("Customize...")
                customize_action.triggered.connect(
                    lambda checked, c=conv: self._on_customize(c)
                )
            else:
                edit_action = menu.addAction("Edit Code...")
                edit_action.triggered.connect(
                    lambda checked, c=conv: self._on_edit_code(c)
                )
            
            action_btn.setMenu(menu)
            actions_layout.addWidget(action_btn)
            
            self._converter_table.setCellWidget(row, 6, actions_widget)
            
            # Store converter info for later
            name_item.setData(Qt.ItemDataRole.UserRole, conv)
    
    def _on_row_double_clicked(self, index) -> None:
        """Handle double-click on row"""
        row = index.row()
        name_item = self._converter_table.item(row, 1)
        if name_item:
            conv = name_item.data(Qt.ItemDataRole.UserRole)
            if conv:
                if conv.config:
                    self._on_configure(conv)
                else:
                    self._on_add_config(conv)
    
    def _on_add_config(self, conv: ConverterInfo) -> None:
        """Add configuration for a converter"""
        dialog = ConverterSettingsDialogV2(
            converter_info=conv,
            config=None,
            user_folder=self._folder_edit.text(),
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            
            # Check for duplicate names
            for cfg in self.config.converters:
                if cfg.name == new_config.name:
                    QMessageBox.warning(
                        self, "Duplicate Name",
                        f"A configuration named '{new_config.name}' already exists."
                    )
                    return
            
            self.config.converters.append(new_config)
            self._refresh_list()
            self._emit_changed()
    
    def _on_configure(self, conv: ConverterInfo) -> None:
        """Configure an existing converter configuration"""
        if not conv.config:
            return
        
        # Find index in config list
        config_idx = None
        for i, cfg in enumerate(self.config.converters):
            if cfg.module_path == conv.module_path:
                config_idx = i
                break
        
        if config_idx is None:
            return
        
        dialog = ConverterSettingsDialogV2(
            converter_info=conv,
            config=conv.config,
            user_folder=self._folder_edit.text(),
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config.converters[config_idx] = dialog.get_config()
            self._refresh_list()
            self._emit_changed()
    
    def _on_remove_config(self, conv: ConverterInfo) -> None:
        """Remove converter configuration"""
        if not conv.config:
            return
        
        reply = QMessageBox.question(
            self, "Remove Configuration",
            f"Remove configuration for '{conv.name}'?\n\n"
            "This only removes the configuration, not the converter file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.converters = [
                cfg for cfg in self.config.converters 
                if cfg.module_path != conv.module_path
            ]
            self._refresh_list()
            self._emit_changed()
    
    def _on_view_code(self, conv: ConverterInfo) -> None:
        """View system converter code (read-only)"""
        user_folder = Path(self._folder_edit.text()) if self._folder_edit.text() else None
        dialog = ConverterEditorDialogV2(conv, user_folder, self)
        dialog.exec()
        self._refresh_list()  # Refresh in case user customized
    
    def _on_edit_code(self, conv: ConverterInfo) -> None:
        """Edit user converter code"""
        user_folder = Path(self._folder_edit.text()) if self._folder_edit.text() else None
        dialog = ConverterEditorDialogV2(conv, user_folder, self)
        dialog.exec()
        self._refresh_list()
    
    def _on_customize(self, conv: ConverterInfo) -> None:
        """Create customized copy of system converter"""
        user_folder = Path(self._folder_edit.text()) if self._folder_edit.text() else None
        if not user_folder:
            QMessageBox.warning(
                self, "No Folder",
                "Please configure a user converters folder first."
            )
            return
        
        dialog = ConverterEditorDialogV2(conv, user_folder, self)
        dialog.exec()
        self._refresh_list()
    
    def _on_new_converter(self) -> None:
        """Create a new converter from template"""
        folder = self._folder_edit.text()
        if not folder:
            QMessageBox.warning(
                self, "No Folder",
                "Please configure a user converters folder first."
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
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_list()
            
            # Optionally open the new converter in editor
            if dialog.created_path:
                new_conv = ConverterInfo(
                    name=dialog.created_path.stem,
                    class_name="",
                    module_path=f"{dialog.created_path.stem}",
                    file_path=dialog.created_path,
                    source=ConverterSource.USER,
                    version="1.0.0",
                )
                self._on_edit_code(new_conv)
