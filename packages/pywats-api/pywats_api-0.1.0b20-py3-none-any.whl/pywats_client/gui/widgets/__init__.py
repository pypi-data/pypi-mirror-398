"""
GUI Widgets for pyWATS Client

Reusable widget components for the GUI.
"""

from .script_editor import (
    ScriptEditorWidget,
    CodeParser,
    CodeNode,
    NodeType,
    PythonSyntaxHighlighter,
)
from .new_converter_dialog import NewConverterDialog

__all__ = [
    "ScriptEditorWidget",
    "CodeParser",
    "CodeNode",
    "NodeType",
    "PythonSyntaxHighlighter",
    "NewConverterDialog",
]
