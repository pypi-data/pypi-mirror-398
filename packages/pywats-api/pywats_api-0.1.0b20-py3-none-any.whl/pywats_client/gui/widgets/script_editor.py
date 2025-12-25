"""
Script Editor Widget

Advanced converter script editor with:
- Tree view showing class structure and functions
- Function-by-function editing
- Syntax highlighting
- Base class method detection
- Custom helper function support
"""

import ast
import re
import inspect
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget,
    QTreeWidgetItem, QPlainTextEdit, QLabel, QFrame, QToolBar,
    QPushButton, QComboBox, QMessageBox, QMenu, QTabWidget,
    QLineEdit, QTextEdit, QGroupBox, QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat, 
    QTextDocument, QAction, QIcon
)


class NodeType(Enum):
    """Type of node in the code tree"""
    ROOT = "root"
    CLASS = "class"
    BASE_CLASS = "base_class"
    PROPERTY = "property"
    ABSTRACT_METHOD = "abstract_method"
    METHOD = "method"
    HELPER_FUNCTION = "helper"
    IMPORT = "import"
    CONSTANT = "constant"


@dataclass
class CodeNode:
    """Represents a node in the code structure"""
    name: str
    node_type: NodeType
    start_line: int = 0
    end_line: int = 0
    source: str = ""
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    parameters: str = ""
    return_type: str = ""
    is_overridden: bool = False
    is_required: bool = False  # For abstract methods
    children: List['CodeNode'] = field(default_factory=list)
    
    @property
    def signature(self) -> str:
        """Get method/function signature"""
        if self.node_type in (NodeType.METHOD, NodeType.ABSTRACT_METHOD, 
                              NodeType.HELPER_FUNCTION):
            sig = f"def {self.name}({self.parameters})"
            if self.return_type:
                sig += f" -> {self.return_type}"
            return sig
        elif self.node_type == NodeType.PROPERTY:
            sig = f"@property\ndef {self.name}(self)"
            if self.return_type:
                sig += f" -> {self.return_type}"
            return sig
        return self.name


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code"""
    
    KEYWORDS = [
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
        'while', 'with', 'yield'
    ]
    
    BUILTINS = [
        'abs', 'all', 'any', 'bin', 'bool', 'bytes', 'callable', 'chr',
        'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
        'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
        'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
        'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
        'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object',
        'oct', 'open', 'ord', 'pow', 'print', 'property', 'range', 'repr',
        'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
        'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
    ]
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._setup_formats()
        self._setup_rules()
    
    def _setup_formats(self) -> None:
        """Setup text formats for different syntax elements"""
        # Keywords
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569cd6"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # Strings
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#ce9178"))
        
        # Comments
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6a9955"))
        self.comment_format.setFontItalic(True)
        
        # Numbers
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#b5cea8"))
        
        # Functions/methods
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#dcdcaa"))
        
        # Classes
        self.class_format = QTextCharFormat()
        self.class_format.setForeground(QColor("#4ec9b0"))
        
        # Decorators
        self.decorator_format = QTextCharFormat()
        self.decorator_format.setForeground(QColor("#c586c0"))
        
        # Built-ins
        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor("#4fc1ff"))
        
        # Self
        self.self_format = QTextCharFormat()
        self.self_format.setForeground(QColor("#9cdcfe"))
        self.self_format.setFontItalic(True)
    
    def _setup_rules(self) -> None:
        """Setup highlighting rules"""
        self.rules = []
        
        # Keywords
        keyword_pattern = r'\b(' + '|'.join(self.KEYWORDS) + r')\b'
        self.rules.append((re.compile(keyword_pattern), self.keyword_format))
        
        # Built-ins
        builtin_pattern = r'\b(' + '|'.join(self.BUILTINS) + r')\b'
        self.rules.append((re.compile(builtin_pattern), self.builtin_format))
        
        # Self
        self.rules.append((re.compile(r'\bself\b'), self.self_format))
        
        # Decorators
        self.rules.append((re.compile(r'@\w+'), self.decorator_format))
        
        # Function definitions
        self.rules.append((re.compile(r'\bdef\s+(\w+)'), self.function_format))
        
        # Class definitions
        self.rules.append((re.compile(r'\bclass\s+(\w+)'), self.class_format))
        
        # Numbers
        self.rules.append((re.compile(r'\b\d+\.?\d*\b'), self.number_format))
        
        # Single-line strings
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format))
        
        # Comments
        self.rules.append((re.compile(r'#.*'), self.comment_format))
    
    def highlightBlock(self, text: str) -> None:
        """Apply highlighting to a block of text"""
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, fmt)


class CodeParser:
    """Parses Python source code to extract structure"""
    
    # Known FileConverter base class methods
    BASE_CLASS_METHODS = {
        # Required (abstract)
        'name': {'type': 'property', 'required': True, 'return_type': 'str'},
        'convert': {'type': 'method', 'required': True, 'params': 'source: ConverterSource, context: ConverterContext', 'return_type': 'ConverterResult'},
        
        # Optional properties
        'version': {'type': 'property', 'required': False, 'return_type': 'str'},
        'description': {'type': 'property', 'required': False, 'return_type': 'str'},
        'author': {'type': 'property', 'required': False, 'return_type': 'str'},
        'converter_type': {'type': 'property', 'required': False, 'return_type': 'ConverterType'},
        'file_patterns': {'type': 'property', 'required': False, 'return_type': 'List[str]'},
        'arguments_schema': {'type': 'property', 'required': False, 'return_type': 'Dict[str, ArgumentDefinition]'},
        
        # Optional methods
        'validate': {'type': 'method', 'required': False, 'params': 'source: ConverterSource, context: ConverterContext', 'return_type': 'ValidationResult'},
        'on_convert_start': {'type': 'method', 'required': False, 'params': 'source: ConverterSource, context: ConverterContext', 'return_type': 'None'},
        'on_convert_complete': {'type': 'method', 'required': False, 'params': 'source: ConverterSource, result: ConverterResult, context: ConverterContext', 'return_type': 'None'},
        'on_convert_error': {'type': 'method', 'required': False, 'params': 'source: ConverterSource, error: Exception, context: ConverterContext', 'return_type': 'None'},
    }
    
    def __init__(self, source_code: str = ""):
        self.source_code = source_code
        self.lines = source_code.split('\n') if source_code else []
    
    def parse(self) -> CodeNode:
        """Parse source code and return root node"""
        root = CodeNode(
            name="Root",
            node_type=NodeType.ROOT,
            start_line=1,
            end_line=len(self.lines)
        )
        
        if not self.source_code:
            return root
        
        try:
            tree = ast.parse(self.source_code)
            self._parse_module(tree, root)
        except SyntaxError as e:
            # Add error node
            error_node = CodeNode(
                name=f"Syntax Error: {e.msg}",
                node_type=NodeType.CONSTANT,
                start_line=e.lineno or 1
            )
            root.children.append(error_node)
        
        return root
    
    def _parse_module(self, tree: ast.Module, root: CodeNode) -> None:
        """Parse module-level elements"""
        imports_node = CodeNode(
            name="Imports",
            node_type=NodeType.IMPORT,
            start_line=1
        )
        
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_code = self._get_source(node.lineno, node.end_lineno or node.lineno)
                import_node = CodeNode(
                    name=import_code.strip(),
                    node_type=NodeType.IMPORT,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    source=import_code
                )
                imports_node.children.append(import_node)
                
            elif isinstance(node, ast.ClassDef):
                class_node = self._parse_class(node)
                root.children.append(class_node)
                
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_node = self._parse_function(node, is_method=False)
                func_node.node_type = NodeType.HELPER_FUNCTION
                root.children.append(func_node)
                
            elif isinstance(node, ast.Assign):
                # Module-level constants
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        const_node = CodeNode(
                            name=target.id,
                            node_type=NodeType.CONSTANT,
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            source=self._get_source(node.lineno, node.end_lineno or node.lineno)
                        )
                        root.children.append(const_node)
        
        # Only add imports if we found some
        if imports_node.children:
            imports_node.end_line = imports_node.children[-1].end_line
            imports_node.source = '\n'.join(c.source for c in imports_node.children)
            root.children.insert(0, imports_node)
    
    def _parse_class(self, node: ast.ClassDef) -> CodeNode:
        """Parse a class definition"""
        # Detect if it's a converter class
        bases = [self._get_base_name(b) for b in node.bases]
        is_converter = any(b in ('FileConverter', 'FolderConverter', 
                                  'ScheduledConverter', 'ConverterBase') 
                          for b in bases)
        
        class_node = CodeNode(
            name=node.name,
            node_type=NodeType.CLASS,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            source=self._get_source(node.lineno, node.end_lineno or node.lineno),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list]
        )
        
        # Get class docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            class_node.docstring = node.body[0].value.value
        
        # Track which base methods are overridden
        overridden_methods: Set[str] = set()
        
        # Parse class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                func_node = self._parse_function(item, is_method=True)
                
                # Check if this overrides a base class method
                if is_converter and func_node.name in self.BASE_CLASS_METHODS:
                    func_node.is_overridden = True
                    overridden_methods.add(func_node.name)
                    
                    base_info = self.BASE_CLASS_METHODS[func_node.name]
                    if base_info['required']:
                        func_node.is_required = True
                
                class_node.children.append(func_node)
        
        # Add placeholder nodes for unimplemented base class methods
        if is_converter:
            base_methods_node = CodeNode(
                name="Base Class Methods",
                node_type=NodeType.BASE_CLASS,
                start_line=0
            )
            
            for method_name, info in self.BASE_CLASS_METHODS.items():
                if method_name not in overridden_methods:
                    placeholder = CodeNode(
                        name=method_name,
                        node_type=NodeType.ABSTRACT_METHOD if info['required'] else NodeType.METHOD,
                        is_required=info['required'],
                        is_overridden=False,
                        return_type=info.get('return_type', ''),
                        parameters=info.get('params', 'self'),
                        docstring=f"{'Required' if info['required'] else 'Optional'} - Not implemented"
                    )
                    base_methods_node.children.append(placeholder)
            
            if base_methods_node.children:
                # Insert at beginning of class children
                class_node.children.insert(0, base_methods_node)
        
        return class_node
    
    def _parse_function(self, node: ast.FunctionDef, is_method: bool = False) -> CodeNode:
        """Parse a function definition"""
        # Check for property decorator
        is_property = any(
            self._get_decorator_name(d) == 'property' 
            for d in node.decorator_list
        )
        
        # Get parameters
        params = self._get_params(node.args)
        
        # Get return type
        return_type = ""
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        func_node = CodeNode(
            name=node.name,
            node_type=NodeType.PROPERTY if is_property else NodeType.METHOD,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            source=self._get_source(node.lineno, node.end_lineno or node.lineno),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            parameters=params,
            return_type=return_type
        )
        
        # Get docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            func_node.docstring = node.body[0].value.value
        
        return func_node
    
    def _get_source(self, start: int, end: int) -> str:
        """Get source code for line range"""
        if start < 1 or end > len(self.lines):
            return ""
        return '\n'.join(self.lines[start-1:end])
    
    def _get_base_name(self, node: ast.expr) -> str:
        """Get base class name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return ""
    
    def _get_params(self, args: ast.arguments) -> str:
        """Get function parameters as string"""
        parts = []
        
        # Regular args
        defaults_offset = len(args.args) - len(args.defaults)
        for i, arg in enumerate(args.args):
            param = arg.arg
            if arg.annotation:
                param += f": {ast.unparse(arg.annotation)}"
            
            # Check for default
            default_idx = i - defaults_offset
            if default_idx >= 0 and default_idx < len(args.defaults):
                param += f" = {ast.unparse(args.defaults[default_idx])}"
            
            parts.append(param)
        
        # *args
        if args.vararg:
            param = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                param += f": {ast.unparse(args.vararg.annotation)}"
            parts.append(param)
        
        # **kwargs
        if args.kwarg:
            param = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                param += f": {ast.unparse(args.kwarg.annotation)}"
            parts.append(param)
        
        return ", ".join(parts)


