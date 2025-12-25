"""
About Page

Displays version and about information.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtCore import QUrl

from .base import BasePage
from ...core.config import ClientConfig
from ... import __version__


class AboutPage(BasePage):
    """About page showing version and credits"""
    
    def __init__(self, config: ClientConfig, parent: Optional[QWidget] = None):
        super().__init__(config, parent)
        self._setup_ui()
    
    @property
    def page_title(self) -> str:
        return "About"
    
    def _setup_ui(self) -> None:
        """Setup page UI"""
        # Center content
        self._layout.addStretch()
        
        # Logo/Title section
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Application icon (placeholder text for now)
        icon_label = QLabel("🔧")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(icon_label)
        
        # Application name
        name_label = QLabel("pyWATS Client")
        name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(name_label)
        
        # Version
        version_label = QLabel(f"Version {__version__}")
        version_label.setStyleSheet("font-size: 14px; color: #808080;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(version_label)
        
        self._layout.addLayout(title_layout)
        
        self._layout.addSpacing(30)
        
        # Description
        desc_label = QLabel(
            "A Python client for WATS (Web-Based Automated Test System).\n"
            "Provides offline report storage, converter management,\n"
            "and integration with the WATS API."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        self._layout.addWidget(desc_label)
        
        self._layout.addSpacing(30)
        
        # Links section
        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        docs_btn = QPushButton("Documentation")
        docs_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #569cd6; "
            "border: none; text-decoration: underline; } "
            "QPushButton:hover { color: #7fcfff; }"
        )
        docs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        docs_btn.clicked.connect(lambda: self._open_url("https://wats.com/docs"))
        links_layout.addWidget(docs_btn)
        
        links_layout.addSpacing(20)
        
        wats_btn = QPushButton("WATS Website")
        wats_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #569cd6; "
            "border: none; text-decoration: underline; } "
            "QPushButton:hover { color: #7fcfff; }"
        )
        wats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        wats_btn.clicked.connect(lambda: self._open_url("https://wats.com"))
        links_layout.addWidget(wats_btn)
        
        self._layout.addLayout(links_layout)
        
        self._layout.addSpacing(30)
        
        # System info
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_label = QLabel("System Information")
        info_label.setStyleSheet("font-weight: bold;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(info_label)
        
        # Python version
        import sys
        python_version = f"Python {sys.version.split()[0]}"
        
        # Qt version
        from PySide6 import __version__ as pyside_version
        qt_info = f"PySide6 {pyside_version}"
        
        sys_info = QLabel(f"{python_version}\n{qt_info}")
        sys_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sys_info.setStyleSheet("color: #808080; font-size: 11px;")
        info_layout.addWidget(sys_info)
        
        self._layout.addLayout(info_layout)
        
        self._layout.addStretch()
        
        # Copyright footer
        copyright_label = QLabel("© 2024 pyWATS Contributors")
        copyright_label.setStyleSheet("color: #606060; font-size: 10px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(copyright_label)
    
    def _open_url(self, url: str) -> None:
        """Open URL in default browser"""
        QDesktopServices.openUrl(QUrl(url))
    
    def save_config(self) -> None:
        """No config to save on about page"""
        pass
    
    def load_config(self) -> None:
        """No config to load on about page"""
        pass
