"""Monitor template - system/process monitoring UI"""
from typing import Optional, Callable, Any, Dict
import asyncio
from ...core import TerminalSplitter
from ...logging import PaneLogger


class MonitorTemplate:
    """Pre-configured monitor UI for tracking metrics and events"""
    
    def __init__(self, name: str = "Monitor", fps: int = 30, theme: str = "dark") -> None:
        """Initialize monitor template
        
        Args:
            name: Monitor name
            fps: Frames per second
            theme: Theme name
        """
        self.name: str = name
        self.splitter: TerminalSplitter = TerminalSplitter(
            fps=fps,
            theme=theme,
            enable_metrics=True
        )
        
        # Create panes
        self.metrics_pane: Pane = Pane("metrics", color="cyan", theme_name=theme)
        self.events_pane: Pane = Pane("events", color="green", theme_name=theme)
        self.alerts_pane: Pane = Pane("alerts", color="red", theme_name=theme)
        
        self.splitter.add_pane(self.metrics_pane)
        self.splitter.add_pane(self.events_pane)
        self.splitter.add_pane(self.alerts_pane)
        
        # Set weights
        self.splitter.set_pane_weight("metrics", 1.0)
        self.splitter.set_pane_weight("events", 1.5)
        self.splitter.set_pane_weight("alerts", 1.0)
        
        # Create loggers
        self.metrics_logger: PaneLogger = PaneLogger(self.metrics_pane, include_timestamp=True)
        self.events_logger: PaneLogger = PaneLogger(self.events_pane, include_timestamp=True)
        self.alerts_logger: PaneLogger = PaneLogger(self.alerts_pane, include_timestamp=True)
        
        # Metric storage
        self.metrics: Dict[str, Any] = {}
        self.alert_threshold: Dict[str, float] = {}
    
    def record_metric(self, name: str, value: Any, unit: str = "") -> None:
        """Record metric value
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
        """
        self.metrics[name] = value
        display = f"{name}: {value}{unit}" if unit else f"{name}: {value}"
        self.metrics_logger.info(display)
    
    async def arecord_metric(self, name: str, value: Any, unit: str = "") -> None:
        """Async record metric"""
        self.metrics[name] = value
        display = f"{name}: {value}{unit}" if unit else f"{name}: {value}"
        await self.metrics_logger.ainfo(display)
    
    def record_event(self, event_type: str, message: str) -> None:
        """Record event
        
        Args:
            event_type: Type of event
            message: Event message
        """
        self.events_logger.info(f"[{event_type}] {message}")
    
    async def arecord_event(self, event_type: str, message: str) -> None:
        """Async record event"""
        await self.events_logger.ainfo(f"[{event_type}] {message}")
    
    def set_alert_threshold(self, metric_name: str, threshold: float) -> None:
        """Set alert threshold for metric
        
        Args:
            metric_name: Name of metric to monitor
            threshold: Alert threshold value
        """
        self.alert_threshold[metric_name] = threshold
    
    def check_alerts(self) -> None:
        """Check metrics against thresholds and emit alerts"""
        for metric_name, threshold in self.alert_threshold.items():
            if metric_name in self.metrics:
                value = self.metrics[metric_name]
                
                # Try to convert to float for comparison
                try:
                    if float(value) > threshold:
                        self.alerts_logger.warning(
                            f"Alert: {metric_name} ({value}) exceeds threshold ({threshold})"
                        )
                except (ValueError, TypeError):
                    pass
    
    async def acheck_alerts(self) -> None:
        """Async check alerts"""
        for metric_name, threshold in self.alert_threshold.items():
            if metric_name in self.metrics:
                value = self.metrics[metric_name]
                
                try:
                    if float(value) > threshold:
                        await self.alerts_logger.awarning(
                            f"Alert: {metric_name} ({value}) exceeds threshold ({threshold})"
                        )
                except (ValueError, TypeError):
                    pass
    
    def get_metric(self, name: str) -> Any:
        """Get metric value
        
        Args:
            name: Metric name
            
        Returns:
            Metric value or None
        """
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics
        
        Returns:
            Dict of all metrics
        """
        return self.metrics.copy()
    
    def monitor_function(self, metric_name: str, unit: str = "") -> Callable:
        """Decorator to monitor function execution
        
        Args:
            metric_name: Name for the metric
            unit: Unit of measurement
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @asyncio.wraps(func)
            async def async_wrapper(*args, **kwargs):
                import time
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    elapsed = (time.time() - start) * 1000  # ms
                    await self.arecord_metric(metric_name, f"{elapsed:.2f}", unit or "ms")
                    await self.arecord_event("execution", f"{func.__name__} completed")
                    return result
                except Exception as e:
                    await self.alerts_logger.aerror(f"{func.__name__} failed: {e}")
                    raise
            
            def sync_wrapper(*args, **kwargs):
                import time
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = (time.time() - start) * 1000  # ms
                    self.record_metric(metric_name, f"{elapsed:.2f}", unit or "ms")
                    self.record_event("execution", f"{func.__name__} completed")
                    return result
                except Exception as e:
                    self.alerts_logger.error(f"{func.__name__} failed: {e}")
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def render(self) -> None:
        """Start rendering UI"""
        await self.splitter.render_loop()


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
