import asyncio
import threading
from typing import Callable, Optional, Any
from functools import wraps


class Debouncer:
    """Thread-safe debouncer for async functions"""
    
    def __init__(self, delay: float = 0.1) -> None:
        """Initialize debouncer
        
        Args:
            delay: Debounce delay in seconds
        """
        self.delay: float = delay
        self.lock: threading.RLock = threading.RLock()
        self._pending_task: Optional[asyncio.Task] = None
    
    async def debounce(self, func: Callable, *args, **kwargs) -> Any:
        """Debounce function call (thread-safe)
        
        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        with self.lock:
            # Cancel previous task if pending
            if self._pending_task and not self._pending_task.done():
                self._pending_task.cancel()
            
            # Create new task
            async def delayed():
                await asyncio.sleep(self.delay)
                return await func(*args, **kwargs)
            
            self._pending_task = asyncio.create_task(delayed())
        
        try:
            return await self._pending_task
        except asyncio.CancelledError:
            return None


class Throttler:
    """Thread-safe throttler for rate limiting"""
    
    def __init__(self, min_interval: float = 0.1) -> None:
        """Initialize throttler
        
        Args:
            min_interval: Minimum interval between calls in seconds
        """
        self.min_interval: float = min_interval
        self.lock: threading.RLock = threading.RLock()
        self._last_call: float = 0
    
    async def throttle(self, func: Callable, *args, **kwargs) -> Any:
        """Throttle function call (thread-safe)
        
        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result if called, None if throttled
        """
        import time
        
        with self.lock:
            now = time.time()
            time_since_last = now - self._last_call
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)
                self._last_call = time.time()
            else:
                self._last_call = now
        
        return await func(*args, **kwargs)
    
    def reset(self) -> None:
        """Reset throttle timer (thread-safe)"""
        with self.lock:
            self._last_call = 0


def debounced(delay: float = 0.1) -> Callable:
    """Decorator for debouncing async functions
    
    Args:
        delay: Debounce delay in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        debouncer = Debouncer(delay)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await debouncer.debounce(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


def throttled(min_interval: float = 0.1) -> Callable:
    """Decorator for throttling async functions
    
    Args:
        min_interval: Minimum interval between calls in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        throttler = Throttler(min_interval)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await throttler.throttle(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
