"""Input field and text input handling"""
import threading
from typing import Optional, Callable, List
from enum import Enum


class InputType(Enum):
    """Input field types"""
    TEXT = "text"
    PASSWORD = "password"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"


class InputField:
    """Thread-safe input field for text input"""
    
    def __init__(
        self,
        name: str,
        input_type: InputType = InputType.TEXT,
        placeholder: str = "",
        max_length: int = 255,
        required: bool = False
    ) -> None:
        """Initialize input field
        
        Args:
            name: Field name
            input_type: Type of input
            placeholder: Placeholder text
            max_length: Maximum input length
            required: Whether field is required
        """
        self.name: str = name
        self.input_type: InputType = input_type
        self.placeholder: str = placeholder
        self.max_length: int = max_length
        self.required: bool = required
        self.value: str = ""
        self.lock: threading.RLock = threading.RLock()
        self.is_focused: bool = False
        self.cursor_pos: int = 0
        self.on_change: Optional[Callable] = None
    
    def set_value(self, value: str) -> None:
        """Set field value (thread-safe)
        
        Args:
            value: New value
        """
        with self.lock:
            self.value = value[:self.max_length]
            self.cursor_pos = len(self.value)
            if self.on_change:
                self.on_change(self.value)
    
    def append_char(self, char: str) -> None:
        """Append character at cursor (thread-safe)
        
        Args:
            char: Character to append
        """
        with self.lock:
            if len(self.value) < self.max_length:
                self.value = (
                    self.value[:self.cursor_pos] +
                    char +
                    self.value[self.cursor_pos:]
                )
                self.cursor_pos += 1
                if self.on_change:
                    self.on_change(self.value)
    
    def backspace(self) -> None:
        """Delete character before cursor (thread-safe)"""
        with self.lock:
            if self.cursor_pos > 0:
                self.value = (
                    self.value[:self.cursor_pos-1] +
                    self.value[self.cursor_pos:]
                )
                self.cursor_pos -= 1
                if self.on_change:
                    self.on_change(self.value)
    
    def delete(self) -> None:
        """Delete character at cursor (thread-safe)"""
        with self.lock:
            if self.cursor_pos < len(self.value):
                self.value = (
                    self.value[:self.cursor_pos] +
                    self.value[self.cursor_pos+1:]
                )
                if self.on_change:
                    self.on_change(self.value)
    
    def move_cursor(self, direction: int) -> None:
        """Move cursor (thread-safe)
        
        Args:
            direction: -1 for left, +1 for right
        """
        with self.lock:
            new_pos = self.cursor_pos + direction
            self.cursor_pos = max(0, min(new_pos, len(self.value)))
    
    def clear(self) -> None:
        """Clear field (thread-safe)"""
        with self.lock:
            self.value = ""
            self.cursor_pos = 0
            if self.on_change:
                self.on_change("")
    
    def get_value(self) -> str:
        """Get field value (thread-safe)"""
        with self.lock:
            return self.value
    
    def get_display(self) -> str:
        """Get display representation with cursor (thread-safe)
        
        Returns:
            Display string with cursor indicator
        """
        with self.lock:
            if self.input_type == InputType.PASSWORD:
                display = "•" * len(self.value)
            else:
                display = self.value or self.placeholder
            
            # Add cursor
            cursor_display = (
                display[:self.cursor_pos] +
                "│" +
                display[self.cursor_pos:]
            )
            return cursor_display
    
    def validate(self) -> tuple[bool, str]:
        """Validate field value (thread-safe)
        
        Returns:
            (is_valid, error_message)
        """
        with self.lock:
            if self.required and not self.value:
                return False, f"{self.name} is required"
            
            if self.input_type == InputType.EMAIL:
                if "@" not in self.value or "." not in self.value:
                    return False, "Invalid email format"
            
            elif self.input_type == InputType.PHONE:
                if not self.value.replace("-", "").replace("(", "").replace(")", "").isdigit():
                    return False, "Invalid phone number"
            
            elif self.input_type == InputType.NUMBER:
                try:
                    float(self.value)
                except ValueError:
                    return False, "Must be a number"
            
            return True, ""
    
    def set_focus(self, focused: bool) -> None:
        """Set focus state (thread-safe)
        
        Args:
            focused: Whether field is focused
        """
        with self.lock:
            self.is_focused = focused
    
    def is_valid(self) -> bool:
        """Check if field is valid (thread-safe)"""
        is_valid, _ = self.validate()
        return is_valid


class SelectField:
    """Thread-safe dropdown/selection field"""
    
    def __init__(
        self,
        name: str,
        options: List[str],
        selected_index: int = 0,
        required: bool = False
    ) -> None:
        """Initialize select field
        
        Args:
            name: Field name
            options: List of options
            selected_index: Initially selected index
            required: Whether field is required
        """
        self.name: str = name
        self.options: List[str] = options
        self.selected_index: int = selected_index
        self.required: bool = required
        self.lock: threading.RLock = threading.RLock()
        self.is_focused: bool = False
        self.on_change: Optional[Callable] = None
    
    def next_option(self) -> None:
        """Select next option (thread-safe)"""
        with self.lock:
            if self.selected_index < len(self.options) - 1:
                self.selected_index += 1
                if self.on_change:
                    self.on_change(self.options[self.selected_index])
    
    def previous_option(self) -> None:
        """Select previous option (thread-safe)"""
        with self.lock:
            if self.selected_index > 0:
                self.selected_index -= 1
                if self.on_change:
                    self.on_change(self.options[self.selected_index])
    
    def set_option(self, index: int) -> None:
        """Set selected option (thread-safe)
        
        Args:
            index: Option index
        """
        with self.lock:
            if 0 <= index < len(self.options):
                self.selected_index = index
                if self.on_change:
                    self.on_change(self.options[self.selected_index])
    
    def get_value(self) -> str:
        """Get selected value (thread-safe)"""
        with self.lock:
            if self.selected_index < len(self.options):
                return self.options[self.selected_index]
            return ""
    
    def get_display(self) -> str:
        """Get display string (thread-safe)"""
        with self.lock:
            value = self.options[self.selected_index] if self.selected_index < len(self.options) else ""
            return f"< {value} >"
    
    def validate(self) -> tuple[bool, str]:
        """Validate selection (thread-safe)"""
        with self.lock:
            if self.required and not self.get_value():
                return False, f"{self.name} is required"
            return True, ""
    
    def set_focus(self, focused: bool) -> None:
        """Set focus state (thread-safe)"""
        with self.lock:
            self.is_focused = focused


class CheckboxField:
    """Thread-safe checkbox field"""
    
    def __init__(self, name: str, checked: bool = False) -> None:
        """Initialize checkbox
        
        Args:
            name: Field name
            checked: Initial state
        """
        self.name: str = name
        self.checked: bool = checked
        self.lock: threading.RLock = threading.RLock()
        self.on_change: Optional[Callable] = None
    
    def toggle(self) -> None:
        """Toggle checkbox (thread-safe)"""
        with self.lock:
            self.checked = not self.checked
            if self.on_change:
                self.on_change(self.checked)
    
    def set_checked(self, checked: bool) -> None:
        """Set checkbox state (thread-safe)"""
        with self.lock:
            self.checked = checked
            if self.on_change:
                self.on_change(checked)
    
    def is_checked(self) -> bool:
        """Get checkbox state (thread-safe)"""
        with self.lock:
            return self.checked
    
    def get_display(self) -> str:
        """Get display string (thread-safe)"""
        with self.lock:
            return "[✓]" if self.checked else "[ ]"


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
