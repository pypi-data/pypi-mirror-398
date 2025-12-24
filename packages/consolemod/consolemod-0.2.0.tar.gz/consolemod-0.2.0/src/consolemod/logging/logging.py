import asyncio
import logging
from enum import Enum
from typing import Optional, Union
from datetime import datetime


class LogLevel(Enum):
    """Log levels with colors"""
    DEBUG = ("DEBUG", "blue")
    INFO = ("INFO", "green")
    WARNING = ("WARNING", "yellow")
    ERROR = ("ERROR", "red")
    CRITICAL = ("CRITICAL", "bright_red")


class PaneLogger:
    """Logger that writes to a Pane (thread-safe)"""
    
    def __init__(self, pane, include_timestamp: bool = True) -> None:
        """Initialize pane logger
        
        Args:
            pane: Pane instance to write to
            include_timestamp: Whether to include timestamps
        """
        self.pane = pane
        self.include_timestamp = include_timestamp
    
    def _format_message(self, message: str, level: LogLevel) -> str:
        """Format message with timestamp and level
        
        Args:
            message: Message text
            level: Log level
            
        Returns:
            Formatted message
        """
        prefix = f"[{level.value[0]}]"
        
        if self.include_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = f"[{timestamp}] {prefix}"
        
        return f"{prefix} {message}"
    
    def debug(self, message: str) -> None:
        """Write debug message (synchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.DEBUG)
        self.pane.write(formatted, LogLevel.DEBUG.value[1])
    
    async def adebug(self, message: str) -> None:
        """Write debug message (asynchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.DEBUG)
        await self.pane.awrite(formatted, LogLevel.DEBUG.value[1])
    
    def info(self, message: str) -> None:
        """Write info message (synchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.INFO)
        self.pane.write(formatted, LogLevel.INFO.value[1])
    
    async def ainfo(self, message: str) -> None:
        """Write info message (asynchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.INFO)
        await self.pane.awrite(formatted, LogLevel.INFO.value[1])
    
    def warning(self, message: str) -> None:
        """Write warning message (synchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.WARNING)
        self.pane.write(formatted, LogLevel.WARNING.value[1])
    
    async def awarning(self, message: str) -> None:
        """Write warning message (asynchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.WARNING)
        await self.pane.awrite(formatted, LogLevel.WARNING.value[1])
    
    def error(self, message: str) -> None:
        """Write error message (synchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.ERROR)
        self.pane.write(formatted, LogLevel.ERROR.value[1])
    
    async def aerror(self, message: str) -> None:
        """Write error message (asynchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.ERROR)
        await self.pane.awrite(formatted, LogLevel.ERROR.value[1])
    
    def critical(self, message: str) -> None:
        """Write critical message (synchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.CRITICAL)
        self.pane.write(formatted, LogLevel.CRITICAL.value[1])
    
    async def acritical(self, message: str) -> None:
        """Write critical message (asynchronous)
        
        Args:
            message: Message text
        """
        formatted = self._format_message(message, LogLevel.CRITICAL)
        await self.pane.awrite(formatted, LogLevel.CRITICAL.value[1])
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Write message at specified level (synchronous)
        
        Args:
            message: Message text
            level: Log level
        """
        formatted = self._format_message(message, level)
        self.pane.write(formatted, level.value[1])
    
    async def alog(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Write message at specified level (asynchronous)
        
        Args:
            message: Message text
            level: Log level
        """
        formatted = self._format_message(message, level)
        await self.pane.awrite(formatted, level.value[1])


class StdoutPaneAdapter(logging.Handler):
    """Adapt Python logging to write to a Pane
    
    Usage:
        logger = logging.getLogger(__name__)
        handler = StdoutPaneAdapter(pane)
        logger.addHandler(handler)
    """
    
    def __init__(self, pane) -> None:
        """Initialize adapter
        
        Args:
            pane: Pane instance to write to
        """
        super().__init__()
        self.pane = pane
        self.pane_logger = PaneLogger(pane, include_timestamp=False)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record to pane
        
        Args:
            record: LogRecord to emit
        """
        try:
            msg = self.format(record)
            
            # Map Python log level to LogLevel
            level_map = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL,
            }
            
            log_level = level_map.get(record.levelno, LogLevel.INFO)
            self.pane_logger.log(msg, log_level)
        except Exception:
            self.handleError(record)


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
