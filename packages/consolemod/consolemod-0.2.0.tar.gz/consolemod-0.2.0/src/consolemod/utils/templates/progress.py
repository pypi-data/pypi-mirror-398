"""Progress template - task and progress tracking UI"""
from typing import Optional, Dict, Any
from ...core import TerminalSplitter, Pane
from ...logging import PaneLogger
from ...ui import ProgressBar


class ProgressTemplate:
    """Pre-configured progress tracking UI"""
    
    def __init__(self, title: str = "Progress", fps: int = 30, theme: str = "dark") -> None:
        """Initialize progress template
        
        Args:
            title: Progress tracker title
            fps: Frames per second
            theme: Theme name
        """
        self.title: str = title
        self.splitter: TerminalSplitter = TerminalSplitter(fps=fps, theme=theme)
        
        # Create panes
        self.overview_pane: Pane = Pane("overview", color="cyan", theme_name=theme)
        self.tasks_pane: Pane = Pane("tasks", color="green", theme_name=theme)
        self.logs_pane: Pane = Pane("logs", color="white", theme_name=theme)
        
        self.splitter.add_pane(self.overview_pane)
        self.splitter.add_pane(self.tasks_pane)
        self.splitter.add_pane(self.logs_pane)
        
        # Set weights
        self.splitter.set_pane_weight("overview", 0.5)
        self.splitter.set_pane_weight("tasks", 1.5)
        self.splitter.set_pane_weight("logs", 1.0)
        
        # Create loggers
        self.overview_logger: PaneLogger = PaneLogger(self.overview_pane, include_timestamp=False)
        self.tasks_logger: PaneLogger = PaneLogger(self.tasks_pane, include_timestamp=False)
        self.logs_logger: PaneLogger = PaneLogger(self.logs_pane, include_timestamp=True)
        
        # Progress bars
        self.progress_bars: Dict[str, ProgressBar] = {}
    
    def create_task(self, task_id: str, total: int, width: int = 30) -> ProgressBar:
        """Create new task progress bar
        
        Args:
            task_id: Unique task ID
            total: Total steps for task
            width: Progress bar width
            
        Returns:
            ProgressBar instance
        """
        progress = ProgressBar(total=total, width=width)
        self.progress_bars[task_id] = progress
        return progress
    
    def update_task(self, task_id: str, current: int) -> None:
        """Update task progress
        
        Args:
            task_id: Task ID
            current: Current progress value
        """
        if task_id in self.progress_bars:
            self.progress_bars[task_id].update(current)
            self._render_tasks()
    
    async def aupdate_task(self, task_id: str, current: int) -> None:
        """Async update task"""
        if task_id in self.progress_bars:
            self.progress_bars[task_id].update(current)
            await self._arender_tasks()
    
    def increment_task(self, task_id: str, amount: int = 1) -> None:
        """Increment task progress
        
        Args:
            task_id: Task ID
            amount: Amount to increment
        """
        if task_id in self.progress_bars:
            self.progress_bars[task_id].increment(amount)
            self._render_tasks()
    
    async def aincrement_task(self, task_id: str, amount: int = 1) -> None:
        """Async increment task"""
        if task_id in self.progress_bars:
            self.progress_bars[task_id].increment(amount)
            await self._arender_tasks()
    
    def _render_tasks(self) -> None:
        """Render all task progress bars"""
        self.tasks_pane.clear()
        for task_id, progress in self.progress_bars.items():
            self.tasks_pane.write(f"{task_id}: {progress.render()}", "green")
    
    async def _arender_tasks(self) -> None:
        """Async render tasks"""
        await self.tasks_pane.aclear()
        for task_id, progress in self.progress_bars.items():
            await self.tasks_pane.awrite(f"{task_id}: {progress.render()}", "green")
    
    def set_overview(self, text: str) -> None:
        """Set overview text
        
        Args:
            text: Overview text
        """
        self.overview_pane.clear()
        self.overview_pane.write(f"═══ {self.title} ═══\n{text}", "cyan")
    
    async def aset_overview(self, text: str) -> None:
        """Async set overview"""
        await self.overview_pane.aclear()
        await self.overview_pane.awrite(f"═══ {self.title} ═══\n{text}", "cyan")
    
    def log(self, message: str, level: str = "info") -> None:
        """Log message
        
        Args:
            message: Log message
            level: Log level (info, warning, error, debug)
        """
        if level == "info":
            self.logs_logger.info(message)
        elif level == "warning":
            self.logs_logger.warning(message)
        elif level == "error":
            self.logs_logger.error(message)
        elif level == "debug":
            self.logs_logger.debug(message)
    
    async def alog(self, message: str, level: str = "info") -> None:
        """Async log message"""
        if level == "info":
            await self.logs_logger.ainfo(message)
        elif level == "warning":
            await self.logs_logger.awarning(message)
        elif level == "error":
            await self.logs_logger.aerror(message)
        elif level == "debug":
            await self.logs_logger.adebug(message)
    
    def get_progress(self, task_id: str) -> Optional[ProgressBar]:
        """Get progress bar for task
        
        Args:
            task_id: Task ID
            
        Returns:
            ProgressBar or None
        """
        return self.progress_bars.get(task_id)
    
    def get_all_progress(self) -> Dict[str, ProgressBar]:
        """Get all progress bars
        
        Returns:
            Dict of task_id -> ProgressBar
        """
        return self.progress_bars.copy()
    
    async def render(self) -> None:
        """Start rendering UI"""
        await self.splitter.render_loop()


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
