import threading
import time
from typing import Dict, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class FrameMetrics:
    """Frame timing metrics"""
    timestamp: float
    render_time: float  # milliseconds
    input_time: float   # milliseconds
    total_time: float   # milliseconds


class PerformanceMonitor:
    """Thread-safe performance monitoring"""
    
    def __init__(self, max_history: int = 300) -> None:
        """Initialize performance monitor
        
        Args:
            max_history: Max frames to keep in history
        """
        self.lock: threading.RLock = threading.RLock()
        self.frames: deque = deque(maxlen=max_history)
        self.pane_metrics: Dict[str, dict] = {}  # pane_id -> metrics
        self._current_frame: Optional[FrameMetrics] = None
        self._frame_start: Optional[float] = None
    
    def start_frame(self) -> None:
        """Mark start of frame (thread-safe)"""
        with self.lock:
            self._frame_start = time.time()
    
    def end_frame(self, render_time: float = 0, input_time: float = 0) -> None:
        """Mark end of frame and record metrics (thread-safe)
        
        Args:
            render_time: Time spent rendering (ms)
            input_time: Time spent on input (ms)
        """
        with self.lock:
            if self._frame_start is None:
                return
            
            total_time = (time.time() - self._frame_start) * 1000  # Convert to ms
            
            frame = FrameMetrics(
                timestamp=time.time(),
                render_time=render_time,
                input_time=input_time,
                total_time=total_time
            )
            
            self.frames.append(frame)
            self._frame_start = None
    
    def record_pane_write(self, pane_id: str, message_count: int = 1) -> None:
        """Record pane write event (thread-safe)
        
        Args:
            pane_id: Pane ID
            message_count: Number of messages written
        """
        with self.lock:
            if pane_id not in self.pane_metrics:
                self.pane_metrics[pane_id] = {
                    "writes": 0,
                    "messages": 0,
                    "last_write": 0
                }
            
            self.pane_metrics[pane_id]["writes"] += 1
            self.pane_metrics[pane_id]["messages"] += message_count
            self.pane_metrics[pane_id]["last_write"] = time.time()
    
    def get_fps(self) -> float:
        """Get current FPS (thread-safe)
        
        Returns:
            Frames per second
        """
        with self.lock:
            if len(self.frames) < 2:
                return 0
            
            time_span = self.frames[-1].timestamp - self.frames[0].timestamp
            if time_span <= 0:
                return 0
            
            return len(self.frames) / time_span
    
    def get_avg_frame_time(self) -> float:
        """Get average frame time (thread-safe)
        
        Returns:
            Average frame time in milliseconds
        """
        with self.lock:
            if not self.frames:
                return 0
            
            total = sum(f.total_time for f in self.frames)
            return total / len(self.frames)
    
    def get_max_frame_time(self) -> float:
        """Get max frame time (thread-safe)
        
        Returns:
            Maximum frame time in milliseconds
        """
        with self.lock:
            if not self.frames:
                return 0
            
            return max(f.total_time for f in self.frames)
    
    def get_pane_stats(self, pane_id: str) -> Optional[Dict]:
        """Get pane statistics (thread-safe)
        
        Args:
            pane_id: Pane ID
            
        Returns:
            Stats dict or None if pane not found
        """
        with self.lock:
            return self.pane_metrics.get(pane_id, {}).copy()
    
    def reset(self) -> None:
        """Reset metrics (thread-safe)"""
        with self.lock:
            self.frames.clear()
            self.pane_metrics.clear()
            self._frame_start = None


class MemoryMonitor:
    """Thread-safe memory usage monitoring"""
    
    def __init__(self) -> None:
        """Initialize memory monitor"""
        self.lock: threading.RLock = threading.RLock()
        self.pane_memory: Dict[str, int] = {}
        self.total_memory: int = 0
    
    def record_pane_memory(self, pane_id: str, bytes_used: int) -> None:
        """Record pane memory usage (thread-safe)
        
        Args:
            pane_id: Pane ID
            bytes_used: Bytes used by pane
        """
        with self.lock:
            old_value = self.pane_memory.get(pane_id, 0)
            self.pane_memory[pane_id] = bytes_used
            
            # Update total
            self.total_memory = sum(self.pane_memory.values())
    
    def get_pane_memory(self, pane_id: str) -> int:
        """Get pane memory usage (thread-safe)
        
        Args:
            pane_id: Pane ID
            
        Returns:
            Bytes used
        """
        with self.lock:
            return self.pane_memory.get(pane_id, 0)
    
    def get_total_memory(self) -> int:
        """Get total memory usage (thread-safe)
        
        Returns:
            Total bytes used
        """
        with self.lock:
            return self.total_memory
    
    def get_pane_breakdown(self) -> Dict[str, int]:
        """Get memory breakdown by pane (thread-safe)
        
        Returns:
            Dict of pane_id -> bytes
        """
        with self.lock:
            return self.pane_memory.copy()
    
    def reset(self) -> None:
        """Reset metrics (thread-safe)"""
        with self.lock:
            self.pane_memory.clear()
            self.total_memory = 0


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
