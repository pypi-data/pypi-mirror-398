"""
New Converter Dialog

Dialog for creating new converter files from templates.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QPushButton,
    QMessageBox, QGroupBox, QLabel, QDialogButtonBox
)
from PySide6.QtCore import Qt


# Converter templates
FILE_CONVERTER_TEMPLATE = '''"""
{name} Converter

{description}

Author: {author}
Version: {version}
"""

from pathlib import Path
from typing import Dict, List, Any

from pywats_client.converters import (
    FileConverter,
    ConverterSource,
    ConverterContext,
    ConverterResult,
    ValidationResult,
    PostProcessAction,
    ArgumentDefinition,
    ArgumentType,
)
from pywats.domains.report.report_models import UUTReport


class {class_name}(FileConverter):
    """
    {description}
    """
    
    # =========================================================================
    # Required Properties
    # =========================================================================
    
    @property
    def name(self) -> str:
        """Human-readable name of the converter"""
        return "{name}"
    
    # =========================================================================
    # Optional Properties
    # =========================================================================
    
    @property
    def version(self) -> str:
        """Version string for the converter"""
        return "{version}"
    
    @property
    def description(self) -> str:
        """Description of what this converter does"""
        return "{description}"
    
    @property
    def author(self) -> str:
        """Author/maintainer of this converter"""
        return "{author}"
    
    @property
    def file_patterns(self) -> List[str]:
        """File patterns this converter handles"""
        return {patterns}
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """Define configurable arguments"""
        return {{
            # Example argument:
            # "delimiter": ArgumentDefinition(
            #     arg_type=ArgumentType.STRING,
            #     default=",",
            #     description="Field delimiter character"
            # ),
        }}
    
    # =========================================================================
    # Optional Methods
    # =========================================================================
    
    def validate(
        self,
        source: ConverterSource,
        context: ConverterContext
    ) -> ValidationResult:
        """
        Validate if this converter can handle the source file.
        
        Returns a confidence score (0.0 to 1.0) indicating how well
        this converter matches the file.
        """
        try:
            # Read and check file content
            content = source.path.read_text(encoding='utf-8')
            
            # TODO: Add validation logic
            # Example: Check for expected headers/format
            # if "ExpectedHeader" in content:
            #     return ValidationResult.perfect_match()
            
            # For now, accept based on file extension match
            return ValidationResult.pattern_match()
            
        except Exception as e:
            return ValidationResult.no_match(str(e))
    
    # =========================================================================
    # Required Methods
    # =========================================================================
    
    def convert(
        self,
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """
        Convert the source file to a UUTReport.
        
        Args:
            source: Information about the source file
            context: Conversion context with configuration
            
        Returns:
            ConverterResult with the converted report
        """
        try:
            # Read the source file
            content = source.path.read_text(encoding='utf-8')
            
            # TODO: Parse your file format here
            # Example for a simple data extraction:
            # data = self._parse_file(content)
            
            # Create the report using UUTReport model
            report = self._build_report(content, context)
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE
            )
            
        except Exception as e:
            return ConverterResult.failed_result(
                error=str(e),
                post_action=PostProcessAction.KEEP
            )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _build_report(self, content: str, context: ConverterContext) -> UUTReport:
        """
        Build a UUTReport from the parsed content.
        
        This is where you create the report structure with all steps.
        """
        # TODO: Extract these from your file
        part_number = "PART-001"
        serial_number = "SN-001"
        
        # Create the report
        report = UUTReport(
            pn=part_number,
            sn=serial_number,
        )
        
        # Set result based on test data
        report.result = "Passed"
        
        # TODO: Add steps from your test data
        # Example: Add a numeric measurement step
        # report.add_numeric_step(
        #     name="Voltage Test",
        #     status="Passed",
        #     value=5.02,
        #     unit="V",
        #     low_limit=4.8,
        #     high_limit=5.2,
        # )
        
        return report
'''

FOLDER_CONVERTER_TEMPLATE = '''"""
{name} Folder Converter

