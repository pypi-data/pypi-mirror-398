"""Table template - data display and monitoring UI"""
from typing import Optional, List, Dict, Any
from ...core import TerminalSplitter, Pane
from ...logging import PaneLogger
from ...ui import Table


class TableTemplate:
    """Pre-configured table UI for displaying and updating data"""
    
    def __init__(self, title: str = "Data", fps: int = 30, theme: str = "dark") -> None:
        """Initialize table template
        
        Args:
            title: Table title
            fps: Frames per second
            theme: Theme name
        """
        self.title: str = title
        self.splitter: TerminalSplitter = TerminalSplitter(fps=fps, theme=theme)
        
        # Create panes
        self.title_pane: Pane = Pane("title", color="cyan", theme_name=theme)
        self.table_pane: Pane = Pane("table", color="white", theme_name=theme)
        self.info_pane: Pane = Pane("info", color="green", theme_name=theme)
        
        self.splitter.add_pane(self.title_pane)
        self.splitter.add_pane(self.table_pane)
        self.splitter.add_pane(self.info_pane)
        
        # Set weights
        self.splitter.set_pane_weight("title", 0.3)
        self.splitter.set_pane_weight("table", 2.0)
        self.splitter.set_pane_weight("info", 1.0)
        
        # Create loggers
        self.info_logger: PaneLogger = PaneLogger(self.info_pane, include_timestamp=True)
        
        # Table storage
        self.table: Optional[Table] = None
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
    
    def set_headers(self, *headers: str) -> None:
        """Set table headers
        
        Args:
            *headers: Column headers
        """
        self.headers = list(headers)
        self.table = Table(self.headers)
        self._render_table()
    
    async def aset_headers(self, *headers: str) -> None:
        """Async set headers"""
        self.headers = list(headers)
        self.table = Table(self.headers)
        await self._arender_table()
    
    def add_row(self, *values: Any) -> None:
        """Add row to table
        
        Args:
            *values: Row values
        """
        if not self.table:
            return
        
        row = [str(v) for v in values]
        self.rows.append(row)
        self.table.add_row(*values)
        self._render_table()
    
    async def aadd_row(self, *values: Any) -> None:
        """Async add row"""
        if not self.table:
            return
        
        row = [str(v) for v in values]
        self.rows.append(row)
        self.table.add_row(*values)
        await self._arender_table()
    
    def add_rows(self, rows: List[List[Any]]) -> None:
        """Add multiple rows at once
        
        Args:
            rows: List of rows (each row is list of values)
        """
        if not self.table:
            return
        
        for row_values in rows:
            self.table.add_row(*row_values)
            self.rows.append([str(v) for v in row_values])
        
        self._render_table()
    
    async def aadd_rows(self, rows: List[List[Any]]) -> None:
        """Async add multiple rows"""
        if not self.table:
            return
        
        for row_values in rows:
            self.table.add_row(*row_values)
            self.rows.append([str(v) for v in row_values])
        
        await self._arender_table()
    
    def clear_rows(self) -> None:
        """Clear all table rows"""
        if not self.table:
            return
        
        self.table.clear()
        self.rows = []
        self._render_table()
    
    async def aclear_rows(self) -> None:
        """Async clear rows"""
        if not self.table:
            return
        
        self.table.clear()
        self.rows = []
        await self._arender_table()
    
    def _render_table(self) -> None:
        """Render table to pane"""
        self.title_pane.clear()
        self.title_pane.write(f"═══ {self.title} ═══", "cyan")
        
        if self.table:
            self.table_pane.clear()
            self.table_pane.write(self.table.render(), "white")
        
        self.info_logger.info(f"Table updated: {len(self.rows)} rows")
    
    async def _arender_table(self) -> None:
        """Async render table"""
        await self.title_pane.aclear()
        await self.title_pane.awrite(f"═══ {self.title} ═══", "cyan")
        
        if self.table:
            await self.table_pane.aclear()
            await self.table_pane.awrite(self.table.render(), "white")
        
        await self.info_logger.ainfo(f"Table updated: {len(self.rows)} rows")
    
    def update_row(self, row_index: int, *values: Any) -> None:
        """Update specific row
        
        Args:
            row_index: Row index
            *values: New row values
        """
        if not self.table or row_index >= len(self.rows):
            return
        
        # Rebuild table with updated row
        self.table.clear()
        self.rows[row_index] = [str(v) for v in values]
        
        for row in self.rows:
            self.table.add_row(*row)
        
        self._render_table()
    
    async def aupdate_row(self, row_index: int, *values: Any) -> None:
        """Async update row"""
        if not self.table or row_index >= len(self.rows):
            return
        
        self.table.clear()
        self.rows[row_index] = [str(v) for v in values]
        
        for row in self.rows:
            self.table.add_row(*row)
        
        await self._arender_table()
    
    def get_rows(self) -> List[List[str]]:
        """Get all rows
        
        Returns:
            List of rows
        """
        return [row.copy() for row in self.rows]
    
    def get_row(self, index: int) -> Optional[List[str]]:
        """Get specific row
        
        Args:
            index: Row index
            
        Returns:
            Row values or None
        """
        if 0 <= index < len(self.rows):
            return self.rows[index].copy()
        return None
    
    def get_row_count(self) -> int:
        """Get number of rows
        
        Returns:
            Row count
        """
        return len(self.rows)
    
    def log(self, message: str, level: str = "info") -> None:
        """Log message
        
        Args:
            message: Log message
            level: Log level
        """
        if level == "info":
            self.info_logger.info(message)
        elif level == "warning":
            self.info_logger.warning(message)
        elif level == "error":
            self.info_logger.error(message)
        elif level == "debug":
            self.info_logger.debug(message)
    
    async def alog(self, message: str, level: str = "info") -> None:
        """Async log message"""
        if level == "info":
            await self.info_logger.ainfo(message)
        elif level == "warning":
            await self.info_logger.awarning(message)
        elif level == "error":
            await self.info_logger.aerror(message)
        elif level == "debug":
            await self.info_logger.adebug(message)
    
    async def render(self) -> None:
        """Start rendering UI"""
        await self.splitter.render_loop()


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
