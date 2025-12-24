"""
Performance monitoring and optimization example
"""
import asyncio
from ConsoleMod import (
    TerminalSplitter, Pane, PaneLogger, LogLevel,
    ProgressBar, PerformanceMonitor, PaneExporter,
    Debouncer
)


async def main():
    """Example showing performance monitoring and optimization"""
    
    # Create splitter with metrics enabled
    splitter = TerminalSplitter(
        fps=30,
        theme="dark",
        enable_input=False,
        enable_metrics=True  # Enable performance monitoring
    )
    
    # Create panes
    logs = Pane("logs", color="green")
    metrics_pane = Pane("metrics", color="cyan")
    
    splitter.add_pane(logs)
    splitter.add_pane(metrics_pane)
    
    # Create loggers
    logger = PaneLogger(logs)
    metrics_logger = PaneLogger(metrics_pane, include_timestamp=False)
    
    # Create exporter
    exporter = PaneExporter()
    
    # Progress bar for demo
    progress = ProgressBar(total=100, width=25)
    
    # Debouncer for expensive operations
    debouncer = Debouncer(delay=0.5)
    
    async def expensive_operation(value: int):
        """Simulate expensive operation"""
        await asyncio.sleep(0.1)
        return value * 2
    
    async def log_writer():
        """Generate logs with variable rate"""
        for i in range(50):
            await logger.ainfo(f"Processing item {i}")
            
            # Demonstrate debouncing
            if i % 10 == 0:
                result = await debouncer.debounce(expensive_operation, i)
                await logger.adebug(f"Debounced operation result: {result}")
            
            progress.update(i)
            await asyncio.sleep(0.05)
    
    async def metrics_updater():
        """Update metrics display"""
        for _ in range(100):
            if splitter.perf_monitor:
                metrics = splitter.get_performance_metrics()
                mem_metrics = splitter.get_memory_metrics()
                
                await metrics_pane.aclear()
                
                if metrics:
                    metrics_text = f"""
Performance Metrics:
  FPS: {metrics['fps']:.1f}
  Avg Frame: {metrics['avg_frame_time_ms']:.2f}ms
  Max Frame: {metrics['max_frame_time_ms']:.2f}ms
"""
                    await metrics_pane.awrite(metrics_text)
                
                if mem_metrics:
                    mem_text = f"""
Memory Usage:
  Total: {mem_metrics['total_bytes'] / 1024:.2f}KB
  Breakdown: {mem_metrics['pane_breakdown']}
"""
                    await metrics_pane.awrite(mem_text)
            
            # Update progress
            await metrics_pane.awrite(f"\n{progress.render()}")
            await asyncio.sleep(0.1)
    
    async def export_logs():
        """Periodically export logs"""
        await asyncio.sleep(5)
        
        content = logs.get_content_snapshot()
        
        # Export to multiple formats
        exporter.export_text(content, "logs.txt")
        exporter.export_json(content, "logs.json")
        exporter.export_html(content, "logs.html")
        
        await logger.ainfo("Logs exported to logs.txt, logs.json, logs.html")
    
    # Run tasks
    try:
        await asyncio.gather(
            splitter.render_loop(),
            log_writer(),
            metrics_updater(),
            export_logs(),
        )
    except KeyboardInterrupt:
        await splitter.astop()


if __name__ == "__main__":
    asyncio.run(main())
