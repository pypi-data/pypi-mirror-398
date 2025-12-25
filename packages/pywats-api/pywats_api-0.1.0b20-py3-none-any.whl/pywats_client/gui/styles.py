"""
Dark theme stylesheet for WATS Client GUI

Mimics the WATS Client dark theme with orange accents.
"""

DARK_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}

/* Sidebar/Navigation */
QListWidget#navList {
    background-color: #252526;
    border: none;
    outline: none;
    padding: 10px 0;
}

QListWidget#navList::item {
    padding: 12px 20px;
    border: none;
    color: #cccccc;
}

QListWidget#navList::item:hover {
    background-color: #2a2d2e;
    color: #ffffff;
}

QListWidget#navList::item:selected {
    background-color: #2a2d2e;
    color: #ffffff;
    border-left: 3px solid #f0a30a;
}

/* Content Area */
QFrame#contentFrame {
    background-color: #1e1e1e;
    border: none;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #ffffff;
}

/* Labels */
QLabel {
    color: #cccccc;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
    padding: 10px 0;
}

QLabel#statusLabel {
    font-weight: bold;
}

QLabel#statusOnline {
    color: #4ec9b0;
}

QLabel#statusOffline {
    color: #f14c4c;
}

QLabel#statusConnecting {
    color: #dcdcaa;
}

/* Line Edits */
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 20px;
    color: #ffffff;
    selection-background-color: #f0a30a;
}

QLineEdit:focus {
    border: 1px solid #f0a30a;
}

QLineEdit:disabled {
    background-color: #2d2d2d;
    color: #808080;
}

/* Buttons */
QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
    color: #ffffff;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #505050;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #404040;
}

QPushButton:disabled {
    background-color: #2d2d2d;
    color: #606060;
    border-color: #404040;
}

QPushButton#primaryButton {
    background-color: #f0a30a;
    border: none;
    color: #1e1e1e;
    font-weight: bold;
}

QPushButton#primaryButton:hover {
    background-color: #ffb824;
}

QPushButton#primaryButton:pressed {
    background-color: #d99200;
}

QPushButton#dangerButton {
    background-color: #c42b1c;
    border: none;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #e83929;
}

/* Combo Boxes */
QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 8px 12px;
    color: #ffffff;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #666666;
}

QComboBox:focus {
    border-color: #f0a30a;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #cccccc;
}

QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    selection-background-color: #f0a30a;
    selection-color: #1e1e1e;
}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 8px 12px;
    color: #ffffff;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #f0a30a;
}

/* Check Boxes */
QCheckBox {
    spacing: 8px;
    color: #cccccc;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #3c3c3c;
}

QCheckBox::indicator:hover {
    border-color: #f0a30a;
}

QCheckBox::indicator:checked {
    background-color: #f0a30a;
    border-color: #f0a30a;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 10px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    border-bottom: 2px solid #f0a30a;
}

QTabBar::tab:hover:!selected {
    background-color: #353535;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #252526;
    alternate-background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    gridline-color: #3c3c3c;
    selection-background-color: #f0a30a;
    selection-color: #1e1e1e;
}

QTableWidget::item, QTableView::item {
    padding: 8px;
}

QHeaderView::section {
    background-color: #333333;
    border: none;
    border-right: 1px solid #3c3c3c;
    border-bottom: 1px solid #3c3c3c;
    padding: 8px;
    font-weight: bold;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #5a5a5a;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6a6a6a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #5a5a5a;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6a6a6a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Progress Bar */
QProgressBar {
    background-color: #3c3c3c;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #f0a30a;
    border-radius: 4px;
}

/* Tool Tips */
QToolTip {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    color: #ffffff;
    padding: 5px;
}

/* Status Bar */
QStatusBar {
    background-color: #252526;
    border-top: 1px solid #3c3c3c;
    color: #cccccc;
}

QStatusBar::item {
    border: none;
}

/* Separator */
QFrame#separator {
    background-color: #3c3c3c;
    max-height: 1px;
}

/* Footer */
QLabel#footerLabel {
    color: #569cd6;
    font-size: 11px;
}
"""
