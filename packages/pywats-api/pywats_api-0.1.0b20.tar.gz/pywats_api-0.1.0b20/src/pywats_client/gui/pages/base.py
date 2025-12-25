"""
Base Page Widget

Base class for all configuration pages.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal

from ...core.config import ClientConfig


class BasePage(QWidget):
    """
    Base class for configuration pages.
    
    Provides common functionality for all pages:
    - Title display
    - Config change signal
    - Save/load config methods
    """
    
    # Emitted when configuration is changed
    config_changed = Signal()
    
    def __init__(self, config: ClientConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self._setup_base_ui()
    
    def _setup_base_ui(self) -> None:
        """Setup base UI layout"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(15)
        
        # Title
        self._title_label = QLabel(self.page_title)
        self._title_label.setObjectName("titleLabel")
        self._layout.addWidget(self._title_label)
        
        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        self._layout.addWidget(separator)
    
    @property
    def page_title(self) -> str:
        """Override in subclass to set page title"""
        return "Page"
    
    def save_config(self) -> None:
        """Override in subclass to save configuration"""
        pass
    
    def load_config(self) -> None:
        """Override in subclass to load configuration"""
        pass
    
    def _emit_changed(self) -> None:
        """Emit config changed signal"""
        self.config_changed.emit()
