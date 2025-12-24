import threading
import asyncio
from typing import Optional, List, Tuple, Callable
from ..ui.themes import Theme, get_theme
from ..utils.buffer import CircularBuffer

class Pane:
    """Thread-safe pane for displaying content with circular buffer"""
    
    def __init__(
        self,
        id: str,
        width: float = 0.5,
        height: float = 0.5,
        color: str = "white",
        border: bool = True,
        theme_name: str = "dark",
        max_lines: int = 1000
    ) -> None:
        self.id: str = id
        self.width: float = width
        self.height: float = height
        self.color: str = color
        self.border: bool = border
        self.lock: threading.RLock = threading.RLock()
        self.theme: Theme = get_theme(theme_name)
        self.buffer: CircularBuffer = CircularBuffer(max_size=max_lines)
        self.focused: bool = False
        self.scrollback: int = 0  # Current scroll position
        self.last_rendered_version: int = 0  # Track changes for optimization
        self.on_write_callback: Optional[Callable] = None  # Optional callback
    
    def write(self, message: str, style: Optional[str] = None) -> None:
        """Synchronous write to pane (thread-safe)"""
        with self.lock:
            self.buffer.append(message, style or self.color)
            if self.on_write_callback:
                self.on_write_callback(message, style or self.color)
    
    async def awrite(self, message: str, style: Optional[str] = None) -> None:
        """Asynchronous write to pane (thread-safe)"""
        await asyncio.to_thread(self.write, message, style)
    
    def write_many(self, messages: List[Tuple[str, str]]) -> None:
        """Write multiple messages efficiently (thread-safe)
        
        Args:
            messages: List of (message, style) tuples
        """
        with self.lock:
            for message, style in messages:
                self.buffer.append(message, style)
                if self.on_write_callback:
                    self.on_write_callback(message, style)
    
    async def awrite_many(self, messages: List[Tuple[str, str]]) -> None:
        """Asynchronous write multiple messages (thread-safe)"""
        await asyncio.to_thread(self.write_many, messages)
    
    def clear(self) -> None:
        """Clear pane content (thread-safe)"""
        with self.lock:
            self.buffer.clear()
            self.scrollback = 0
            self.last_rendered_version = 0
    
    async def aclear(self) -> None:
        """Asynchronous clear (thread-safe)"""
        await asyncio.to_thread(self.clear)
    
    def set_focus(self, focused: bool) -> None:
        """Set focus state (thread-safe)"""
        with self.lock:
            self.focused = focused
    
    async def aset_focus(self, focused: bool) -> None:
        """Asynchronous set focus (thread-safe)"""
        await asyncio.to_thread(self.set_focus, focused)
    
    def scroll(self, direction: int, amount: int = 1) -> None:
        """Scroll pane content (thread-safe)
        
        Args:
            direction: -1 for up, +1 for down
            amount: Number of lines to scroll
        """
        with self.lock:
            buffer_len = len(self.buffer)
            self.scrollback = max(0, min(self.scrollback + (direction * amount), buffer_len))
    
    async def ascroll(self, direction: int, amount: int = 1) -> None:
        """Asynchronous scroll (thread-safe)"""
        await asyncio.to_thread(self.scroll, direction, amount)
    
    def get_visible_content(self, height: int) -> List[Tuple[str, str]]:
        """Get visible content based on scroll position (thread-safe)"""
        with self.lock:
            buffer_len = len(self.buffer)
            start = max(0, buffer_len - height - self.scrollback)
            end = max(0, buffer_len - self.scrollback)
            return self.buffer.get_slice(start, end) if start < buffer_len else []
    
    async def aget_visible_content(self, height: int) -> List[Tuple[str, str]]:
        """Asynchronous get visible content (thread-safe)"""
        return await asyncio.to_thread(self.get_visible_content, height)
    
    def get_content_snapshot(self) -> List[Tuple[str, str]]:
        """Get entire content snapshot (thread-safe)"""
        with self.lock:
            return self.buffer.get_all()
    
    async def aget_content_snapshot(self) -> List[Tuple[str, str]]:
        """Asynchronous get content snapshot (thread-safe)"""
        return await asyncio.to_thread(self.get_content_snapshot)
    
    def search(self, query: str, case_sensitive: bool = False) -> List[Tuple[int, str, str]]:
        """Search for text in pane content (thread-safe)
        
        Args:
            query: Search query
            case_sensitive: Whether to match case
            
        Returns:
            List of (line_number, message, style) tuples
        """
        with self.lock:
            return self.buffer.search(query, case_sensitive)
    
    async def asearch(self, query: str, case_sensitive: bool = False) -> List[Tuple[int, str, str]]:
        """Asynchronous search (thread-safe)"""
        return await asyncio.to_thread(self.search, query, case_sensitive)
    
    def filter_content(self, predicate: Callable) -> List[Tuple[int, str, str]]:
        """Filter content with predicate (thread-safe)
        
        Args:
            predicate: Function that takes (message, style) and returns bool
            
        Returns:
            List of (line_number, message, style) tuples
        """
        with self.lock:
            return self.buffer.filter(predicate)
    
    async def afilter_content(self, predicate: Callable) -> List[Tuple[int, str, str]]:
        """Asynchronous filter (thread-safe)"""
        return await asyncio.to_thread(self.filter_content, predicate)
    
    def set_write_callback(self, callback: Optional[Callable]) -> None:
        """Set callback for write events (thread-safe)
        
        Args:
            callback: Function called on each write with (message, style)
        """
        with self.lock:
            self.on_write_callback = callback
    
    def has_changes(self) -> bool:
        """Check if content changed since last render (thread-safe)
        
        Returns:
            True if buffer was updated
        """
        with self.lock:
            current_version = self.buffer.get_version()
            return current_version != self.last_rendered_version
    
    def mark_rendered(self) -> None:
        """Mark content as rendered (for change detection) (thread-safe)"""
        with self.lock:
            self.last_rendered_version = self.buffer.get_version()
    
    def get_memory_usage(self) -> int:
        """Get estimated memory usage (thread-safe)
        
        Returns:
            Approximate bytes used
        """
        with self.lock:
            return self.buffer.get_memory_usage()

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")