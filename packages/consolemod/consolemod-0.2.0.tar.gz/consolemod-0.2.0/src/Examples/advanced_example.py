import asyncio
import threading
from ConsoleMod import (
    TerminalSplitter, Pane, LayoutMode, PaneLogger, LogLevel,
    ProgressBar, Table, wrap_text, format_bytes, get_theme
)


async def main():
    """Advanced example with multiple features"""
    
    # Create splitter with horizontal layout
    splitter = TerminalSplitter(
        fps=10,
        theme="dark",
        enable_input=True,
        layout_mode=LayoutMode.VERTICAL
    )
    
    # Create panes
    logs_pane = Pane("logs", color="green", theme_name="dark")
    errors_pane = Pane("errors", color="red", theme_name="dark")
    status_pane = Pane("status", color="cyan", theme_name="dark")
    
    splitter.add_pane(logs_pane)
    splitter.add_pane(errors_pane)
    splitter.add_pane(status_pane)
    
    # Set pane weights for layout (logs gets more space)
    splitter.set_pane_weight("logs", 2.0)
    splitter.set_pane_weight("errors", 1.0)
    splitter.set_pane_weight("status", 0.5)
    
    # Create loggers for each pane
    log_logger = PaneLogger(logs_pane, include_timestamp=True)
    error_logger = PaneLogger(errors_pane, include_timestamp=True)
    status_logger = PaneLogger(status_pane, include_timestamp=False)
    
    # Widget examples
    progress = ProgressBar(total=100, width=30)
    status_table = Table(["Task", "Status", "Progress"])
    
    async def log_writer():
        """Write logs with levels"""
        for i in range(10):
            await log_logger.ainfo(f"Task {i} started")
            await asyncio.sleep(0.5)
            await log_logger.adebug(f"Processing step {i}")
            await asyncio.sleep(0.3)
    
    async def error_writer():
        """Write errors and warnings"""
        await error_logger.awarning("High memory usage detected")
        await asyncio.sleep(1.0)
        await error_logger.aerror("Connection timeout")
        await asyncio.sleep(1.0)
        await error_logger.aerror("Retry attempt 1")
        await asyncio.sleep(0.5)
        await error_logger.acritical("Fatal error occurred")
    
    async def status_updater():
        """Update status display"""
        for i in range(101):
            progress.update(i)
            
            # Update table
            status_table.clear()
            status_table.add_row("Task 1", "Running", progress.render())
            status_table.add_row("Task 2", "Queued", "[░░░░░░░░░░] 0%")
            
            await status_pane.aclear()
            await status_pane.awrite(status_table.render())
            await asyncio.sleep(0.1)
    
    # Event handlers
    @splitter.event_bus.on_key
    async def handle_key(event):
        if event.key.value == "up":
            await log_logger.adebug("User pressed up arrow")
        elif event.key.value == "down":
            await log_logger.adebug("User pressed down arrow")
    
    # Run all tasks concurrently
    try:
        await asyncio.gather(
            splitter.render_loop(),
            log_writer(),
            error_writer(),
            status_updater(),
        )
    except KeyboardInterrupt:
        await splitter.astop()


if __name__ == "__main__":
    asyncio.run(main())
