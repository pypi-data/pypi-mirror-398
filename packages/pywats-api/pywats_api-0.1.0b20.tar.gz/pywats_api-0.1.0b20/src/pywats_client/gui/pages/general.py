"""
General Settings Page
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt

from .base import BasePage
from ...core.config import ClientConfig


class GeneralPage(BasePage):
    """General settings page"""
    
    def __init__(self, config: ClientConfig, parent: Optional[QWidget] = None):
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "General"
    
    def _setup_ui(self) -> None:
        """Setup page UI"""
        # Instance settings group
        instance_group = QGroupBox("Instance Settings")
        instance_layout = QVBoxLayout(instance_group)
        
        # Instance name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Instance name:"))
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._emit_changed)
        name_layout.addWidget(self._name_edit)
        instance_layout.addLayout(name_layout)
        
        # Instance ID (read-only)
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Instance ID:"))
        self._id_label = QLabel()
        self._id_label.setStyleSheet("color: #808080;")
        id_layout.addWidget(self._id_label)
        id_layout.addStretch()
        instance_layout.addLayout(id_layout)
        
        self._layout.addWidget(instance_group)
        
        # Startup settings group
        startup_group = QGroupBox("Startup Settings")
        startup_layout = QVBoxLayout(startup_group)
        
        self._start_minimized_cb = QCheckBox("Start minimized")
        self._start_minimized_cb.stateChanged.connect(self._emit_changed)
        startup_layout.addWidget(self._start_minimized_cb)
        
        self._minimize_to_tray_cb = QCheckBox("Minimize to system tray")
        self._minimize_to_tray_cb.stateChanged.connect(self._emit_changed)
        startup_layout.addWidget(self._minimize_to_tray_cb)
        
        self._layout.addWidget(startup_group)
        
        # Logging settings group
        logging_group = QGroupBox("Logging")
        logging_layout = QVBoxLayout(logging_group)
        
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Log level:"))
        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._log_level_combo.currentTextChanged.connect(self._emit_changed)
        level_layout.addWidget(self._log_level_combo)
        level_layout.addStretch()
        logging_layout.addLayout(level_layout)
        
        self._layout.addWidget(logging_group)
        
        # Add stretch to push content to top
        self._layout.addStretch()
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.instance_name = self._name_edit.text()
        self.config.start_minimized = self._start_minimized_cb.isChecked()
        self.config.minimize_to_tray = self._minimize_to_tray_cb.isChecked()
        self.config.log_level = self._log_level_combo.currentText()
    
    def load_config(self) -> None:
        """Load configuration"""
        self._name_edit.setText(self.config.instance_name)
        self._id_label.setText(self.config.instance_id)
        self._start_minimized_cb.setChecked(self.config.start_minimized)
        self._minimize_to_tray_cb.setChecked(self.config.minimize_to_tray)
        
        index = self._log_level_combo.findText(self.config.log_level)
        if index >= 0:
            self._log_level_combo.setCurrentIndex(index)
