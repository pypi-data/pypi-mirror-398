"""
Template system example - shows all pre-configured templates
"""
import asyncio
from ConsoleMod import (
    LoggerTemplate, DashboardTemplate, MonitorTemplate,
    ProgressTemplate, TableTemplate
)


async def logger_template_example():
    """Example using LoggerTemplate"""
    print("Running LoggerTemplate example..")
    
    logger = LoggerTemplate(name="Logger Example", theme="dark")
    
    # Use decorator to auto-log function calls
    @logger.function(level="info")
    async def process_data(data):
        await asyncio.sleep(0.5)
        return len(data)
    
    async def run_logger():
        await logger.alog("Application started")
        await logger.adebug("Debug information")
        
        result = await process_data([1, 2, 3, 4, 5])
        await logger.alog(f"Processed {result} items")
        
        await logger.awarning("This is a warning")
        
        for i in range(5):
            await logger.alog(f"Task {i} completed")
            await asyncio.sleep(0.2)
    
    try:
        await asyncio.gather(
            logger.render(),
            run_logger(),
        )
    except KeyboardInterrupt:
        await logger.splitter.astop()


async def dashboard_template_example():
    """Example using DashboardTemplate"""
    print("Running DashboardTemplate example..")
    
    dashboard = DashboardTemplate(title="System Dashboard", theme="dark")
    
    async def update_dashboard():
        await dashboard.aset_header("System Status")
        
        # Simulate status updates
        for i in range(20):
            await dashboard.aset_status("CPU", f"{30 + i*2}%", "green")
            await dashboard.aset_status("Memory", f"{60 - i}%", "yellow" if i > 10 else "green")
            
            # Update table
            table_data = [
                ["Task 1", "Running", f"{i*5}%"],
                ["Task 2", "Queued", "0%"],
                ["Task 3", "Complete", "100%"],
            ]
            await dashboard.aset_data_table(["Name", "Status", "Progress"], table_data)
            
            await dashboard.alog(f"Status update {i}", "info")
            
            await asyncio.sleep(0.2)
        
        await dashboard.aset_footer("Dashboard ready. Press Ctrl+C to exit.")
    
    try:
        await asyncio.gather(
            dashboard.render(),
            update_dashboard(),
        )
    except KeyboardInterrupt:
        await dashboard.splitter.astop()


async def monitor_template_example():
    """Example using MonitorTemplate"""
    print("Running MonitorTemplate example..")
    
    monitor = MonitorTemplate(name="Process Monitor", theme="dark")
    
    # Set alert thresholds
    monitor.set_alert_threshold("cpu_usage", 80)
    monitor.set_alert_threshold("memory_usage", 85)
    
    @monitor.monitor_function(metric_name="request_time", unit="ms")
    async def process_request():
        await asyncio.sleep(0.1)
        return "success"
    
    async def run_monitor():
        for i in range(30):
            # Record metrics
            cpu = 30 + (i % 20)
            memory = 50 + (i % 30)
            
            await monitor.arecord_metric("cpu_usage", cpu, "%")
            await monitor.arecord_metric("memory_usage", memory, "%")
            
            await monitor.arecord_event("fetch", f"Retrieved data batch {i}")
            
            # Process request and measure it
            await process_request()
            
            # Check alerts
            await monitor.acheck_alerts()
            
            await asyncio.sleep(0.2)
    
    try:
        await asyncio.gather(
            monitor.render(),
            run_monitor(),
        )
    except KeyboardInterrupt:
        await monitor.splitter.astop()


async def progress_template_example():
    """Example using ProgressTemplate"""
    print("Running ProgressTemplate example..")
    
    progress = ProgressTemplate(title="Multi-Task Progress", theme="dark")
    
    # Create multiple tasks
    task1 = progress.create_task("Download", total=100, width=25)
    task2 = progress.create_task("Process", total=100, width=25)
    task3 = progress.create_task("Upload", total=100, width=25)
    
    async def simulate_tasks():
        await progress.aset_overview("Processing multiple concurrent tasks")
        
        for i in range(101):
            if i <= 50:
                await progress.aupdate_task("Download", i)
            if 30 <= i <= 80:
                await progress.aupdate_task("Process", i - 30)
            if i >= 50:
                await progress.aupdate_task("Upload", i - 50)
            
            await progress.alog(f"Progress: {i}%", "info")
            await asyncio.sleep(0.05)
        
        await progress.alog("All tasks completed!", "info")
    
    try:
        await asyncio.gather(
            progress.render(),
            simulate_tasks(),
        )
    except KeyboardInterrupt:
        await progress.splitter.astop()


async def table_template_example():
    """Example using TableTemplate"""
    print("Running TableTemplate example..")
    
    table = TableTemplate(title="Data Table", theme="dark")
    
    async def update_table():
        # Set headers
        await table.aset_headers("ID", "Name", "Status", "Value")
        
        # Add initial rows
        rows = [
            [1, "Item A", "Active", "100"],
            [2, "Item B", "Pending", "200"],
            [3, "Item C", "Complete", "300"],
        ]
        await table.aadd_rows(rows)
        
        # Simulate updates
        for i in range(20):
            # Add new rows
            await table.aadd_row(i+4, f"Item {chr(68+i%26)}", "Active", str((i+1)*50))
            
            # Update existing rows
            await table.aupdate_row(1, 2, "Item B", "Processing", str(200 + i*10))
            
            await table.alog(f"Table updated: {table.get_row_count()} rows", "info")
            
            await asyncio.sleep(0.2)
    
    try:
        await asyncio.gather(
            table.render(),
            update_table(),
        )
    except KeyboardInterrupt:
        await table.splitter.astop()


async def main():
    """Run all template examples"""
    examples = [
        ("Logger", logger_template_example),
        ("Dashboard", dashboard_template_example),
        ("Monitor", monitor_template_example),
        ("Progress", progress_template_example),
        ("Table", table_template_example),
    ]
    
    print("ConsoleMod Template Examples")
    print("=" * 40)
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}Template")
    
    choice = input("\nSelect example (1-5): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(examples):
            await examples[idx][1]()
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")


if __name__ == "__main__":
    asyncio.run(main())