class ScriptEditorWidget(QWidget):
    """
    Advanced script editor for converter files.
    
    Features:
    - Tree view showing file structure (classes, methods, helpers)
    - Function-by-function editing in separate panels
    - Syntax highlighting
    - Base class method detection and status
    - Quick navigation via tree selection
    """
    
    # Emitted when content changes
    content_changed = Signal()
    
    # Emitted when a function is saved
    function_saved = Signal(str, str)  # function_name, new_source
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._file_path: Optional[Path] = None
        self._source_code: str = ""
        self._code_tree: Optional[CodeNode] = None
        self._current_node: Optional[CodeNode] = None
        self._modified = False
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the editor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Main splitter (tree | editor)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Tree view
        tree_frame = QFrame()
        tree_frame.setObjectName("treeFrame")
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(5, 5, 5, 5)
        
        tree_label = QLabel("Structure")
        tree_label.setObjectName("sectionLabel")
        tree_layout.addWidget(tree_label)
        
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        tree_layout.addWidget(self._tree)
        
        splitter.addWidget(tree_frame)
        
        # Right: Editor area with tabs
        editor_frame = QFrame()
        editor_frame.setObjectName("editorFrame")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(5, 5, 5, 5)
        
        # Function info header
        info_layout = QHBoxLayout()
        self._func_label = QLabel("Select a function from the tree")
        self._func_label.setObjectName("functionLabel")
        info_layout.addWidget(self._func_label)
        info_layout.addStretch()
        
        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        info_layout.addWidget(self._status_label)
        editor_layout.addLayout(info_layout)
        
        # Tabs for different views
        self._tabs = QTabWidget()
        
        # Code tab
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)
        code_layout.setContentsMargins(0, 0, 0, 0)
        
        self._code_editor = QPlainTextEdit()
        self._code_editor.setFont(QFont("Consolas", 10))
        self._code_editor.textChanged.connect(self._on_code_changed)
        self._highlighter = PythonSyntaxHighlighter(self._code_editor.document())
        code_layout.addWidget(self._code_editor)
        
        self._tabs.addTab(code_widget, "Code")
        
        # Documentation tab
        doc_widget = QWidget()
        doc_layout = QVBoxLayout(doc_widget)
        doc_layout.setContentsMargins(5, 5, 5, 5)
        
        self._doc_text = QTextEdit()
        self._doc_text.setReadOnly(True)
        self._doc_text.setStyleSheet("background-color: #2d2d2d;")
        doc_layout.addWidget(self._doc_text)
        
        self._tabs.addTab(doc_widget, "Documentation")
        
        # Settings tab (for properties/methods with schemas)
        settings_widget = QWidget()
        settings_layout = QFormLayout(settings_widget)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., CSV Converter")
        settings_layout.addRow("Name:", self._name_edit)
        
        self._version_edit = QLineEdit()
        self._version_edit.setPlaceholderText("e.g., 1.0.0")
        settings_layout.addRow("Version:", self._version_edit)
        
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Description of what this converter does")
        settings_layout.addRow("Description:", self._desc_edit)
        
        self._author_edit = QLineEdit()
        self._author_edit.setPlaceholderText("Author name")
        settings_layout.addRow("Author:", self._author_edit)
        
        self._patterns_edit = QLineEdit()
        self._patterns_edit.setPlaceholderText("*.csv, *.txt")
        settings_layout.addRow("File Patterns:", self._patterns_edit)
        
        self._tabs.addTab(settings_widget, "Settings")
        
        editor_layout.addWidget(self._tabs)
        
        splitter.addWidget(editor_frame)
        
        # Set splitter proportions
        splitter.setSizes([250, 650])
        
        layout.addWidget(splitter)
        
        # Apply styles
        self._apply_styles()
    
    def _create_toolbar(self) -> QToolBar:
        """Create the editor toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        
        # Save action
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)
        toolbar.addAction(save_action)
        
        # Reload action
        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self._on_reload)
        toolbar.addAction(reload_action)
        
        toolbar.addSeparator()
        
        # Add method action
        add_method_action = QAction("Add Method", self)
        add_method_action.triggered.connect(self._on_add_method)
        toolbar.addAction(add_method_action)
        
        # Add helper action
        add_helper_action = QAction("Add Helper", self)
        add_helper_action.triggered.connect(self._on_add_helper)
        toolbar.addAction(add_helper_action)
        
        toolbar.addSeparator()
        
        # Validate action
        validate_action = QAction("Validate", self)
        validate_action.triggered.connect(self._on_validate)
        toolbar.addAction(validate_action)
        
        return toolbar
    
    def _apply_styles(self) -> None:
        """Apply editor styles"""
        self.setStyleSheet("""
            #treeFrame, #editorFrame {
                background-color: #1e1e1e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
            
            #sectionLabel, #functionLabel {
                color: #e0e0e0;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 0;
            }
            
            #statusLabel {
                color: #808080;
                font-size: 11px;
            }
            
            QTreeWidget {
                background-color: #252526;
                border: none;
                color: #d4d4d4;
            }
            
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                selection-background-color: #264f78;
            }
            
            QTabWidget::pane {
                border: 1px solid #3e3e3e;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px 16px;
                border: 1px solid #3e3e3e;
                border-bottom: none;
            }
            
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #0078d4;
            }
            
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def load_file(self, file_path: str) -> bool:
        """Load a converter file"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            self._source_code = path.read_text(encoding='utf-8')
            self._file_path = path
            self._modified = False
            
            # Parse and update tree
            self._refresh_tree()
            
            return True
        except Exception as e:
            QMessageBox.critical(
                self, "Load Error",
                f"Failed to load file:\n{e}"
            )
            return False
    
    def load_source(self, source: str, file_path: Optional[str] = None) -> None:
        """Load source code directly"""
        self._source_code = source
        self._file_path = Path(file_path) if file_path else None
        self._modified = False
        self._refresh_tree()
    
    def get_source(self) -> str:
        """Get current source code"""
        return self._source_code
    
    def is_modified(self) -> bool:
        """Check if content has been modified"""
        return self._modified
    
    def save(self) -> bool:
        """Save to file"""
        if not self._file_path:
            return False
        
        try:
            self._file_path.write_text(self._source_code, encoding='utf-8')
            self._modified = False
            return True
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save file:\n{e}"
            )
            return False
    
    # =========================================================================
    # Tree Management
    # =========================================================================
    
    def _refresh_tree(self) -> None:
        """Refresh the code tree"""
        self._tree.clear()
        
        parser = CodeParser(self._source_code)
        self._code_tree = parser.parse()
        
        # Build tree widget
        self._build_tree_items(self._code_tree, None)
        
        # Expand all by default
        self._tree.expandAll()
    
    def _build_tree_items(
        self, 
        node: CodeNode, 
        parent: Optional[QTreeWidgetItem]
    ) -> None:
        """Recursively build tree items"""
        
        # Skip root node
        if node.node_type == NodeType.ROOT:
            for child in node.children:
                self._build_tree_items(child, None)
            return
        
        # Create tree item
        if parent:
            item = QTreeWidgetItem(parent)
        else:
            item = QTreeWidgetItem(self._tree)
        
        # Set display text and icon based on type
        icon_text = self._get_node_icon(node)
        display_name = f"{icon_text} {node.name}"
        
        # Add status indicators
        if node.is_required and not node.is_overridden:
            display_name += " ⚠️"
        elif node.is_overridden:
            display_name += " ✓"
        
        item.setText(0, display_name)
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        
        # Set color based on type
        color = self._get_node_color(node)
        item.setForeground(0, QColor(color))
        
        # Process children
        for child in node.children:
            self._build_tree_items(child, item)
    
    def _get_node_icon(self, node: CodeNode) -> str:
        """Get icon character for node type"""
        icons = {
            NodeType.CLASS: "🔶",
            NodeType.BASE_CLASS: "📦",
            NodeType.PROPERTY: "🔷",
            NodeType.ABSTRACT_METHOD: "⚡",
            NodeType.METHOD: "📘",
            NodeType.HELPER_FUNCTION: "🔧",
            NodeType.IMPORT: "📥",
            NodeType.CONSTANT: "📌",
        }
        return icons.get(node.node_type, "")
    
    def _get_node_color(self, node: CodeNode) -> str:
        """Get display color for node type"""
        colors = {
            NodeType.CLASS: "#4ec9b0",
            NodeType.BASE_CLASS: "#808080",
            NodeType.PROPERTY: "#9cdcfe",
            NodeType.ABSTRACT_METHOD: "#dcdcaa",
            NodeType.METHOD: "#dcdcaa",
            NodeType.HELPER_FUNCTION: "#c586c0",
            NodeType.IMPORT: "#6a9955",
            NodeType.CONSTANT: "#b5cea8",
        }
        return colors.get(node.node_type, "#d4d4d4")
    
    # =========================================================================
    # Event Handlers
    # =========================================================================
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle tree item selection"""
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if not node:
            return
        
        self._current_node = node
        self._update_editor(node)
    
    def _on_tree_context_menu(self, position) -> None:
        """Show context menu for tree item"""
        item = self._tree.itemAt(position)
        if not item:
            return
        
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if not node:
            return
        
        menu = QMenu(self)
        
        if node.node_type in (NodeType.METHOD, NodeType.ABSTRACT_METHOD, 
                              NodeType.PROPERTY, NodeType.HELPER_FUNCTION):
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(lambda: self._update_editor(node))
            
            if not node.is_required:
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self._delete_node(node))
        
        elif node.node_type == NodeType.CLASS:
            add_method = menu.addAction("Add Method")
            add_method.triggered.connect(self._on_add_method)
        
        elif node.node_type == NodeType.BASE_CLASS:
            implement_all = menu.addAction("Implement All Required")
            implement_all.triggered.connect(self._on_implement_all_required)
        
        menu.exec_(self._tree.mapToGlobal(position))
    
    def _update_editor(self, node: CodeNode) -> None:
        """Update editor with node content"""
        # Update function label
        self._func_label.setText(node.signature if hasattr(node, 'signature') else node.name)
        
        # Update status
        status_parts = []
        if node.is_required:
            status_parts.append("Required")
        if node.is_overridden:
            status_parts.append("Implemented")
        elif node.node_type == NodeType.ABSTRACT_METHOD:
            status_parts.append("Not Implemented")
        if node.start_line > 0:
            status_parts.append(f"Lines {node.start_line}-{node.end_line}")
        self._status_label.setText(" | ".join(status_parts))
        
        # Update code editor
        if node.source:
            self._code_editor.setPlainText(node.source)
        elif node.node_type in (NodeType.ABSTRACT_METHOD, NodeType.METHOD, NodeType.PROPERTY):
            # Generate template for unimplemented methods
            template = self._generate_method_template(node)
            self._code_editor.setPlainText(template)
        else:
            self._code_editor.clear()
        
        # Update documentation
        if node.docstring:
            self._doc_text.setHtml(self._format_docstring(node.docstring))
        else:
            self._doc_text.setPlainText("No documentation available")
    
    def _format_docstring(self, docstring: str) -> str:
        """Format docstring as HTML"""
        # Basic formatting
        html = docstring.replace('\n', '<br>')
        
        # Highlight Args, Returns, etc.
        for section in ['Args:', 'Returns:', 'Raises:', 'Example:', 'Note:']:
            html = html.replace(section, f'<b style="color: #569cd6">{section}</b>')
        
        return f'<div style="color: #d4d4d4; font-family: Consolas; font-size: 10pt;">{html}</div>'
    
    def _generate_method_template(self, node: CodeNode) -> str:
        """Generate template code for a method"""
        decorators = ""
        if node.node_type == NodeType.PROPERTY:
            decorators = "@property\n    "
        
        params = node.parameters if node.parameters else "self"
        return_type = f" -> {node.return_type}" if node.return_type else ""
        
        template = f'''    {decorators}def {node.name}({params}){return_type}:
        """
        TODO: Implement this method
        """
        raise NotImplementedError("{node.name} not implemented")
'''
        return template
    
    def _on_code_changed(self) -> None:
        """Handle code change"""
        if self._current_node and self._current_node.source:
            self._modified = True
            self.content_changed.emit()
    
    def _on_save(self) -> None:
        """Handle save action"""
        if self._current_node:
            # Update node source
            new_source = self._code_editor.toPlainText()
            self._update_node_source(self._current_node, new_source)
        
        # Save file
        if self._file_path:
            self.save()
            QMessageBox.information(self, "Saved", f"Saved to {self._file_path}")
    
    def _on_reload(self) -> None:
        """Handle reload action"""
        if self._file_path:
            self.load_file(str(self._file_path))
    
    def _on_add_method(self) -> None:
        """Add a new method to the class"""
        # Show dialog to get method details
        # For now, just add a template
        template = '''
    def new_method(self) -> None:
        """
        TODO: Describe what this method does
        """
        pass
'''
        self._code_editor.setPlainText(template)
        self._func_label.setText("New Method")
    
    def _on_add_helper(self) -> None:
        """Add a new helper function"""
        template = '''
def helper_function(arg1, arg2):
    """
    Helper function for converter.
    
    Args:
        arg1: First argument
        arg2: Second argument
    
    Returns:
        Processed result
    """
    pass
'''
        self._code_editor.setPlainText(template)
        self._func_label.setText("New Helper Function")
    
    def _on_validate(self) -> None:
        """Validate the converter code"""
        try:
            ast.parse(self._source_code)
            
            # Check for required methods
            missing = []
            if self._code_tree:
                for child in self._code_tree.children:
                    if child.node_type == NodeType.CLASS:
                        for method in child.children:
                            if (method.node_type == NodeType.BASE_CLASS):
                                for base_method in method.children:
                                    if base_method.is_required and not base_method.is_overridden:
                                        missing.append(base_method.name)
            
            if missing:
                QMessageBox.warning(
                    self, "Validation Warning",
                    f"Missing required methods:\n• " + "\n• ".join(missing)
                )
            else:
                QMessageBox.information(
                    self, "Validation OK",
                    "Converter code is valid!"
                )
        except SyntaxError as e:
            QMessageBox.critical(
                self, "Syntax Error",
                f"Line {e.lineno}: {e.msg}"
            )
    
    def _on_implement_all_required(self) -> None:
        """Implement all required methods"""
        if not self._code_tree:
            return
        
        templates = []
        for child in self._code_tree.children:
            if child.node_type == NodeType.CLASS:
                for item in child.children:
                    if item.node_type == NodeType.BASE_CLASS:
                        for method in item.children:
                            if method.is_required and not method.is_overridden:
                                templates.append(self._generate_method_template(method))
        
        if templates:
            code = "\n".join(templates)
            self._code_editor.setPlainText(code)
            self._func_label.setText("Required Methods Template")
    
    def _delete_node(self, node: CodeNode) -> None:
        """Delete a node from the source"""
        if node.start_line == 0:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {node.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove lines from source
            lines = self._source_code.split('\n')
            del lines[node.start_line - 1:node.end_line]
            self._source_code = '\n'.join(lines)
            self._modified = True
            self._refresh_tree()
    
    def _update_node_source(self, node: CodeNode, new_source: str) -> None:
        """Update node source in the full source code"""
        if node.start_line == 0:
            # New node - append to class
            # For now, just mark as modified
            self._modified = True
            return
        
        lines = self._source_code.split('\n')
        new_lines = new_source.split('\n')
        
        # Replace lines
        lines[node.start_line - 1:node.end_line] = new_lines
        
        self._source_code = '\n'.join(lines)
        node.source = new_source
        node.end_line = node.start_line + len(new_lines) - 1
        
        self._modified = True
