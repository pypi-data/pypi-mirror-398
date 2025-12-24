"""Modal dialogs and popups"""
import asyncio
import threading
from typing import Optional, Callable, List
from enum import Enum


class DialogType(Enum):
    """Dialog types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CONFIRM = "confirm"
    INPUT = "input"


class Dialog:
    """Thread-safe modal dialog"""
    
    def __init__(
        self,
        title: str,
        message: str,
        dialog_type: DialogType = DialogType.INFO
    ) -> None:
        """Initialize dialog
        
        Args:
            title: Dialog title
            message: Dialog message
            dialog_type: Type of dialog
        """
        self.title: str = title
        self.message: str = message
        self.dialog_type: DialogType = dialog_type
        self.lock: threading.RLock = threading.RLock()
        self.result: Optional[str] = None
        self.is_open: bool = False
    
    def open(self) -> None:
        """Open dialog (thread-safe)"""
        with self.lock:
            self.is_open = True
    
    def close(self, result: Optional[str] = None) -> None:
        """Close dialog (thread-safe)
        
        Args:
            result: Result value
        """
        with self.lock:
            self.is_open = False
            self.result = result
    
    def get_result(self) -> Optional[str]:
        """Get dialog result (thread-safe)"""
        with self.lock:
            return self.result
    
    def is_visible(self) -> bool:
        """Check if dialog is visible (thread-safe)"""
        with self.lock:
            return self.is_open
    
    def get_display(self) -> str:
        """Get dialog display (thread-safe)"""
        with self.lock:
            border = "╔" + "═" * (len(self.title) + 2) + "╗"
            title_line = f"║ {self.title} ║"
            close_border = "╚" + "═" * (len(self.title) + 2) + "╝"
            
            lines = [border, title_line, close_border, "", self.message]
            
            return "\n".join(lines)


class ConfirmDialog(Dialog):
    """Confirmation dialog"""
    
    def __init__(self, title: str, message: str) -> None:
        """Initialize confirm dialog
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        super().__init__(title, message, DialogType.CONFIRM)
        self.confirmed: bool = False
    
    def confirm(self) -> None:
        """Confirm dialog"""
        with self.lock:
            self.confirmed = True
            self.result = "yes"
            self.is_open = False
    
    def cancel(self) -> None:
        """Cancel dialog"""
        with self.lock:
            self.confirmed = False
            self.result = "no"
            self.is_open = False
    
    def is_confirmed(self) -> bool:
        """Check if confirmed (thread-safe)"""
        with self.lock:
            return self.confirmed
    
    def get_display(self) -> str:
        """Get dialog display (thread-safe)"""
        base = super().get_display()
        return base + "\n\n[Y]es  [N]o"


class InputDialog(Dialog):
    """Input dialog"""
    
    def __init__(self, title: str, prompt: str, default: str = "") -> None:
        """Initialize input dialog
        
        Args:
            title: Dialog title
            prompt: Input prompt
            default: Default value
        """
        super().__init__(title, prompt, DialogType.INPUT)
        self.input_value: str = default
    
    def set_input(self, value: str) -> None:
        """Set input value (thread-safe)
        
        Args:
            value: Input value
        """
        with self.lock:
            self.input_value = value
    
    def get_input(self) -> str:
        """Get input value (thread-safe)"""
        with self.lock:
            return self.input_value
    
    def submit(self) -> None:
        """Submit input"""
        with self.lock:
            self.result = self.input_value
            self.is_open = False
    
    def get_display(self) -> str:
        """Get dialog display (thread-safe)"""
        base = super().get_display()
        with self.lock:
            cursor = self.input_value + "│"
            return base + f"\n\n> {cursor}"


class MenuDialog:
    """Dialog with menu options"""
    
    def __init__(self, title: str, options: List[str]) -> None:
        """Initialize menu dialog
        
        Args:
            title: Dialog title
            options: Menu options
        """
        self.title: str = title
        self.options: List[str] = options
        self.selected_index: int = 0
        self.lock: threading.RLock = threading.RLock()
        self.result: Optional[str] = None
        self.is_open: bool = False
    
    def open(self) -> None:
        """Open dialog (thread-safe)"""
        with self.lock:
            self.is_open = True
    
    def close(self, result: Optional[str] = None) -> None:
        """Close dialog (thread-safe)"""
        with self.lock:
            self.is_open = False
            self.result = result
    
    def next_option(self) -> None:
        """Select next option (thread-safe)"""
        with self.lock:
            if self.options:
                self.selected_index = (self.selected_index + 1) % len(self.options)
    
    def previous_option(self) -> None:
        """Select previous option (thread-safe)"""
        with self.lock:
            if self.options:
                self.selected_index = (self.selected_index - 1) % len(self.options)
    
    def select_current(self) -> str:
        """Select current option (thread-safe)"""
        with self.lock:
            if self.options:
                result = self.options[self.selected_index]
                self.result = result
                self.is_open = False
                return result
            return ""
    
    def is_visible(self) -> bool:
        """Check if visible (thread-safe)"""
        with self.lock:
            return self.is_open
    
    def get_result(self) -> Optional[str]:
        """Get result (thread-safe)"""
        with self.lock:
            return self.result
    
    def get_display(self) -> str:
        """Get dialog display (thread-safe)"""
        with self.lock:
            lines = [f"═══ {self.title} ═══", ""]
            
            for i, option in enumerate(self.options):
                marker = "►" if i == self.selected_index else " "
                lines.append(f"{marker} {option}")
            
            return "\n".join(lines)


class ProgressDialog(Dialog):
    """Progress dialog"""
    
    def __init__(self, title: str, message: str = "Processing..") -> None:
        """Initialize progress dialog
        
        Args:
            title: Dialog title
            message: Status message
        """
        super().__init__(title, message, DialogType.INFO)
        self.progress: float = 0.0
        self.max_progress: float = 100.0
    
    def set_progress(self, current: float, maximum: float = 100.0) -> None:
        """Set progress (thread-safe)
        
        Args:
            current: Current progress
            maximum: Maximum progress
        """
        with self.lock:
            self.progress = current
            self.max_progress = maximum
    
    def get_progress(self) -> tuple[float, float]:
        """Get progress (thread-safe)"""
        with self.lock:
            return self.progress, self.max_progress
    
    def get_display(self) -> str:
        """Get dialog display (thread-safe)"""
        base = super().get_display()
        with self.lock:
            percent = (self.progress / self.max_progress * 100) if self.max_progress > 0 else 0
            filled = int(20 * self.progress / max(self.max_progress, 1))
            bar = "█" * filled + "░" * (20 - filled)
            return base + f"\n\n[{bar}] {percent:.1f}%"


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
