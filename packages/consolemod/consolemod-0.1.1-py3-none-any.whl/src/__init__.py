"""ConsoleMod - A powerful, thread-safe terminal UI library"""

# Core module
from .core import TerminalSplitter, Pane, EventBus, KeyEvent, FocusEvent, KeyCode

# UI module
from .ui import (
    Theme, Style, get_theme, register_theme, style_to_rich,
    DARK_THEME, LIGHT_THEME, SOLARIZED_THEME, THEMES,
    Layout, LayoutMode, LayoutConstraints,
    Button, ProgressBar, Spinner, Table
)

# Input module
from .input import InputHandler
from .input.keybindings import KeyBinding, KeyBindingManager, KeyBindingPreset

# Interaction module
from .interaction import (
    Form, Menu, MenuItem, SelectionList, ContextMenu,
    Dialog, ConfirmDialog, InputDialog, MenuDialog, ProgressDialog, DialogType,
)

# Input classes (forms/fields)
from .input import InputField, InputType, SelectField, CheckboxField

# Logging module
from .logging import PaneLogger, LogLevel, StdoutPaneAdapter

# Monitoring module
from .monitoring import (
    PerformanceMonitor, MemoryMonitor, FrameMetrics,
    Debouncer, Throttler, debounced, throttled
)

# Utils module
from .utils import (
    wrap_text, align_text, truncate_text, highlight_text,
    format_bytes, format_duration, create_box, TextAlign,
    load_config, CircularBuffer,
    CommandHistory, UndoRedoStack, StateSnapshot,
    PaneExporter,
)

# Templates (imported lazily to avoid circular imports)
from .utils.templates import (
    LoggerTemplate, DashboardTemplate, MonitorTemplate, ProgressTemplate, TableTemplate
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    
    # Core
    "TerminalSplitter",
    "Pane",
    
    # Events
    "EventBus",
    "KeyEvent",
    "FocusEvent",
    "KeyCode",
    
    # UI - Themes
    "Theme",
    "Style",
    "get_theme",
    "register_theme",
    "style_to_rich",
    "DARK_THEME",
    "LIGHT_THEME",
    "SOLARIZED_THEME",
    "THEMES",
    
    # UI - Layout
    "Layout",
    "LayoutMode",
    "LayoutConstraints",
    
    # UI - Widgets
    "Button",
    "ProgressBar",
    "Spinner",
    "Table",
    
    # Input
    "InputHandler",
    "KeyBinding",
    "KeyBindingManager",
    "KeyBindingPreset",
    
    # Interaction - Forms
    "Form",
    "InputField",
    "InputType",
    "SelectField",
    "CheckboxField",
    
    # Interaction - Menus
    "Menu",
    "MenuItem",
    "SelectionList",
    "ContextMenu",
    
    # Interaction - Dialogs
    "Dialog",
    "ConfirmDialog",
    "InputDialog",
    "MenuDialog",
    "ProgressDialog",
    "DialogType",
    
    # Logging
    "PaneLogger",
    "LogLevel",
    "StdoutPaneAdapter",
    
    # Monitoring
    "PerformanceMonitor",
    "MemoryMonitor",
    "FrameMetrics",
    "Debouncer",
    "Throttler",
    "debounced",
    "throttled",
    
    # Utils - Formatting
    "wrap_text",
    "align_text",
    "truncate_text",
    "highlight_text",
    "format_bytes",
    "format_duration",
    "create_box",
    "TextAlign",
    
    # Utils - Config
    "load_config",
    
    # Utils - Buffer
    "CircularBuffer",
    
    # Utils - History
    "CommandHistory",
    "UndoRedoStack",
    "StateSnapshot",
    
    # Utils - Export
    "PaneExporter",
    
    # Utils - Templates
    "LoggerTemplate",
    "DashboardTemplate",
    "MonitorTemplate",
    "ProgressTemplate",
    "TableTemplate",
]
