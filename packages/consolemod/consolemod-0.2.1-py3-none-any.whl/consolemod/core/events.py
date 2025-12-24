from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional, List
import asyncio
import threading

class KeyCode(Enum):
    """Key codes for keyboard events"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    ENTER = "enter"
    ESC = "escape"
    TAB = "tab"
    SHIFT_TAB = "shift+tab"
    CTRL_C = "ctrl+c"
    CTRL_D = "ctrl+d"
    BACKSPACE = "backspace"
    DELETE = "delete"
    HOME = "home"
    END = "end"
    PAGE_UP = "pageup"
    PAGE_DOWN = "pagedown"

@dataclass
class KeyEvent:
    """Keyboard event"""
    key: KeyCode
    raw: Optional[str] = None

@dataclass
class FocusEvent:
    """Focus change event"""
    pane_id: str
    focused: bool

class EventBus:
    """Thread-safe event bus for UI events"""
    
    def __init__(self) -> None:
        self.key_handlers: List[Callable] = []
        self.focus_handlers: List[Callable] = []
        self.lock: threading.RLock = threading.RLock()
    
    def on_key(self, handler: Callable) -> Callable:
        """Register key event handler (thread-safe)
        
        Args:
            handler: Callback function (sync or async)
            
        Returns:
            The handler function
        """
        with self.lock:
            self.key_handlers.append(handler)
        return handler
    
    def off_key(self, handler: Callable) -> None:
        """Unregister key event handler (thread-safe)
        
        Args:
            handler: Handler to remove
        """
        with self.lock:
            if handler in self.key_handlers:
                self.key_handlers.remove(handler)
    
    def on_focus(self, handler: Callable) -> Callable:
        """Register focus event handler (thread-safe)
        
        Args:
            handler: Callback function (sync or async)
            
        Returns:
            The handler function
        """
        with self.lock:
            self.focus_handlers.append(handler)
        return handler
    
    def off_focus(self, handler: Callable) -> None:
        """Unregister focus event handler (thread-safe)
        
        Args:
            handler: Handler to remove
        """
        with self.lock:
            if handler in self.focus_handlers:
                self.focus_handlers.remove(handler)
    
    async def emit_key(self, event: KeyEvent) -> None:
        """Emit key event to all handlers (thread-safe)
        
        Args:
            event: KeyEvent to emit
        """
        with self.lock:
            handlers = self.key_handlers.copy()
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    await asyncio.to_thread(handler, event)
            except Exception:
                pass  # Silently ignore handler errors
    
    async def emit_focus(self, event: FocusEvent) -> None:
        """Emit focus event to all handlers (thread-safe)
        
        Args:
            event: FocusEvent to emit
        """
        with self.lock:
            handlers = self.focus_handlers.copy()
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    await asyncio.to_thread(handler, event)
            except Exception:
                pass  # Silently ignore handler errors

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
