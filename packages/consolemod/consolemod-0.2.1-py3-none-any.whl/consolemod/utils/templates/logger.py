"""Logger template - auto-configured logging UI"""
from typing import Optional, Callable, Any
from functools import wraps
import asyncio
from ...core import TerminalSplitter, Pane
from ...logging import PaneLogger


class LoggerTemplate:
    """Pre-configured logger UI with automatic setup"""
    
    def __init__(self, name: str = "logger", fps: int = 30, theme: str = "dark") -> None:
        """Initialize logger template
        
        Args:
            name: Name for the window/pane
            fps: Frames per second
            theme: Theme name
        """
        self.name: str = name
        self.splitter: TerminalSplitter = TerminalSplitter(fps=fps, theme=theme)
        
        # Create panes
        self.logs_pane: Pane = Pane("logs", color="green", theme_name=theme)
        self.errors_pane: Pane = Pane("errors", color="red", theme_name=theme)
        self.warnings_pane: Pane = Pane("warnings", color="yellow", theme_name=theme)
        
        self.splitter.add_pane(self.logs_pane)
        self.splitter.add_pane(self.errors_pane)
        self.splitter.add_pane(self.warnings_pane)
        
        # Create loggers
        self.logs: PaneLogger = PaneLogger(self.logs_pane, include_timestamp=True)
        self.errors: PaneLogger = PaneLogger(self.errors_pane, include_timestamp=True)
        self.warnings: PaneLogger = PaneLogger(self.warnings_pane, include_timestamp=True)
    
    def log(self, message: str) -> None:
        """Log info message
        
        Args:
            message: Message to log
        """
        self.logs.info(message)
    
    async def alog(self, message: str) -> None:
        """Async log info message"""
        await self.logs.ainfo(message)
    
    def error(self, message: str) -> None:
        """Log error message
        
        Args:
            message: Error message
        """
        self.errors.error(message)
    
    async def aerror(self, message: str) -> None:
        """Async log error message"""
        await self.errors.aerror(message)
    
    def warning(self, message: str) -> None:
        """Log warning message
        
        Args:
            message: Warning message
        """
        self.warnings.warning(message)
    
    async def awarning(self, message: str) -> None:
        """Async log warning message"""
        await self.warnings.awarning(message)
    
    def debug(self, message: str) -> None:
        """Log debug message
        
        Args:
            message: Debug message
        """
        self.logs.debug(message)
    
    async def adebug(self, message: str) -> None:
        """Async log debug message"""
        await self.logs.adebug(message)
    
    async def render(self) -> None:
        """Start rendering UI"""
        await self.splitter.render_loop()
    
    def function(self, level: str = "info") -> Callable:
        """Decorator to auto-log function calls
        
        Args:
            level: Log level (debug, info, warning, error)
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                self.log(f"→ Calling {func.__name__}")
                try:
                    result = await func(*args, **kwargs)
                    self.log(f"✓ {func.__name__} completed")
                    return result
                except Exception as e:
                    self.error(f"✗ {func.__name__} failed: {e}")
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                self.log(f"→ Calling {func.__name__}")
                try:
                    result = func(*args, **kwargs)
                    self.log(f"✓ {func.__name__} completed")
                    return result
                except Exception as e:
                    self.error(f"✗ {func.__name__} failed: {e}")
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