{description}

Author: {author}
Version: {version}
"""

from pathlib import Path
from typing import Dict, List, Any

from pywats_client.converters import (
    FolderConverter,
    ConverterSource,
    ConverterContext,
    ConverterResult,
    ValidationResult,
    PostProcessAction,
)
from pywats.domains.report.report_models import UUTReport


class {class_name}(FolderConverter):
    """
    {description}
    
    This converter processes entire folders when they are "ready".
    Useful for test equipment that outputs multiple files per test.
    """
    
    @property
    def name(self) -> str:
        return "{name}"
    
    @property
    def version(self) -> str:
        return "{version}"
    
    @property
    def marker_file(self) -> str:
        """File that indicates the folder is ready for processing"""
        return "complete.flag"
    
    def is_folder_ready(self, folder: Path, context: ConverterContext) -> bool:
        """Check if folder is ready for processing"""
        marker = folder / self.marker_file
        return marker.exists()
    
    def convert_folder(
        self,
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Convert all files in the folder to a single report"""
        try:
            folder = source.path
            
            # TODO: Process files in the folder
            # files = list(folder.glob("*.dat"))
            
            report = self._build_report(folder, context)
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=str(e))
    
    def _build_report(self, folder: Path, context: ConverterContext) -> UUTReport:
        """Build report from folder contents"""
        report = UUTReport(
            pn="PART-001",
            sn="SN-001",
        )
        report.result = "Passed"
        return report
'''

SCHEDULED_CONVERTER_TEMPLATE = '''"""
{name} Scheduled Converter

{description}

Author: {author}
Version: {version}
"""

from datetime import timedelta
from typing import List, Optional

from pywats_client.converters import (
    ScheduledConverter,
    ConverterContext,
    ConverterResult,
)
from pywats.domains.report.report_models import UUTReport


class {class_name}(ScheduledConverter):
    """
    {description}
    
    This converter runs on a schedule to fetch or generate reports.
    Useful for polling external systems or generating periodic reports.
    """
    
    @property
    def name(self) -> str:
        return "{name}"
    
    @property
    def version(self) -> str:
        return "{version}"
    
    @property
    def schedule_interval(self) -> Optional[timedelta]:
        """How often to run (e.g., every 5 minutes)"""
        return timedelta(minutes=5)
    
    @property
    def run_on_startup(self) -> bool:
        """Whether to run immediately on startup"""
        return False
    
    async def run(self, context: ConverterContext) -> List[ConverterResult]:
        """
        Run the scheduled task.
        
        Returns a list of ConverterResults (can be empty if no work).
        """
        results = []
        
        try:
            # TODO: Implement your scheduled logic here
            # Example: Poll an external API, check a database, etc.
            
            # If you have data to convert:
            # report = self._build_report(data)
            # results.append(ConverterResult.success_result(report=report))
            
            pass
            
        except Exception as e:
            results.append(ConverterResult.failed_result(error=str(e)))
        
        return results
    
    def _build_report(self, data: dict) -> UUTReport:
        """Build report from fetched data"""
        report = UUTReport(
            pn="PART-001",
            sn="SN-001",
        )
        report.result = "Passed"
        return report
