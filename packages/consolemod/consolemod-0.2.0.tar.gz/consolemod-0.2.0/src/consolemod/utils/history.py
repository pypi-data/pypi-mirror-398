import threading
from typing import List, Optional, Callable
from collections import deque


class CommandHistory:
    """Thread-safe command history with navigation"""
    
    def __init__(self, max_size: int = 100) -> None:
        """Initialize command history
        
        Args:
            max_size: Maximum number of commands to keep
        """
        self.history: deque = deque(maxlen=max_size)
        self.lock: threading.RLock = threading.RLock()
        self._current_index: Optional[int] = None
    
    def add(self, command: str) -> None:
        """Add command to history (thread-safe)
        
        Args:
            command: Command string to add
        """
        with self.lock:
            # Don't add duplicate consecutive commands
            if self.history and self.history[-1] == command:
                return
            
            self.history.append(command)
            self._current_index = None
    
    def previous(self) -> Optional[str]:
        """Get previous command (thread-safe)
        
        Returns:
            Previous command or None
        """
        with self.lock:
            if not self.history:
                return None
            
            if self._current_index is None:
                self._current_index = len(self.history) - 1
            elif self._current_index > 0:
                self._current_index -= 1
            
            return self.history[self._current_index] if self._current_index >= 0 else None
    
    def next(self) -> Optional[str]:
        """Get next command (thread-safe)
        
        Returns:
            Next command or None
        """
        with self.lock:
            if self._current_index is None:
                return None
            
            if self._current_index < len(self.history) - 1:
                self._current_index += 1
                return self.history[self._current_index]
            else:
                self._current_index = None
                return None
    
    def reset(self) -> None:
        """Reset navigation pointer (thread-safe)"""
        with self.lock:
            self._current_index = None
    
    def get_all(self) -> List[str]:
        """Get all commands (thread-safe)
        
        Returns:
            List of all commands
        """
        with self.lock:
            return list(self.history)
    
    def clear(self) -> None:
        """Clear history (thread-safe)"""
        with self.lock:
            self.history.clear()
            self._current_index = None
    
    def search(self, query: str) -> List[str]:
        """Search history for matching commands (thread-safe)
        
        Args:
            query: Search query
            
        Returns:
            List of matching commands
        """
        with self.lock:
            return [cmd for cmd in self.history if query.lower() in cmd.lower()]


class StateSnapshot:
    """Snapshot of state for undo/redo"""
    
    def __init__(self, state_data: dict, timestamp: float) -> None:
        """Initialize state snapshot
        
        Args:
            state_data: State data to store
            timestamp: Snapshot timestamp
        """
        self.state: dict = state_data.copy()
        self.timestamp: float = timestamp


class UndoRedoStack:
    """Thread-safe undo/redo stack"""
    
    def __init__(self, max_size: int = 50) -> None:
        """Initialize undo/redo stack
        
        Args:
            max_size: Maximum snapshots to keep
        """
        self.undo_stack: deque = deque(maxlen=max_size)
        self.redo_stack: deque = deque(maxlen=max_size)
        self.lock: threading.RLock = threading.RLock()
    
    def push(self, state: dict) -> None:
        """Push state snapshot (thread-safe)
        
        Args:
            state: State dict to push
        """
        import time
        with self.lock:
            self.undo_stack.append(StateSnapshot(state, time.time()))
            self.redo_stack.clear()  # Clear redo on new action
    
    def undo(self) -> Optional[dict]:
        """Undo last action (thread-safe)
        
        Returns:
            Previous state or None
        """
        with self.lock:
            if not self.undo_stack:
                return None
            
            state_snapshot = self.undo_stack.pop()
            self.redo_stack.append(state_snapshot)
            return state_snapshot.state
    
    def redo(self) -> Optional[dict]:
        """Redo last undone action (thread-safe)
        
        Returns:
            Next state or None
        """
        with self.lock:
            if not self.redo_stack:
                return None
            
            state_snapshot = self.redo_stack.pop()
            self.undo_stack.append(state_snapshot)
            return state_snapshot.state
    
    def can_undo(self) -> bool:
        """Check if undo is available (thread-safe)
        
        Returns:
            True if undo possible
        """
        with self.lock:
            return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available (thread-safe)
        
        Returns:
            True if redo possible
        """
        with self.lock:
            return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        """Clear all history (thread-safe)"""
        with self.lock:
            self.undo_stack.clear()
            self.redo_stack.clear()
    
    def get_undo_count(self) -> int:
        """Get number of undo steps available (thread-safe)"""
        with self.lock:
            return len(self.undo_stack)
    
    def get_redo_count(self) -> int:
        """Get number of redo steps available (thread-safe)"""
        with self.lock:
            return len(self.redo_stack)


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
