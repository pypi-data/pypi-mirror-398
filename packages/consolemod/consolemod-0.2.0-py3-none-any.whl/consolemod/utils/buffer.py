from typing import List, Tuple, Optional, Deque
from collections import deque
import threading


class CircularBuffer:
    """Thread-safe circular buffer with size limits and search capabilities"""
    
    def __init__(self, max_size: int = 10000) -> None:
        """Initialize circular buffer
        
        Args:
            max_size: Maximum number of items to store
        """
        self.max_size: int = max_size
        self.buffer: Deque[Tuple[str, str]] = deque(maxlen=max_size)
        self.lock: threading.RLock = threading.RLock()
        self.version: int = 0  # Bumped on each write for change detection
    
    def append(self, message: str, style: str = "white") -> None:
        """Add message to buffer (thread-safe)
        
        Args:
            message: Message text
            style: Style/color identifier
        """
        with self.lock:
            self.buffer.append((message, style))
            self.version += 1
    
    def clear(self) -> None:
        """Clear buffer (thread-safe)"""
        with self.lock:
            self.buffer.clear()
            self.version += 1
    
    def get_all(self) -> List[Tuple[str, str]]:
        """Get all messages (thread-safe)
        
        Returns:
            List of (message, style) tuples
        """
        with self.lock:
            return list(self.buffer)
    
    def get_slice(self, start: int = 0, end: Optional[int] = None) -> List[Tuple[str, str]]:
        """Get slice of buffer (thread-safe)
        
        Args:
            start: Start index
            end: End index (None = end of buffer)
            
        Returns:
            List of (message, style) tuples
        """
        with self.lock:
            return list(self.buffer)[start:end]
    
    def get_last(self, count: int) -> List[Tuple[str, str]]:
        """Get last N messages (thread-safe)
        
        Args:
            count: Number of messages to retrieve
            
        Returns:
            List of (message, style) tuples
        """
        with self.lock:
            if count <= 0:
                return []
            return list(self.buffer)[-count:]
    
    def search(self, query: str, case_sensitive: bool = False) -> List[Tuple[int, str, str]]:
        """Search for query in buffer (thread-safe)
        
        Args:
            query: Search query
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            List of (line_number, message, style) tuples
        """
        with self.lock:
            results = []
            
            for idx, (message, style) in enumerate(self.buffer):
                if case_sensitive:
                    if query in message:
                        results.append((idx, message, style))
                else:
                    if query.lower() in message.lower():
                        results.append((idx, message, style))
            
            return results
    
    def filter(self, predicate) -> List[Tuple[int, str, str]]:
        """Filter buffer with predicate function (thread-safe)
        
        Args:
            predicate: Function that returns True for matching items
            
        Returns:
            List of (line_number, message, style) tuples
        """
        with self.lock:
            results = []
            
            for idx, (message, style) in enumerate(self.buffer):
                if predicate(message, style):
                    results.append((idx, message, style))
            
            return results
    
    def __len__(self) -> int:
        """Get buffer length (thread-safe)"""
        with self.lock:
            return len(self.buffer)
    
    def get_version(self) -> int:
        """Get version number for change detection (thread-safe)
        
        Returns:
            Current version
        """
        with self.lock:
            return self.version
    
    def get_memory_usage(self) -> int:
        """Estimate memory usage in bytes (thread-safe)
        
        Returns:
            Approximate memory usage
        """
        with self.lock:
            total = 0
            for message, style in self.buffer:
                total += len(message) * 2  # Unicode
                total += len(style) * 2
            return total


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