'''


class NewConverterDialog(QDialog):
    """Dialog for creating new converter files"""
    
    TEMPLATES = {
        "File Converter": FILE_CONVERTER_TEMPLATE,
        "Folder Converter": FOLDER_CONVERTER_TEMPLATE,
        "Scheduled Converter": SCHEDULED_CONVERTER_TEMPLATE,
    }
    
    def __init__(
        self, 
        converters_folder: str = "",
        parent=None
    ):
        super().__init__(parent)
        self.converters_folder = Path(converters_folder) if converters_folder else None
        self.created_path: Optional[Path] = None
        
        self.setWindowTitle("Create New Converter")
        self.resize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Converter details group
        details_group = QGroupBox("Converter Details")
        details_layout = QFormLayout(details_group)
        
        # Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., My CSV Converter")
        self._name_edit.textChanged.connect(self._update_class_name)
        details_layout.addRow("Name:", self._name_edit)
        
        # Class name (auto-generated)
        self._class_edit = QLineEdit()
        self._class_edit.setPlaceholderText("e.g., MyCsvConverter")
        details_layout.addRow("Class Name:", self._class_edit)
        
        # Type
        self._type_combo = QComboBox()
        self._type_combo.addItems(list(self.TEMPLATES.keys()))
        details_layout.addRow("Type:", self._type_combo)
        
        # Version
        self._version_edit = QLineEdit()
        self._version_edit.setText("1.0.0")
        details_layout.addRow("Version:", self._version_edit)
        
        # Author
        self._author_edit = QLineEdit()
        details_layout.addRow("Author:", self._author_edit)
        
        # File patterns
        self._patterns_edit = QLineEdit()
        self._patterns_edit.setPlaceholderText("*.csv, *.txt")
        self._patterns_edit.setText("*.*")
        details_layout.addRow("File Patterns:", self._patterns_edit)
        
        layout.addWidget(details_group)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Describe what this converter does...")
        self._desc_edit.setMaximumHeight(100)
        desc_layout.addWidget(self._desc_edit)
        
        layout.addWidget(desc_group)
        
        # File name preview
        self._file_label = QLabel()
        self._file_label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(self._file_label)
        
        layout.addStretch()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_create)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _update_class_name(self, name: str) -> None:
        """Auto-generate class name from name"""
        # Convert to PascalCase
        words = name.replace("-", " ").replace("_", " ").split()
        class_name = "".join(w.capitalize() for w in words)
        
        # Ensure it ends with "Converter"
        if not class_name.endswith("Converter"):
            class_name += "Converter"
        
        self._class_edit.setText(class_name)
        
        # Update file name preview
        file_name = self._get_file_name()
        if self.converters_folder:
            self._file_label.setText(f"Will create: {self.converters_folder / file_name}")
        else:
            self._file_label.setText(f"File name: {file_name}")
    
    def _get_file_name(self) -> str:
        """Generate file name from class name"""
        class_name = self._class_edit.text()
        if not class_name:
            return "converter.py"
        
        # Convert PascalCase to snake_case
        import re
        file_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        return f"{file_name}.py"
    
    def _on_create(self) -> None:
        """Create the converter file"""
        name = self._name_edit.text().strip()
        class_name = self._class_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        
        if not class_name:
            QMessageBox.warning(self, "Validation", "Class name is required.")
            return
        
        if not self.converters_folder:
            QMessageBox.warning(self, "Validation", "No converters folder configured.")
            return
        
        # Get template
        template_name = self._type_combo.currentText()
        template = self.TEMPLATES[template_name]
        
        # Parse patterns
        patterns_str = self._patterns_edit.text().strip()
        patterns = [p.strip() for p in patterns_str.split(",") if p.strip()]
        patterns_repr = repr(patterns) if patterns else '["*.*"]'
        
        # Format template
        content = template.format(
            name=name,
            class_name=class_name,
            version=self._version_edit.text() or "1.0.0",
            author=self._author_edit.text() or "",
            description=self._desc_edit.toPlainText() or f"{name} converter",
            patterns=patterns_repr,
        )
        
        # Write file
        file_path = self.converters_folder / self._get_file_name()
        
        if file_path.exists():
            reply = QMessageBox.question(
                self, "File Exists",
                f"File {file_path.name} already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        try:
            file_path.write_text(content, encoding='utf-8')
            self.created_path = file_path
            
            QMessageBox.information(
                self, "Created",
                f"Converter created:\n{file_path}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to create converter:\n{e}"
            )
