"""
RootCause Tickets Page

Issue tracking and resolution for quality management.
Create, view, and manage tickets linked to test failures.

Based on the WATS RootCause/Ticketing API:
- GET /api/RootCause/Tickets - List tickets
- GET /api/RootCause/Ticket/{id} - Get ticket details
- POST /api/RootCause/Ticket - Create/update ticket
- GET /api/RootCause/Teams - Get teams for assignment
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QDialogButtonBox, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class TicketDialog(QDialog):
    """Dialog for creating/editing tickets"""
    
    def __init__(
        self, 
        teams: List[str] = None,
        ticket: Dict[str, Any] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.teams = teams or []
        self.ticket = ticket
        self._setup_ui()
        if ticket:
            self._populate_data(ticket)
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("New Ticket" if not self.ticket else "Edit Ticket")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(10)
        
        # Subject
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Brief description of the issue")
        form.addRow("Subject:", self.subject_edit)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentIndex(1)  # Default to Medium
        form.addRow("Priority:", self.priority_combo)
        
        # Status (for editing)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Open", "In Progress", "Resolved", "Closed", "Cancelled"])
        if not self.ticket:
            self.status_combo.setEnabled(False)
            self.status_combo.setCurrentIndex(0)
        form.addRow("Status:", self.status_combo)
        
        # Team
        self.team_combo = QComboBox()
        self.team_combo.addItem("Unassigned", None)
        for team in self.teams:
            self.team_combo.addItem(team, team)
        form.addRow("Team:", self.team_combo)
        
        # Assignee
        self.assignee_edit = QLineEdit()
        self.assignee_edit.setPlaceholderText("Username to assign (optional)")
        form.addRow("Assignee:", self.assignee_edit)
        
        layout.addLayout(form)
        
        # Description/Comment
        layout.addWidget(QLabel("Description / Comment:"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Detailed description of the issue or additional comments...")
        self.comment_edit.setMinimumHeight(120)
        layout.addWidget(self.comment_edit, 1)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _populate_data(self, ticket: Dict[str, Any]) -> None:
        """Populate form with existing ticket data"""
        self.subject_edit.setText(ticket.get("subject", ""))
        
        # Priority
        priority = ticket.get("priority", "Medium")
        index = self.priority_combo.findText(priority)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)
        
        # Status
        status = ticket.get("status", "Open")
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        self.status_combo.setEnabled(True)
        
        # Team
        team = ticket.get("team")
        if team:
            index = self.team_combo.findText(team)
            if index >= 0:
                self.team_combo.setCurrentIndex(index)
        
        # Assignee
        self.assignee_edit.setText(ticket.get("assignee", ""))
    
    def _validate_and_accept(self) -> None:
        """Validate input before accepting"""
        if not self.subject_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Subject is required")
            return
        
        self.accept()
    
    def get_ticket_data(self) -> Dict[str, Any]:
        """Get ticket data from form"""
        data = {
            "subject": self.subject_edit.text().strip(),
            "priority": self.priority_combo.currentText(),
            "status": self.status_combo.currentText(),
            "team": self.team_combo.currentData(),
            "assignee": self.assignee_edit.text().strip() or None,
            "comment": self.comment_edit.toPlainText().strip() or None,
        }
        return data


class RootCausePage(BasePage):
    """RootCause Tickets page - issue tracking and resolution"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ):
        self._main_window = main_window
        self._tickets: List[Dict[str, Any]] = []
        self._teams: List[str] = []
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "RootCause Tickets"
    
    def _setup_ui(self) -> None:
        """Setup page UI for RootCause Tickets"""
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self._refresh_btn = QPushButton("⟳ Refresh")
        self._refresh_btn.setToolTip("Refresh tickets from server")
        self._refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self._refresh_btn)
        
        self._add_btn = QPushButton("+ New Ticket")
        self._add_btn.clicked.connect(self._on_add_ticket)
        toolbar_layout.addWidget(self._add_btn)
        
        toolbar_layout.addStretch()
        
        # View filter
        toolbar_layout.addWidget(QLabel("View:"))
        self._view_combo = QComboBox()
        self._view_combo.addItems(["Assigned to Me", "Following", "All"])
        self._view_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._view_combo)
        
        # Status filter
        toolbar_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItems(["Open", "In Progress", "Active (Open + In Progress)", "Resolved", "All"])
        self._status_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._status_filter)
        
        # Search
        toolbar_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search subject, tags...")
        self._search_edit.setMaximumWidth(200)
        self._search_edit.textChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self._search_edit)
        
        self._layout.addLayout(toolbar_layout)
        
        # Main content - splitter with table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tickets table
        table_group = QGroupBox("Tickets")
        table_layout = QVBoxLayout(table_group)
        
        self._tickets_table = QTableWidget()
        self._tickets_table.setColumnCount(6)
        self._tickets_table.setHorizontalHeaderLabels([
            "ID", "Subject", "Priority", "Status", "Assignee", "Updated"
        ])
        self._tickets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tickets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tickets_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tickets_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tickets_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tickets_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tickets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tickets_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._tickets_table.setAlternatingRowColors(True)
        self._tickets_table.itemSelectionChanged.connect(self._on_selection_changed)
        self._tickets_table.doubleClicked.connect(self._on_edit_ticket)
        
        # Apply dark theme styling
        self._tickets_table.setStyleSheet("""
            QTableWidget {
                font-size: 11pt;
                background-color: #1e1e1e;
                alternate-background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #3c3c3c;
                font-weight: bold;
            }
        """)
        table_layout.addWidget(self._tickets_table)
        
        splitter.addWidget(table_group)
        
        # Details panel with tabs
        details_group = QGroupBox("Ticket Details")
        details_layout = QVBoxLayout(details_group)
        
        self._details_tabs = QTabWidget()
        
        # Info tab
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        self._details_label = QLabel("Select a ticket to view details")
        self._details_label.setStyleSheet("color: #808080; font-style: italic;")
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._details_label.setWordWrap(True)
        info_layout.addWidget(self._details_label)
        self._details_tabs.addTab(info_widget, "Info")
        
        # Comments tab
        comments_widget = QWidget()
        comments_layout = QVBoxLayout(comments_widget)
        self._comments_list = QListWidget()
        comments_layout.addWidget(self._comments_list)
        
        # Add comment input
        comment_input_layout = QHBoxLayout()
        self._comment_input = QLineEdit()
        self._comment_input.setPlaceholderText("Add a comment...")
        comment_input_layout.addWidget(self._comment_input)
        
        self._add_comment_btn = QPushButton("Add")
        self._add_comment_btn.setEnabled(False)
        self._add_comment_btn.clicked.connect(self._on_add_comment)
        comment_input_layout.addWidget(self._add_comment_btn)
        
        comments_layout.addLayout(comment_input_layout)
        self._details_tabs.addTab(comments_widget, "Comments")
        
        details_layout.addWidget(self._details_tabs)
        
        # Action buttons for selected ticket
        action_layout = QHBoxLayout()
        
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit_ticket)
        action_layout.addWidget(self._edit_btn)
        
        self._resolve_btn = QPushButton("Resolve")
        self._resolve_btn.setEnabled(False)
        self._resolve_btn.clicked.connect(self._on_resolve_ticket)
        action_layout.addWidget(self._resolve_btn)
        
        self._close_btn = QPushButton("Close")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self._on_close_ticket)
        action_layout.addWidget(self._close_btn)
        
        action_layout.addStretch()
        details_layout.addLayout(action_layout)
        
        splitter.addWidget(details_group)
        splitter.setSizes([350, 250])
        
        self._layout.addWidget(splitter, 1)
        
        # Status label
        self._status_label = QLabel("Connect to WATS server to view tickets")
        self._status_label.setStyleSheet("color: #808080; font-style: italic;")
        self._layout.addWidget(self._status_label)
        
        # Auto-load if connected
        if self._main_window and self._main_window.app.wats_client:
            self._load_tickets()
    
    def _on_selection_changed(self) -> None:
        """Handle ticket selection change"""
        selected = len(self._tickets_table.selectedItems()) > 0
        self._edit_btn.setEnabled(selected)
        self._add_comment_btn.setEnabled(selected)
        
        if selected:
            row = self._tickets_table.currentRow()
            if 0 <= row < len(self._tickets):
                ticket = self._tickets[row]
                self._show_ticket_details(ticket)
                
                # Enable/disable resolve/close based on status
                status = ticket.get('status', '')
                self._resolve_btn.setEnabled(status in ['Open', 'In Progress'])
                self._close_btn.setEnabled(status not in ['Closed', 'Cancelled'])
        else:
            self._details_label.setText("Select a ticket to view details")
            self._resolve_btn.setEnabled(False)
            self._close_btn.setEnabled(False)
    
    def _show_ticket_details(self, ticket: Dict[str, Any]) -> None:
        """Show ticket details in details panel"""
        details = f"""
<b>Ticket ID:</b> {str(ticket.get('ticketId', 'N/A'))[:8]}...<br>
<b>Subject:</b> {ticket.get('subject', 'N/A')}<br>
<b>Priority:</b> {ticket.get('priority', 'N/A')}<br>
<b>Status:</b> {ticket.get('status', 'N/A')}<br>
<b>Team:</b> {ticket.get('team', 'Unassigned')}<br>
<b>Assignee:</b> {ticket.get('assignee', 'Unassigned')}<br>
<b>Created:</b> {ticket.get('created', 'N/A')}<br>
<b>Updated:</b> {ticket.get('updated', 'N/A')}<br>
"""
        if ticket.get('reportUuid'):
            details += f"<b>Linked Report:</b> {str(ticket.get('reportUuid'))[:8]}...<br>"
        
        if ticket.get('tags'):
            details += f"<b>Tags:</b> {', '.join(ticket.get('tags', []))}<br>"
        
        self._details_label.setText(details)
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Populate comments
        self._comments_list.clear()
        for update in ticket.get('updates', []):
            comment_text = f"[{update.get('created', '')}] {update.get('userName', 'Unknown')}: {update.get('content', '')}"
            item = QListWidgetItem(comment_text)
            self._comments_list.addItem(item)
    
    def _on_filter_changed(self) -> None:
        """Handle filter changes - reload tickets"""
        if self._main_window and self._main_window.app.wats_client:
            self._load_tickets()
    
    def _on_refresh(self) -> None:
        """Refresh tickets from server"""
        if self._main_window and self._main_window.app.wats_client:
            self._load_tickets()
        else:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
    
    def _load_tickets(self) -> None:
        """Load tickets from WATS server"""
        try:
            self._status_label.setText("Loading tickets...")
            
            if self._main_window and self._main_window.app.wats_client:
                client = self._main_window.app.wats_client
                
                # Get view and status filters
                view_text = self._view_combo.currentText()
                status_text = self._status_filter.currentText()
                search = self._search_edit.text().strip() or None
                
                # Map view text to TicketView enum values
                view_map = {
                    "Assigned to Me": "ASSIGNED",
                    "Following": "FOLLOWING",
                    "All": "ALL"
                }
                view = view_map.get(view_text, "ASSIGNED")
                
                # Load tickets based on status filter
                if status_text == "Open":
                    tickets = client.rootcause.get_open_tickets()
                elif status_text == "Active (Open + In Progress)":
                    tickets = client.rootcause.get_active_tickets()
                else:
                    tickets = client.rootcause.get_tickets(search_string=search)
                
                self._tickets = [self._ticket_to_dict(t) for t in tickets] if tickets else []
                
                self._populate_table()
                self._status_label.setText(f"Loaded {len(self._tickets)} tickets")
            else:
                self._status_label.setText("Not connected to WATS server")
        except Exception as e:
            self._status_label.setText(f"Error: {str(e)[:50]}")
            QMessageBox.warning(self, "Error", f"Failed to load tickets: {e}")
    
    def _ticket_to_dict(self, ticket: Any) -> Dict[str, Any]:
        """Convert Ticket model to dictionary"""
        if hasattr(ticket, '__dict__'):
            return {
                'ticketId': getattr(ticket, 'ticket_id', None),
                'subject': getattr(ticket, 'subject', ''),
                'priority': getattr(ticket, 'priority', 'Medium'),
                'status': getattr(ticket, 'status', 'Open'),
                'team': getattr(ticket, 'team', None),
                'assignee': getattr(ticket, 'assignee', None),
                'created': str(getattr(ticket, 'created', ''))[:19],
                'updated': str(getattr(ticket, 'updated', ''))[:19],
                'reportUuid': getattr(ticket, 'report_uuid', None),
                'tags': getattr(ticket, 'tags', []),
                'updates': getattr(ticket, 'updates', []),
            }
        return dict(ticket) if isinstance(ticket, dict) else {}
    
    def _populate_table(self) -> None:
        """Populate the tickets table"""
        self._tickets_table.setRowCount(0)
        
        for ticket in self._tickets:
            row = self._tickets_table.rowCount()
            self._tickets_table.insertRow(row)
            
            # ID (shortened)
            ticket_id = str(ticket.get('ticketId', ''))
            short_id = ticket_id[:8] + "..." if len(ticket_id) > 8 else ticket_id
            self._tickets_table.setItem(row, 0, QTableWidgetItem(short_id))
            
            self._tickets_table.setItem(row, 1, QTableWidgetItem(ticket.get('subject', '')))
            
            # Priority with color coding
            priority = str(ticket.get('priority', 'Medium'))
            priority_item = QTableWidgetItem(priority)
            if priority == "Critical":
                priority_item.setForeground(QColor("#f44336"))  # Red
            elif priority == "High":
                priority_item.setForeground(QColor("#FF9800"))  # Orange
            elif priority == "Medium":
                priority_item.setForeground(QColor("#2196F3"))  # Blue
            else:
                priority_item.setForeground(QColor("#4CAF50"))  # Green
            self._tickets_table.setItem(row, 2, priority_item)
            
            # Status with color coding
            status = str(ticket.get('status', 'Open'))
            status_item = QTableWidgetItem(status)
            if status == "Open":
                status_item.setForeground(QColor("#2196F3"))  # Blue
            elif status == "In Progress":
                status_item.setForeground(QColor("#FF9800"))  # Orange
            elif status == "Resolved":
                status_item.setForeground(QColor("#4CAF50"))  # Green
            elif status in ["Closed", "Cancelled"]:
                status_item.setForeground(QColor("#808080"))  # Gray
            self._tickets_table.setItem(row, 3, status_item)
            
            self._tickets_table.setItem(row, 4, QTableWidgetItem(ticket.get('assignee', '')))
            self._tickets_table.setItem(row, 5, QTableWidgetItem(ticket.get('updated', '')))
    
    def _on_add_ticket(self) -> None:
        """Show dialog to create new ticket"""
        if not self._main_window or not self._main_window.app.wats_client:
            QMessageBox.warning(self, "Not Connected", "Please connect to WATS server first.")
            return
        
        dialog = TicketDialog(self._teams, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_ticket_data()
                client = self._main_window.app.wats_client
                
                # Map priority string to enum value
                priority_map = {
                    "Low": 1,
                    "Medium": 2,
                    "High": 3,
                    "Critical": 4
                }
                
                result = client.rootcause.create_ticket(
                    subject=data['subject'],
                    priority=priority_map.get(data['priority'], 2),
                    assignee=data.get('assignee'),
                    team=data.get('team'),
                    initial_comment=data.get('comment'),
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Ticket created successfully")
                    self._load_tickets()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create ticket")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create ticket: {e}")
    
    def _on_edit_ticket(self) -> None:
        """Edit selected ticket"""
        row = self._tickets_table.currentRow()
        if row < 0 or row >= len(self._tickets):
            return
        
        ticket = self._tickets[row]
        dialog = TicketDialog(self._teams, ticket=ticket, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_ticket_data()
                client = self._main_window.app.wats_client
                
                # Update via add_comment if there's a comment, otherwise update directly
                if data.get('comment'):
                    result = client.rootcause.add_comment(
                        ticket_id=ticket['ticketId'],
                        comment=data['comment']
                    )
                
                # TODO: Add proper update_ticket call when available
                
                QMessageBox.information(self, "Success", "Ticket updated successfully")
                self._load_tickets()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update ticket: {e}")
    
    def _on_add_comment(self) -> None:
        """Add comment to selected ticket"""
        comment = self._comment_input.text().strip()
        if not comment:
            return
        
        row = self._tickets_table.currentRow()
        if row < 0 or row >= len(self._tickets):
            return
        
        ticket = self._tickets[row]
        
        try:
            client = self._main_window.app.wats_client
            result = client.rootcause.add_comment(
                ticket_id=ticket['ticketId'],
                comment=comment
            )
            
            if result:
                self._comment_input.clear()
                self._load_tickets()
                # Re-select the same ticket
                self._tickets_table.selectRow(row)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add comment: {e}")
    
    def _on_resolve_ticket(self) -> None:
        """Mark ticket as resolved"""
        row = self._tickets_table.currentRow()
        if row < 0 or row >= len(self._tickets):
            return
        
        ticket = self._tickets[row]
        
        try:
            client = self._main_window.app.wats_client
            # Use change_status method
            result = client.rootcause.change_status(
                ticket_id=ticket['ticketId'],
                status=4  # Resolved
            )
            
            if result:
                QMessageBox.information(self, "Success", "Ticket marked as resolved")
                self._load_tickets()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to resolve ticket: {e}")
    
    def _on_close_ticket(self) -> None:
        """Close the ticket"""
        row = self._tickets_table.currentRow()
        if row < 0 or row >= len(self._tickets):
            return
        
        ticket = self._tickets[row]
        
        reply = QMessageBox.question(
            self, "Confirm Close",
            "Are you sure you want to close this ticket?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                client = self._main_window.app.wats_client
                result = client.rootcause.change_status(
                    ticket_id=ticket['ticketId'],
                    status=8  # Closed
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Ticket closed")
                    self._load_tickets()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to close ticket: {e}")
    
    def save_config(self) -> None:
        """Save configuration"""
        pass
    
    def load_config(self) -> None:
        """Load configuration"""
        pass
