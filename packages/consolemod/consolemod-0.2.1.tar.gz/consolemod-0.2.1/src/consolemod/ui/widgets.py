from typing import Optional, Callable, List
from dataclasses import dataclass
import threading


@dataclass
class Button:
    """Simple button widget"""
    label: str
    callback: Optional[Callable] = None
    
    def activate(self) -> None:
        """Activate button (call callback)"""
        if self.callback:
            self.callback()


class ProgressBar:
    """Thread-safe progress bar widget"""
    
    def __init__(self, total: int, width: int = 20) -> None:
        """Initialize progress bar
        
        Args:
            total: Total steps
            width: Width in characters
        """
        self.total: int = total
        self.width: int = width
        self.current: int = 0
        self.lock: threading.RLock = threading.RLock()
    
    def update(self, current: int) -> None:
        """Update progress (thread-safe)
        
        Args:
            current: Current progress value
        """
        with self.lock:
            self.current = min(current, self.total)
    
    def increment(self, amount: int = 1) -> None:
        """Increment progress (thread-safe)
        
        Args:
            amount: Amount to increment
        """
        with self.lock:
            self.current = min(self.current + amount, self.total)
    
    def render(self) -> str:
        """Render progress bar as string (thread-safe)
        
        Returns:
            Rendered progress bar
        """
        with self.lock:
            if self.total == 0:
                percent = 0
            else:
                percent = (self.current / self.total) * 100
            
            filled = int(self.width * self.current / max(self.total, 1))
            bar = "█" * filled + "░" * (self.width - filled)
            return f"[{bar}] {percent:.1f}% ({self.current}/{self.total})"


class Spinner:
    """Thread-safe spinning indicator"""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str = "Loading") -> None:
        """Initialize spinner
        
        Args:
            message: Message to display
        """
        self.message: str = message
        self.frame_idx: int = 0
        self.lock: threading.RLock = threading.RLock()
    
    def next_frame(self) -> str:
        """Get next frame (thread-safe)
        
        Returns:
            Next frame string with message
        """
        with self.lock:
            frame = self.FRAMES[self.frame_idx]
            self.frame_idx = (self.frame_idx + 1) % len(self.FRAMES)
            return f"{frame} {self.message}"
    
    def set_message(self, message: str) -> None:
        """Set spinner message (thread-safe)
        
        Args:
            message: New message
        """
        with self.lock:
            self.message = message


class Table:
    """Simple table widget (thread-safe)"""
    
    def __init__(self, headers: List[str]) -> None:
        """Initialize table
        
        Args:
            headers: Column headers
        """
        self.headers: List[str] = headers
        self.rows: List[List[str]] = []
        self.lock: threading.RLock = threading.RLock()
    
    def add_row(self, *values) -> None:
        """Add row to table (thread-safe)
        
        Args:
            values: Row values
        """
        with self.lock:
            self.rows.append([str(v) for v in values])
    
    def clear(self) -> None:
        """Clear all rows (thread-safe)"""
        with self.lock:
            self.rows = []
    
    def render(self) -> str:
        """Render table as string (thread-safe)
        
        Returns:
            Rendered table
        """
        with self.lock:
            if not self.headers:
                return ""
            
            # Calculate column widths
            widths = [len(h) for h in self.headers]
            for row in self.rows:
                for i, cell in enumerate(row):
                    if i < len(widths):
                        widths[i] = max(widths[i], len(cell))
            
            # Build table
            lines = []
            
            # Header
            header_cells = [h.ljust(widths[i]) for i, h in enumerate(self.headers)]
            lines.append(" | ".join(header_cells))
            lines.append("-+-".join("-" * w for w in widths))
            
            # Rows
            for row in self.rows:
                cells = [
                    (row[i] if i < len(row) else "").ljust(widths[i])
                    for i in range(len(self.headers))
                ]
                lines.append(" | ".join(cells))
            
            return "\n".join(lines)


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
