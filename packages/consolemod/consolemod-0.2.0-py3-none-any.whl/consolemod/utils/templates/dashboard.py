"""Dashboard template - multi-pane status display"""
from typing import Optional, Dict, Any
from ...core import TerminalSplitter, Pane
from ...logging import PaneLogger
from ...ui import Table, ProgressBar


class DashboardTemplate:
    """Pre-configured dashboard UI with multiple status sections"""
    
    def __init__(self, title: str = "Dashboard", fps: int = 30, theme: str = "dark") -> None:
        """Initialize dashboard template
        
        Args:
            title: Dashboard title
            fps: Frames per second
            theme: Theme name
        """
        self.title: str = title
        self.splitter: TerminalSplitter = TerminalSplitter(
            fps=fps,
            theme=theme,
            enable_metrics=True
        )
        
        # Create panes
        self.header_pane: Pane = Pane("header", color="cyan", theme_name=theme)
        self.status_pane: Pane = Pane("status", color="green", theme_name=theme)
        self.data_pane: Pane = Pane("data", color="white", theme_name=theme)
        self.logs_pane: Pane = Pane("logs", color="yellow", theme_name=theme)
        self.footer_pane: Pane = Pane("footer", color="blue", theme_name=theme)
        
        self.splitter.add_pane(self.header_pane)
        self.splitter.add_pane(self.status_pane)
        self.splitter.add_pane(self.data_pane)
        self.splitter.add_pane(self.logs_pane)
        self.splitter.add_pane(self.footer_pane)
        
        # Set pane weights
        self.splitter.set_pane_weight("header", 0.3)
        self.splitter.set_pane_weight("status", 0.8)
        self.splitter.set_pane_weight("data", 1.5)
        self.splitter.set_pane_weight("logs", 1.0)
        self.splitter.set_pane_weight("footer", 0.3)
        
        # Create loggers
        self.header_logger: PaneLogger = PaneLogger(self.header_pane, include_timestamp=False)
        self.status_logger: PaneLogger = PaneLogger(self.status_pane, include_timestamp=True)
        self.logs_logger: PaneLogger = PaneLogger(self.logs_pane, include_timestamp=True)
        self.footer_logger: PaneLogger = PaneLogger(self.footer_pane, include_timestamp=False)
        
        # Data storage
        self.status_items: Dict[str, Any] = {}
        self.data_table: Optional[Table] = None
    
    def set_header(self, text: str) -> None:
        """Set header text
        
        Args:
            text: Header text
        """
        self.header_pane.clear()
        self.header_pane.write(f"═══ {self.title}: {text} ═══", "cyan")
    
    async def aset_header(self, text: str) -> None:
        """Async set header"""
        await self.header_pane.aclear()
        await self.header_pane.awrite(f"═══ {self.title}: {text} ═══", "cyan")
    
    def set_status(self, key: str, value: str, color: str = "green") -> None:
        """Set status item
        
        Args:
            key: Status key
            value: Status value
            color: Display color
        """
        self.status_items[key] = value
        self.status_pane.clear()
        
        for k, v in self.status_items.items():
            self.status_pane.write(f"{k}: {v}", color)
    
    async def aset_status(self, key: str, value: str, color: str = "green") -> None:
        """Async set status"""
        await self.status_pane.aclear()
        self.status_items[key] = value
        
        for k, v in self.status_items.items():
            await self.status_pane.awrite(f"{k}: {v}", color)
    
    def set_data_table(self, headers: list, rows: list) -> None:
        """Set data table
        
        Args:
            headers: Table headers
            rows: Table rows (list of lists)
        """
        self.data_table = Table(headers)
        for row in rows:
            self.data_table.add_row(*row)
        
        self.data_pane.clear()
        self.data_pane.write(self.data_table.render())
    
    async def aset_data_table(self, headers: list, rows: list) -> None:
        """Async set data table"""
        self.data_table = Table(headers)
        for row in rows:
            self.data_table.add_row(*row)
        
        await self.data_pane.aclear()
        await self.data_pane.awrite(self.data_table.render())
    
    def log(self, message: str, level: str = "info") -> None:
        """Log message
        
        Args:
            message: Log message
            level: Log level
        """
        if level == "info":
            self.logs_logger.info(message)
        elif level == "error":
            self.logs_logger.error(message)
        elif level == "warning":
            self.logs_logger.warning(message)
        elif level == "debug":
            self.logs_logger.debug(message)
    
    async def alog(self, message: str, level: str = "info") -> None:
        """Async log message"""
        if level == "info":
            await self.logs_logger.ainfo(message)
        elif level == "error":
            await self.logs_logger.aerror(message)
        elif level == "warning":
            await self.logs_logger.awarning(message)
        elif level == "debug":
            await self.logs_logger.adebug(message)
    
    def set_footer(self, text: str) -> None:
        """Set footer text
        
        Args:
            text: Footer text
        """
        self.footer_pane.clear()
        self.footer_pane.write(text, "blue")
    
    async def aset_footer(self, text: str) -> None:
        """Async set footer"""
        await self.footer_pane.aclear()
        await self.footer_pane.awrite(text, "blue")
    
    async def render(self) -> None:
        """Start rendering UI"""
        await self.splitter.render_loop()


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
