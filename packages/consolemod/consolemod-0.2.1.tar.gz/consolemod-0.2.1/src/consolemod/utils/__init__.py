"""Utils module - Formatting, configuration, and utilities"""
from .formatter import (
    wrap_text, align_text, format_bytes, format_duration,
    create_box, truncate_text, highlight_text, TextAlign
)
from .config import load_config
from .export import PaneExporter
from .buffer import CircularBuffer
from .history import CommandHistory, UndoRedoStack, StateSnapshot

# Templates are imported lazily to avoid circular imports
# Import with: from ConsoleMod.utils.templates import LoggerTemplate

__all__ = [
    # Formatter
    "wrap_text", "align_text", "format_bytes", "format_duration",
    "create_box", "truncate_text", "highlight_text", "TextAlign",
    # Config
    "load_config",
    # Export
    "PaneExporter",
    # Buffer
    "CircularBuffer",
    # History
    "CommandHistory", "UndoRedoStack", "StateSnapshot",
    # Note: Templates in .templates submodule to avoid circular imports
]
