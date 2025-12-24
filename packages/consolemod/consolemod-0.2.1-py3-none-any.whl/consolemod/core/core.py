import threading
import asyncio
import time
from typing import Optional, List, Dict, Any, Union
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from .pane import Pane
from .events import EventBus, KeyEvent, FocusEvent, KeyCode
from ..input.input_handler import InputHandler
from ..ui.themes import Theme, get_theme, style_to_rich
from ..ui.layout import Layout, LayoutMode, LayoutConstraints
from ..monitoring.metrics import PerformanceMonitor, MemoryMonitor
from ..monitoring.debounce import Debouncer
from ..utils.config import load_config

class TerminalSplitter:
    """Thread-safe terminal UI splitter with interactive controls"""
    
    def __init__(
        self,
        config: Optional[Union[str, Dict[str, Any]]] = None,
        fps: int = 30,
        theme: str = "dark",
        enable_input: bool = True,
        layout_mode: LayoutMode = LayoutMode.VERTICAL,
        enable_metrics: bool = False
    ) -> None:
        self.panes: List[Pane] = []
        self.lock: threading.RLock = threading.RLock()
        self.fps: int = fps
        self.console: Console = Console()
        self.theme: Theme = get_theme(theme)
        self.event_bus: EventBus = EventBus()
        self.input_handler: Optional[InputHandler] = InputHandler() if enable_input else None
        self.focused_pane_idx: int = 0
        self._running: bool = False
        self.layout: Layout = Layout(layout_mode)
        self.perf_monitor: Optional[PerformanceMonitor] = PerformanceMonitor() if enable_metrics else None
        self.mem_monitor: Optional[MemoryMonitor] = MemoryMonitor() if enable_metrics else None
        self._render_debouncer: Debouncer = Debouncer(0.01)  # Debounce rapid updates
        self.load_config(config)
        if self.panes:
            with self.lock:
                self.panes[self.focused_pane_idx].set_focus(True)
    
    def load_config(self, config: Optional[Union[str, Dict[str, Any]]]) -> None:
        """Load configuration from file or dict (thread-safe)"""
        if isinstance(config, str):
            cfg: Dict[str, Any] = load_config(config)
        elif isinstance(config, dict):
            cfg = config
        else:
            cfg = {}
        for p in cfg.get("panes", []):
            self.add_pane(Pane(**p))
    
    async def aload_config(self, config: Optional[Union[str, Dict[str, Any]]]) -> None:
        """Asynchronous load config (thread-safe)"""
        await asyncio.to_thread(self.load_config, config)
    
    def add_pane(self, pane: Pane) -> None:
        """Add pane to splitter (thread-safe)"""
        with self.lock:
            self.panes.append(pane)
    
    async def aadd_pane(self, pane: Pane) -> None:
        """Asynchronous add pane (thread-safe)"""
        await asyncio.to_thread(self.add_pane, pane)
    
    def get_pane(self, pane_id: str) -> Optional[Pane]:
        """Get pane by ID (thread-safe)"""
        with self.lock:
            return next((p for p in self.panes if p.id == pane_id), None)
    
    async def aget_pane(self, pane_id: str) -> Optional[Pane]:
        """Asynchronous get pane (thread-safe)"""
        return await asyncio.to_thread(self.get_pane, pane_id)
    
    def get_panes(self) -> List[Pane]:
        """Get all panes (thread-safe)"""
        with self.lock:
            return self.panes.copy()
    
    async def aget_panes(self) -> List[Pane]:
        """Asynchronous get all panes (thread-safe)"""
        return await asyncio.to_thread(self.get_panes)
    
    async def render_loop(self) -> None:
        """Main async render loop with input handling (thread-safe)"""
        refresh_rate: float = 1 / self.fps
        
        with self.lock:
            self._running = True
        
        try:
            with Live(console=self.console, refresh_per_second=self.fps, screen=True) as live:
                while True:
                    with self.lock:
                        if not self._running:
                            break
                    
                    # Handle input
                    if self.input_handler:
                        key_event = await self.input_handler.read_key()
                        if key_event:
                            await self._handle_key_event(key_event)
                    
                    layout = self._build_layout()
                    live.update(layout)
                    await asyncio.sleep(refresh_rate)
        except KeyboardInterrupt:
            pass
        finally:
            with self.lock:
                self._running = False
    
    def stop(self) -> None:
        """Stop the render loop (thread-safe)"""
        with self.lock:
            self._running = False
    
    async def astop(self) -> None:
        """Asynchronous stop (thread-safe)"""
        await asyncio.to_thread(self.stop)
    
    async def _handle_key_event(self, event: KeyEvent) -> None:
        """Handle keyboard events (thread-safe)"""
        if event.key == KeyCode.TAB:
            await self._afocus_next()
        elif event.key == KeyCode.SHIFT_TAB:
            await self._afocus_previous()
        elif event.key == KeyCode.UP:
            with self.lock:
                if self.focused_pane_idx < len(self.panes):
                    await self.panes[self.focused_pane_idx].ascroll(-1, 3)
        elif event.key == KeyCode.DOWN:
            with self.lock:
                if self.focused_pane_idx < len(self.panes):
                    await self.panes[self.focused_pane_idx].ascroll(1, 3)
        elif event.key == KeyCode.CTRL_C:
            raise KeyboardInterrupt()
        
        await self.event_bus.emit_key(event)
    
    def _focus_next(self) -> None:
        """Focus next pane (thread-safe)"""
        with self.lock:
            if not self.panes:
                return
            self.panes[self.focused_pane_idx].set_focus(False)
            self.focused_pane_idx = (self.focused_pane_idx + 1) % len(self.panes)
            self.panes[self.focused_pane_idx].set_focus(True)
    
    async def _afocus_next(self) -> None:
        """Asynchronous focus next (thread-safe)"""
        await asyncio.to_thread(self._focus_next)
    
    def _focus_previous(self) -> None:
        """Focus previous pane (thread-safe)"""
        with self.lock:
            if not self.panes:
                return
            self.panes[self.focused_pane_idx].set_focus(False)
            self.focused_pane_idx = (self.focused_pane_idx - 1) % len(self.panes)
            self.panes[self.focused_pane_idx].set_focus(True)
    
    async def _afocus_previous(self) -> None:
        """Asynchronous focus previous (thread-safe)"""
        await asyncio.to_thread(self._focus_previous)
    
    def get_focused_pane(self) -> Optional[Pane]:
        """Get currently focused pane (thread-safe)"""
        with self.lock:
            if 0 <= self.focused_pane_idx < len(self.panes):
                return self.panes[self.focused_pane_idx]
            return None
    
    async def aget_focused_pane(self) -> Optional[Pane]:
        """Asynchronous get focused pane (thread-safe)"""
        return await asyncio.to_thread(self.get_focused_pane)
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Get performance metrics (thread-safe)
        
        Returns:
            Dict with fps, avg_frame_time, etc., or None if metrics disabled
        """
        if self.perf_monitor is None:
            return None
        
        return {
            "fps": self.perf_monitor.get_fps(),
            "avg_frame_time_ms": self.perf_monitor.get_avg_frame_time(),
            "max_frame_time_ms": self.perf_monitor.get_max_frame_time(),
        }
    
    def get_memory_metrics(self) -> Optional[Dict[str, Any]]:
        """Get memory metrics (thread-safe)
        
        Returns:
            Dict with total and per-pane memory, or None if metrics disabled
        """
        if self.mem_monitor is None:
            return None
        
        return {
            "total_bytes": self.mem_monitor.get_total_memory(),
            "pane_breakdown": self.mem_monitor.get_pane_breakdown(),
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics (thread-safe)"""
        if self.perf_monitor:
            self.perf_monitor.reset()
        if self.mem_monitor:
            self.mem_monitor.reset()
    
    def set_layout_mode(self, mode: LayoutMode) -> None:
        """Set layout mode (thread-safe)
        
        Args:
            mode: LayoutMode to use
        """
        self.layout.set_mode(mode)
    
    async def aset_layout_mode(self, mode: LayoutMode) -> None:
        """Asynchronous set layout mode (thread-safe)"""
        await asyncio.to_thread(self.set_layout_mode, mode)
    
    def set_pane_weight(self, pane_id: str, weight: float) -> None:
        """Set pane weight in layout (thread-safe)
        
        Args:
            pane_id: ID of pane
            weight: Layout weight (relative size)
        """
        constraints = self.layout.get_constraints(pane_id)
        constraints.weight = weight
        self.layout.set_constraints(pane_id, constraints)
    
    async def aset_pane_weight(self, pane_id: str, weight: float) -> None:
        """Asynchronous set pane weight (thread-safe)"""
        await asyncio.to_thread(self.set_pane_weight, pane_id, weight)
    
    def _build_layout(self):
        """Build layout with styled panes"""
        from rich.layout import Layout
        layout = Layout()
        with self.lock:
            if not self.panes:
                return layout
            
            # Create sections for each pane
            if len(self.panes) == 1:
                layout.split_column(Layout(name=self.panes[0].id))
            else:
                layout.split_column(*[Layout(name=p.id) for p in self.panes])
            
            for i, pane in enumerate(self.panes):
                # Get visible content
                content_lines = [msg for msg, _ in pane.content]
                content = "\n".join(content_lines[-100:]) if content_lines else "[dim]Empty[/dim]"
                
                # Choose border style based on focus
                if pane.focused:
                    border_style = style_to_rich(self.theme.pane_focus)
                    title = f" {pane.id} [active] "
                else:
                    border_style = style_to_rich(self.theme.pane_border)
                    title = f" {pane.id} "
                
                panel = Panel(
                    content,
                    title=title,
                    border_style=border_style,
                    expand=True
                )
                layout[pane.id].update(panel)
        
        return layout
    
    async def run_async_stream(self, pane_id: str, async_gen) -> None:
        """Run async generator and write output to pane (thread-safe)
        
        Args:
            pane_id: ID of pane to write to
            async_gen: Async generator yielding messages
        """
        pane = await self.aget_pane(pane_id)
        if not pane:
            return
        async for message in async_gen:
            await pane.awrite(message)

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")