# ptydriver

Programmatically drive interactive terminal applications via PTY.

## Overview

ptydriver provides a simple, reliable way to control interactive CLI applications (TUI apps, REPLs, shells, AI agents, etc.) by spawning them in a PTY and maintaining a virtual terminal screen.

**Key Features:**
- Drive any interactive CLI application programmatically
- Send keystrokes and control sequences
- Read terminal output with virtual screen tracking
- Manage multiple instances in parallel with ProcessPool
- No mocks - real process control via PTY

## Installation

```bash
pip install ptydriver
```

Or with uv:

```bash
uv pip install ptydriver
```

## Quick Start

### Basic Usage

```python
from ptydriver import PtyProcess, Keys

# Drive any interactive CLI
with PtyProcess(["python3"]) as proc:
    proc.send("print('hello')")
    proc.wait_for("hello")
    print("Success!")
```

### Interactive Application Control

```python
from ptydriver import PtyProcess, Keys

# Control fzf
with PtyProcess(["bash", "--norc"]) as proc:
    proc.wait_for("$")

    # Launch fzf with some input
    proc.send("echo -e 'apple\\nbanana\\ncherry' | fzf")

    # Type to filter
    proc.send_raw("an")  # Filters to "banana"

    # Navigate and select
    proc.send_raw(Keys.DOWN)
    proc.send_raw(Keys.ENTER)

    proc.wait_for("banana")
```

### Drive Multiple Instances

```python
from ptydriver import ProcessPool

# Manage multiple processes
with ProcessPool() as pool:
    # Spawn 3 instances
    for i in range(3):
        pool.add(["python3"], name=f"python-{i}")

    # Wait for all to be ready
    for proc in pool:
        proc.wait_for(">>>")

    # Send command to all
    pool.broadcast("print('Hello from all!')")

    # Check all have output
    for proc in pool:
        proc.wait_for("Hello from all!")
```

## API Reference

### PtyProcess

The main class for driving a single interactive process.

```python
PtyProcess(
    command: List[str],      # Command and arguments
    width: int = 120,        # Terminal width
    height: int = 40,        # Terminal height
    timeout: int = 5,        # Default timeout for operations
    env: Dict[str, str] = None,  # Environment variables
    cwd: str = None,         # Working directory
)
```

**Methods:**

- `send(text, delay=0.15, press_enter=True)` - Send text to process
- `send_raw(sequence, delay=0.15)` - Send raw escape sequences
- `send_bytes(data, delay=0.15)` - Send raw bytes directly
- `get_content()` - Get current screen content as string
- `get_screen()` - Get screen as list of lines
- `get_cursor_position()` - Get (x, y) cursor position
- `set_size(width, height)` - Resize the terminal window
- `wait_for(pattern, timeout=None)` - Wait for text or regex pattern to appear
- `expect_any(patterns, timeout=None)` - Wait for any of the given patterns (returns index, match)
- `expect_sequence(patterns, timeout=None)` - Wait for a sequence of patterns
- `contains(pattern)` - Check if text or regex is on screen
- `is_alive()` - Check if process is running
- `cleanup()` - Clean up process (called automatically in context manager)

### Advanced Usage

#### Regex Support

`wait_for` and `contains` support compiled regex patterns:

```python
import re
from ptydriver import PtyProcess

with PtyProcess(["bash"]) as proc:
    # Wait for a prompt matching regex
    proc.wait_for(re.compile(r"[\$#]"))
```

#### Multi-Pattern Expectations

Wait for one of multiple possibilities or a specific sequence:

```python
# Expect any of the options
index, match = proc.expect_any(["Success", "Error", re.compile(r"Code: \d+")])
if index == 0:
    print("Succeeded!")

# Expect a sequence of events
proc.expect_sequence([
    "Initializing...",
    re.compile(r"Loading data: \d+%"),
    "Done"
])
```

### ProcessPool

Manage multiple PtyProcess instances for parallel execution.

```python
pool = ProcessPool()
proc = pool.add(["bash"], name="my-bash")
pool.broadcast("echo hello")  # Send to all
pool.cleanup()
```

### Keys

Common key sequences for terminal interaction.

```python
from ptydriver import Keys

# Control characters
Keys.CTRL_C  # Interrupt
Keys.CTRL_D  # EOF
Keys.CTRL_L  # Clear screen

# Arrow keys
Keys.UP, Keys.DOWN, Keys.LEFT, Keys.RIGHT

# Special keys
Keys.ENTER, Keys.TAB, Keys.ESCAPE, Keys.BACKSPACE

# Function keys
Keys.F1 through Keys.F12

# Navigation
Keys.HOME, Keys.END, Keys.PAGE_UP, Keys.PAGE_DOWN

# Helper methods
Keys.ctrl('c')  # Generate Ctrl+C
Keys.alt('f')   # Generate Alt+F
Keys.meta('x')  # Generate Meta+X (same as alt)
Keys.repeat(Keys.DOWN, 5)  # Repeat key 5 times
```

## Use Cases

- **Testing TUI applications**: Automate testing of ncurses apps, vim, fzf, etc.
- **Driving AI agents**: Programmatically control CLI-based AI tools
- **Shell automation**: Script complex interactive shell sessions
- **REPL interaction**: Automate Python, Node.js, or other REPLs
- **Parallel execution**: Run multiple instances of interactive tools

## Requirements

- Python 3.8+
- macOS or Linux
- ptyprocess
- pyte

## License

MIT
