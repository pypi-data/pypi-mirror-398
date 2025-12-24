# ConsoleMod

A powerful, thread-safe terminal UI library combining the best of Rich and Curses with modern async support. Build sophisticated terminal applications with multiple interactive panes, real-time logging, and responsive keyboard controls.

**Status:** Hobby Project | **License:** 404_CM-v1.0 (Custom) | **AI/ML:** See [OPTOUT.md](OPTOUT.md) | **Support:** consolemode@404development.dev

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Module Structure](#module-structure)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)

## Features

### 🎨 Theming & Styling
- Pre-built themes: Dark, Light, Solarized
- Custom theme support with fine-grained control
- Style objects for colors, bold, italic, underline, dim effects
- Dynamic theme switching at runtime

### 🔄 Interactive Controls
- Keyboard navigation (Tab, Shift+Tab for pane focus)
- Arrow key scrolling within panes
- Event-based system for custom key handlers
- Thread-safe event bus with async/sync support
- Configurable keybindings

### 📐 Flexible Layouts
- Vertical, Horizontal, and Grid layout modes
- Per-pane weight control for flexible sizing
- Automatic layout calculation and adjustment
- Dynamic layout switching

### 📝 Logging & Formatting
- PaneLogger with color-coded levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Integration with Python's standard logging module
- Comprehensive text formatting utilities:
  - Word wrapping with custom width
  - Text alignment (left, center, right)
  - Text truncation with custom suffixes
  - Human-readable formatting (bytes, duration)
  - Box drawing for visual emphasis

### 🎛️ Widgets
- ProgressBar with percentage and fill visualization
- Spinner with customizable animation
- Table with automatic column alignment
- Button with click callbacks
- Input fields with validation
- Selection lists and checkboxes

### 🔒 Thread Safety
- RLock-based synchronization for all state
- Dual sync/async API for all operations
- Safe handler execution across threads
- Atomic state updates
- Non-blocking I/O operations

### 📊 Performance Monitoring
- Real-time FPS tracking
- Frame timing metrics
- Per-pane memory tracking
- Performance metrics collection and reporting

### 🎯 Advanced Features
- Debouncing and throttling utilities
- Command history with navigation
- Undo/redo stack for state management
- Pane content export to files
- Circular buffer for efficient memory usage
- Pre-built templates for common UI patterns

## Installation

### From Source
```bash
# Clone or download the repository
cd ConsoleMod

# Install in development mode
pip install -e .

# Or simply import directly
import sys
sys.path.insert(0, '/path/to/ConsoleMod')
```

### Requirements
- Python 3.7+
- Rich library (for rendering)
- Standard library: asyncio, threading, logging

## Quick Start

### Basic Multi-Pane Application

```python
import asyncio
from ConsoleMod import TerminalSplitter, Pane, PaneLogger

async def main():
    # Create the main UI controller
    splitter = TerminalSplitter(fps=30, theme="dark", enable_input=True)
    
    # Create panes for different outputs
    logs_pane = Pane("logs", color="green")
    errors_pane = Pane("errors", color="red")
    status_pane = Pane("status", color="blue")
    
    # Add panes to splitter
    splitter.add_pane(logs_pane)
    splitter.add_pane(errors_pane)
    splitter.add_pane(status_pane)
    
    # Create loggers for each pane
    log_logger = PaneLogger(logs_pane, include_timestamp=True)
    error_logger = PaneLogger(errors_pane, include_timestamp=True)
    
    # Log some messages
    await log_logger.ainfo("Application started")
    await log_logger.ainfo("Initializing components...")
    await error_logger.awarning("Example warning message")
    
    # Write to status pane directly
    await status_pane.awrite("[green]Ready[/green]")
    
    # Run the UI loop (blocks until Ctrl+C)
    await splitter.render_loop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage Examples

### Basic Multi-Pane Display

```python
from ConsoleMod import TerminalSplitter, Pane

# Create splitter with custom FPS
splitter = TerminalSplitter(fps=60, theme="light")

# Create panes
logs_pane = Pane("logs")
status_pane = Pane("status")
debug_pane = Pane("debug")

# Add to splitter
splitter.add_pane(logs_pane)
splitter.add_pane(status_pane)
splitter.add_pane(debug_pane)

# Write data
logs_pane.write("Application log entry")
status_pane.write("Status: Running")
debug_pane.write("Debug information")
```

### Logging with Levels

```python
from ConsoleMod import Pane, PaneLogger, LogLevel

pane = Pane("output")
logger = PaneLogger(pane, include_timestamp=True)

# Different log levels with automatic coloring
logger.debug("Debug message")        # Blue
logger.info("Info message")          # Green
logger.warning("Warning message")    # Yellow
logger.error("Error message")        # Red
logger.critical("Critical error!")   # Bright Red

# Custom level logging
await logger.alog("Custom message", LogLevel.INFO)
```

### Layout Control

```python
from ConsoleMod import TerminalSplitter, LayoutMode, Pane

splitter = TerminalSplitter(layout_mode=LayoutMode.VERTICAL)

# Add panes
main = Pane("main")
sidebar = Pane("sidebar")
splitter.add_pane(main)
splitter.add_pane(sidebar)

# Control pane sizing with weights
splitter.set_pane_weight("main", 3.0)      # 3x larger
splitter.set_pane_weight("sidebar", 1.0)   # 1x size

# Switch layout dynamically
await splitter.aset_layout_mode(LayoutMode.HORIZONTAL)
```

### Widgets and Progress

```python
from ConsoleMod import ProgressBar, Table, Spinner, Button

# Progress bar
progress = ProgressBar(total=100, width=30)
for i in range(101):
    progress.increment(1)
    print(progress.render())

# Table
table = Table(["Name", "Status", "Progress"])
table.add_row("Task 1", "Running", "50%")
table.add_row("Task 2", "Queued", "0%")
table.add_row("Task 3", "Complete", "100%")
print(table.render())

# Spinner for loading states
spinner = Spinner("Loading...")
for _ in range(10):
    print(spinner.next_frame())

# Button with callback
def on_click():
    print("Button clicked!")

button = Button("Click Me", on_click)
```

### Text Formatting

```python
from ConsoleMod import (
    wrap_text, align_text, format_bytes, 
    format_duration, create_box, TextAlign
)

# Wrapping long text
long_text = "This is a very long text that needs to be wrapped..."
lines = wrap_text(long_text, width=40)

# Text alignment
centered = align_text("Hello", width=50, align=TextAlign.CENTER)
right_aligned = align_text("Right", width=50, align=TextAlign.RIGHT)

# Human-readable formatting
size = format_bytes(1048576)      # "1.0 MB"
time = format_duration(3661)      # "1.0h"

# Visual boxes
box = create_box("Important!", style="double")
print(box)
```

### Event Handling

```python
from ConsoleMod import TerminalSplitter, KeyCode

splitter = TerminalSplitter(enable_input=True)

# Register async key handler
@splitter.event_bus.on_key
async def handle_keys(event):
    if event.key == KeyCode.UP:
        print("Up arrow pressed")
    elif event.key == KeyCode.DOWN:
        print("Down arrow pressed")
    elif event.key == KeyCode.ENTER:
        print("Enter pressed")

# Or register sync handler
def sync_handler(event):
    print(f"Key pressed: {event.key.value}")

splitter.event_bus.on_key(sync_handler)
```

### Using Templates

```python
from ConsoleMod import LoggerTemplate, DashboardTemplate, ProgressTemplate

# Pre-built logger UI
logger_ui = LoggerTemplate(name="MyApp", fps=30, theme="dark")
await logger_ui.start()

# Pre-built dashboard
dashboard = DashboardTemplate(name="Dashboard", theme="dark")
dashboard.add_status("cpu", "CPU: 45%")
dashboard.add_status("memory", "Memory: 2.3 GB")

# Progress tracking UI
progress_ui = ProgressTemplate(name="Tasks", theme="dark")
progress_ui.add_task("download", "Downloading...", total=100)
progress_ui.add_task("process", "Processing...", total=50)
```

### History and Undo/Redo

```python
from ConsoleMod import CommandHistory, UndoRedoStack

# Command history with navigation
history = CommandHistory(max_size=100)
history.add("command1")
history.add("command2")

previous = history.previous()  # Get previous command
next_cmd = history.next()      # Get next command

# Undo/redo functionality
undo_stack = UndoRedoStack()
undo_stack.push(state_1)
undo_stack.push(state_2)

previous_state = undo_stack.undo()
restored_state = undo_stack.redo()
```

### Performance Monitoring

```python
from ConsoleMod import TerminalSplitter

splitter = TerminalSplitter(enable_metrics=True)

# During runtime, get metrics
perf = splitter.get_performance_metrics()
print(f"FPS: {perf['fps']}")
print(f"Avg frame time: {perf['avg_frame_time_ms']}ms")

mem = splitter.get_memory_metrics()
print(f"Total memory: {mem['total_bytes']}")
print(f"Per-pane breakdown: {mem['pane_breakdown']}")

# Reset metrics
splitter.reset_metrics()
```

## Module Structure

ConsoleMod is organized into focused modules for easy navigation and maintenance:

```
ConsoleMod/
├── core/              # Terminal UI foundation
├── ui/                # Visual components and theming
├── input/             # Keyboard input and keybindings
├── interaction/       # Forms, dialogs, menus
├── logging/           # Pane-based logging
├── monitoring/        # Performance metrics
└── utils/             # Utilities and templates
```

See [STRUCTURE.md](STRUCTURE.md) for detailed module documentation.

## API Reference

### TerminalSplitter

Main UI controller for managing panes and rendering.

**Constructor:**
```python
TerminalSplitter(
    config: Optional[Union[str, Dict]] = None,
    fps: int = 30,
    theme: str = "dark",
    enable_input: bool = True,
    layout_mode: LayoutMode = LayoutMode.VERTICAL,
    enable_metrics: bool = False
)
```

**Key Methods:**
- `add_pane(pane)` / `aadd_pane(pane)` - Add a pane to the splitter
- `get_pane(pane_id)` / `aget_pane(pane_id)` - Get pane by ID
- `get_panes()` / `aget_panes()` - Get all panes
- `get_focused_pane()` / `aget_focused_pane()` - Get currently focused pane
- `set_layout_mode(mode)` / `aset_layout_mode(mode)` - Change layout mode
- `set_pane_weight(pane_id, weight)` / `aset_pane_weight(...)` - Control sizing
- `render_loop()` - Start the async render loop
- `stop()` / `astop()` - Stop rendering
- `get_performance_metrics()` - Get FPS and timing data
- `get_memory_metrics()` - Get memory usage data
- `reset_metrics()` - Reset all metrics

### Pane

Content container with circular buffer storage.

**Constructor:**
```python
Pane(
    id: str,
    width: float = 0.5,
    height: float = 0.5,
    color: str = "white",
    border: bool = True,
    theme_name: str = "dark",
    max_lines: int = 1000
)
```

**Key Methods:**
- `write(message, style)` / `awrite(...)` - Write text to pane
- `clear()` / `aclear()` - Clear all content
- `scroll(direction, amount)` / `ascroll(...)` - Scroll content
- `set_focus(focused)` / `aset_focus(...)` - Set focus state
- `get_visible_content(height)` / `aget_visible_content(...)` - Get displayed content

### PaneLogger

Structured logging directly to panes with level coloring.

**Constructor:**
```python
PaneLogger(
    pane: Pane,
    include_timestamp: bool = True
)
```

**Key Methods:**
- `debug(message)` / `adebug(message)` - Log debug message
- `info(message)` / `ainfo(message)` - Log info message
- `warning(message)` / `awarning(message)` - Log warning
- `error(message)` / `aerror(message)` - Log error
- `critical(message)` / `acritical(message)` - Log critical error
- `log(message, level)` / `alog(message, level)` - Log at custom level

### Layout

Layout manager for pane arrangement.

**Modes:**
- `LayoutMode.VERTICAL` - Stack panes top to bottom
- `LayoutMode.HORIZONTAL` - Stack panes left to right
- `LayoutMode.GRID` - Arrange in grid pattern

### Widgets

UI component library:
- `ProgressBar` - Progress visualization with percentage
- `Spinner` - Animated loading indicator
- `Table` - Formatted data table with columns
- `Button` - Clickable button with callback
- `InputField` - Text input with validation
- `SelectField` - Selection dropdown
- `CheckboxField` - Boolean checkbox

## Architecture

### Thread Safety
All public methods use `threading.RLock()` for state synchronization. Both sync and async versions are provided for all operations:

```python
# Synchronous - can call from any thread
pane.write("Message")

# Asynchronous - call from async context
await pane.awrite("Message")
```

### Event System
Keyboard events are processed through an event bus, allowing multiple handlers:

```python
@splitter.event_bus.on_key
async def handler(event: KeyEvent):
    # Handle key event
    pass
```

### Performance Optimization
- 30 FPS default refresh rate (configurable)
- Circular buffer with configurable line limits per pane
- Debouncing for rapid updates
- Non-blocking async I/O for input
- Memory-efficient rendering

## Contributing

ConsoleMod is a hobby project. While not accepting external contributions through traditional means, we welcome feedback and suggestions.

**To report issues or suggest features:**
- Email: consolemode@404development.dev
- Include detailed description and steps to reproduce

**To use ConsoleMod in your projects:**
- You may modify and extend for personal/hobby use
- You must attribute the original creators
- You must preserve this license and attribution
- Commercial/industrial use is not permitted

See [404_CM-v1.0](404_CM-v1.0) for full license terms.

## Support

For questions, issues, or suggestions:

**Email:** consolemode@404development.dev

**Documentation:**
- [STRUCTURE.md](STRUCTURE.md) - Detailed module organization
- [examples/](examples/) - Complete working examples
- API Reference above

## Keyboard Shortcuts

Default shortcuts when `enable_input=True`:

| Key | Action |
|-----|--------|
| **Tab** | Next pane |
| **Shift+Tab** | Previous pane |
| **Up Arrow** | Scroll up in focused pane |
| **Down Arrow** | Scroll down in focused pane |
| **Ctrl+C** | Exit application |

## Performance

- **FPS:** 30 default (configurable 1-60)
- **Memory:** Efficient circular buffers with per-pane limits
- **Rendering:** Only changed content updates
- **I/O:** Non-blocking async input handling

## Version History

### v0.1.0
- Initial release
- Core UI framework with multi-pane support
- Theming and styling system
- Keyboard input handling
- Logging and formatting utilities
- Performance monitoring
- Template-based UI patterns

## Acknowledgments

**Original Developer:** 404Development LLC
**Project:** ConsoleMod - A Hobby Terminal UI Library
**Contributors:** See contributions for detailed credits

This project represents collaborative effort in hobby software development.

## Important Policy: AI/ML Opt-Out

**ConsoleMod is NOT authorized for use in training, development, or deployment of Artificial Intelligence, Machine Learning, or Large Language Models.**

This code and documentation are created **exclusively for human consumption and education**. Any use of ConsoleMod for AI/ML purposes is explicitly prohibited.

### Prohibited Uses
- ❌ Training datasets for machine learning
- ❌ Large Language Model (LLM) training data
- ❌ AI model development or fine-tuning
- ❌ Automated data harvesting for AI
- ❌ Deployment in AI systems or products

### Permitted Uses
- ✅ Human learning and education
- ✅ Personal hobby projects
- ✅ Building human-created applications
- ✅ Educational courses and tutorials (for humans)
- ✅ Manual code review and study

**For the complete AI/ML opt-out policy, see [OPTOUT.md](OPTOUT.md).**

This is a binding restriction under the 404_CM-v1.0 license. Violations will result in license termination and potential legal action.

---

## License

**404_CM-v1.0** - Custom hobby software license

This project is licensed under the 404_CM-v1.0 license. You have the right to:
- Use, modify, and implement this system for hobby/personal projects
- Recreate and expand upon the codebase
- Distribute modified versions for non-commercial use

You may NOT:
- Use this software for commercial or industrial purposes
- Profit from this software in any way
- Remove or modify license and attribution information
- Use for AI/ML training or deployment (see [OPTOUT.md](OPTOUT.md))

All rights reserved to the contributors and original developer, 404Development LLC.

For the complete license text, see [404_CM-v1.0](404_CM-v1.0).

---

**Support:** consolemode@404development.dev
**License:** [404_CM-v1.0](404_CM-v1.0)
**Status:** Active (Hobby Project)
