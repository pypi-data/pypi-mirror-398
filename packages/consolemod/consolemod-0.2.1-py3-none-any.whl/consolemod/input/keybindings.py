"""Keyboard shortcuts and keybindings"""
import threading
from typing import Callable, Dict, Optional, List
from ..core.events import KeyCode, KeyEvent


class KeyBinding:
    """Single key binding"""
    
    def __init__(self, key: KeyCode, callback: Callable, description: str = "") -> None:
        """Initialize keybinding
        
        Args:
            key: Key to bind
            callback: Function to call
            description: Human-readable description
        """
        self.key: KeyCode = key
        self.callback: Callable = callback
        self.description: str = description
    
    async def trigger(self) -> None:
        """Trigger keybinding"""
        if callable(self.callback):
            if hasattr(self.callback, '__await__'):
                await self.callback()
            else:
                self.callback()


class KeyBindingManager:
    """Thread-safe keyboard shortcut manager"""
    
    def __init__(self) -> None:
        """Initialize keybinding manager"""
        self.bindings: Dict[KeyCode, List[KeyBinding]] = {}
        self.lock: threading.RLock = threading.RLock()
        self.global_bindings: Dict[KeyCode, KeyBinding] = {}
    
    def bind(self, key: KeyCode, callback: Callable, description: str = "") -> KeyBinding:
        """Register key binding (thread-safe)
        
        Args:
            key: Key to bind
            callback: Function to call
            description: Binding description
            
        Returns:
            KeyBinding instance
        """
        with self.lock:
            binding = KeyBinding(key, callback, description)
            
            if key not in self.bindings:
                self.bindings[key] = []
            
            self.bindings[key].append(binding)
            return binding
    
    def bind_global(self, key: KeyCode, callback: Callable, description: str = "") -> KeyBinding:
        """Register global key binding (thread-safe)
        
        Args:
            key: Key to bind globally
            callback: Function to call
            description: Binding description
            
        Returns:
            KeyBinding instance
        """
        with self.lock:
            binding = KeyBinding(key, callback, description)
            self.global_bindings[key] = binding
            return binding
    
    def unbind(self, key: KeyCode) -> None:
        """Unbind key (thread-safe)
        
        Args:
            key: Key to unbind
        """
        with self.lock:
            if key in self.bindings:
                del self.bindings[key]
            if key in self.global_bindings:
                del self.global_bindings[key]
    
    async def trigger(self, key_event: KeyEvent) -> bool:
        """Trigger key bindings (thread-safe)
        
        Args:
            key_event: Key event
            
        Returns:
            True if binding was triggered
        """
        with self.lock:
            key = key_event.key
            
            # Check global bindings first
            if key in self.global_bindings:
                await self.global_bindings[key].trigger()
                return True
            
            # Check context bindings
            if key in self.bindings:
                for binding in self.bindings[key]:
                    await binding.trigger()
                return True
        
        return False
    
    def get_bindings(self) -> Dict[KeyCode, List[str]]:
        """Get all bindings for display (thread-safe)
        
        Returns:
            Dict of key -> descriptions
        """
        with self.lock:
            result = {}
            
            for key, bindings_list in self.bindings.items():
                if bindings_list:
                    result[key] = [b.description for b in bindings_list if b.description]
            
            return result
    
    def clear(self) -> None:
        """Clear all bindings (thread-safe)"""
        with self.lock:
            self.bindings.clear()
            self.global_bindings.clear()


class KeyBindingPreset:
    """Pre-configured keybinding presets"""
    
    # Standard VI keybindings
    VI_PRESET = {
        "up": "k",
        "down": "j",
        "left": "h",
        "right": "l",
        "next": "n",
        "prev": "N",
        "select": " ",
        "submit": ":",
        "cancel": "q",
    }
    
    # Standard Emacs keybindings
    EMACS_PRESET = {
        "up": "Ctrl+P",
        "down": "Ctrl+N",
        "left": "Ctrl+B",
        "right": "Ctrl+F",
        "next": "Ctrl+D",
        "prev": "Ctrl+U",
        "select": "Enter",
        "submit": "Ctrl+X Ctrl+S",
        "cancel": "Ctrl+C",
    }
    
    # Standard arrow keys
    ARROW_PRESET = {
        "up": "↑",
        "down": "↓",
        "left": "←",
        "right": "→",
        "next": "Tab",
        "prev": "Shift+Tab",
        "select": "Enter",
        "submit": "Enter",
        "cancel": "Esc",
    }
    
    @staticmethod
    def get_preset(name: str) -> Dict[str, str]:
        """Get keybinding preset
        
        Args:
            name: Preset name (vi, emacs, arrow)
            
        Returns:
            Dict of action -> key mapping
        """
        presets = {
            "vi": KeyBindingPreset.VI_PRESET,
            "emacs": KeyBindingPreset.EMACS_PRESET,
            "arrow": KeyBindingPreset.ARROW_PRESET,
        }
        
        return presets.get(name, KeyBindingPreset.ARROW_PRESET)


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
