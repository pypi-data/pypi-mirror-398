"""Menu and selection systems"""
import threading
from typing import List, Optional, Callable, Dict, Any
from enum import Enum


class MenuItem:
    """Single menu item"""
    
    def __init__(self, label: str, callback: Optional[Callable] = None, data: Any = None) -> None:
        """Initialize menu item
        
        Args:
            label: Display label
            callback: Function to call on selection
            data: Associated data
        """
        self.label: str = label
        self.callback: Optional[Callable] = callback
        self.data: Any = data
    
    def activate(self) -> None:
        """Activate menu item"""
        if self.callback:
            self.callback()


class Menu:
    """Thread-safe menu system"""
    
    def __init__(self, title: str = "Menu") -> None:
        """Initialize menu
        
        Args:
            title: Menu title
        """
        self.title: str = title
        self.items: List[MenuItem] = []
        self.selected_index: int = 0
        self.lock: threading.RLock = threading.RLock()
        self.on_select: Optional[Callable] = None
    
    def add_item(self, label: str, callback: Optional[Callable] = None, data: Any = None) -> MenuItem:
        """Add menu item (thread-safe)
        
        Args:
            label: Item label
            callback: Selection callback
            data: Associated data
            
        Returns:
            Created MenuItem
        """
        with self.lock:
            item = MenuItem(label, callback, data)
            self.items.append(item)
            return item
    
    def next_item(self) -> None:
        """Select next item (thread-safe)"""
        with self.lock:
            if self.items:
                self.selected_index = (self.selected_index + 1) % len(self.items)
                if self.on_select:
                    self.on_select(self.get_selected_item())
    
    def previous_item(self) -> None:
        """Select previous item (thread-safe)"""
        with self.lock:
            if self.items:
                self.selected_index = (self.selected_index - 1) % len(self.items)
                if self.on_select:
                    self.on_select(self.get_selected_item())
    
    def select_item(self, index: int) -> None:
        """Select item by index (thread-safe)
        
        Args:
            index: Item index
        """
        with self.lock:
            if 0 <= index < len(self.items):
                self.selected_index = index
                if self.on_select:
                    self.on_select(self.get_selected_item())
    
    def activate_selected(self) -> None:
        """Activate selected item (thread-safe)"""
        with self.lock:
            if self.items and 0 <= self.selected_index < len(self.items):
                self.items[self.selected_index].activate()
    
    def get_selected_item(self) -> Optional[MenuItem]:
        """Get selected item (thread-safe)"""
        with self.lock:
            if self.items and 0 <= self.selected_index < len(self.items):
                return self.items[self.selected_index]
            return None
    
    def get_selected_index(self) -> int:
        """Get selected index (thread-safe)"""
        with self.lock:
            return self.selected_index
    
    def get_display(self) -> str:
        """Get menu display (thread-safe)"""
        with self.lock:
            lines = [f"═══ {self.title} ═══"]
            
            for i, item in enumerate(self.items):
                marker = "►" if i == self.selected_index else " "
                lines.append(f"{marker} {item.label}")
            
            return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear all items (thread-safe)"""
        with self.lock:
            self.items = []
            self.selected_index = 0


class SelectionList:
    """Thread-safe list with multiple selection support"""
    
    def __init__(self, title: str = "Select Items") -> None:
        """Initialize selection list
        
        Args:
            title: List title
        """
        self.title: str = title
        self.items: List[str] = []
        self.selected_indices: set = set()
        self.current_index: int = 0
        self.lock: threading.RLock = threading.RLock()
    
    def add_item(self, label: str) -> None:
        """Add item to list (thread-safe)
        
        Args:
            label: Item label
        """
        with self.lock:
            self.items.append(label)
    
    def add_items(self, labels: List[str]) -> None:
        """Add multiple items (thread-safe)
        
        Args:
            labels: List of labels
        """
        with self.lock:
            self.items.extend(labels)
    
    def toggle_selection(self, index: int) -> None:
        """Toggle item selection (thread-safe)
        
        Args:
            index: Item index
        """
        with self.lock:
            if 0 <= index < len(self.items):
                if index in self.selected_indices:
                    self.selected_indices.remove(index)
                else:
                    self.selected_indices.add(index)
    
    def next_item(self) -> None:
        """Move to next item (thread-safe)"""
        with self.lock:
            if self.items:
                self.current_index = (self.current_index + 1) % len(self.items)
    
    def previous_item(self) -> None:
        """Move to previous item (thread-safe)"""
        with self.lock:
            if self.items:
                self.current_index = (self.current_index - 1) % len(self.items)
    
    def get_selected(self) -> List[str]:
        """Get selected items (thread-safe)
        
        Returns:
            List of selected labels
        """
        with self.lock:
            return [self.items[i] for i in sorted(self.selected_indices) if i < len(self.items)]
    
    def get_current_item(self) -> Optional[str]:
        """Get current item (thread-safe)"""
        with self.lock:
            if 0 <= self.current_index < len(self.items):
                return self.items[self.current_index]
            return None
    
    def get_display(self) -> str:
        """Get list display (thread-safe)"""
        with self.lock:
            lines = [f"═══ {self.title} ═══"]
            
            for i, item in enumerate(self.items):
                marker = "✓" if i in self.selected_indices else " "
                current = "►" if i == self.current_index else " "
                lines.append(f"{current}[{marker}] {item}")
            
            return "\n".join(lines)


class ContextMenu:
    """Thread-safe context menu with key bindings"""
    
    def __init__(self, title: str = "Context Menu") -> None:
        """Initialize context menu
        
        Args:
            title: Menu title
        """
        self.title: str = title
        self.items: Dict[str, Callable] = {}  # key -> callback
        self.lock: threading.RLock = threading.RLock()
    
    def add_action(self, key: str, label: str, callback: Callable) -> None:
        """Add menu action (thread-safe)
        
        Args:
            key: Key/shortcut
            label: Display label
            callback: Action callback
        """
        with self.lock:
            self.items[key] = (label, callback)
    
    def activate(self, key: str) -> bool:
        """Activate action by key (thread-safe)
        
        Args:
            key: Action key
            
        Returns:
            True if activated
        """
        with self.lock:
            if key in self.items:
                _, callback = self.items[key]
                callback()
                return True
            return False
    
    def get_display(self) -> str:
        """Get context menu display (thread-safe)"""
        with self.lock:
            lines = []
            
            for key, (label, _) in self.items.items():
                lines.append(f"[{key}] {label}")
            
            return "  ".join(lines)


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
