"""
Location Page

Manages location services settings for the WATS client.
Based on WATS Client location_tab.png screenshot - this is about
enabling/disabling location services (GPS/network location sharing),
NOT about station naming or physical location text.
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class LocationPage(BasePage):
    """Location services settings page"""
    
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
        return "Location"
    
    def _setup_ui(self) -> None:
        """Setup page UI matching WATS Client design"""
        # Location Services Group
        location_group = QGroupBox("Location Services")
        location_layout = QVBoxLayout(location_group)
        
        # Enable location services checkbox
        self._location_enabled_cb = QCheckBox("Allow this app to use location services")
        self._location_enabled_cb.setToolTip(
            "When enabled, the client can send location data with reports.\n"
            "This helps track where units are tested."
        )
        self._location_enabled_cb.stateChanged.connect(self._emit_changed)
        location_layout.addWidget(self._location_enabled_cb)
        
        # Info text
        info_label = QLabel(
            "Location services allow the WATS client to include geographical\n"
            "coordinates when submitting test reports. This can help with:\n\n"
            "  • Tracking where units are manufactured or tested\n"
            "  • Identifying location-specific yield issues\n"
            "  • Compliance and traceability requirements"
        )
        info_label.setStyleSheet("color: #808080; font-size: 11px; margin-top: 10px;")
        location_layout.addWidget(info_label)
        
        self._layout.addWidget(location_group)
        
        self._layout.addSpacing(15)
        
        # Privacy notice
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout(privacy_group)
        
        privacy_label = QLabel(
            "When location services are enabled:\n\n"
            "  • Location data is only sent with test reports\n"
            "  • No background location tracking occurs\n"
            "  • Location accuracy depends on your network/GPS settings\n"
            "  • You can disable this at any time"
        )
        privacy_label.setStyleSheet("color: #808080; font-size: 11px;")
        privacy_layout.addWidget(privacy_label)
        
        self._layout.addWidget(privacy_group)
        
        # Add stretch to push content to top
        self._layout.addStretch()
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.location_services_enabled = self._location_enabled_cb.isChecked()
    
    def load_config(self) -> None:
        """Load configuration"""
        self._location_enabled_cb.setChecked(
            getattr(self.config, 'location_services_enabled', False)
        )
