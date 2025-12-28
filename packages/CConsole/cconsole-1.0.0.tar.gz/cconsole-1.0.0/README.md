# CConsole (Cool Console Prompt)

A Windows console customization library for Python. Enable VT100 sequences, customize cursor, disable mouse interaction, lock resize, hide scrollbars, and apply blur effects.

## Installation

```bash
pip install CConsole
```

Or install from source:
```bash
pip install -e .
```

## Quick Start

```python
from CConsole import Console

console = Console()
console.init()
```

## Usage

### Basic Initialization

```python
from CConsole import Console

console = Console()
console.init()
```

### Method Chaining for Features

```python
from CConsole import Console

console = Console()
console.init().enable_vt().set_thin_cursor().disable_mouse_interaction().lock_console_resize().hide_console_scrollbar()
```

### Individual Feature Control

```python
console = Console()
console.init()
console.enable_vt()
console.set_thin_cursor()
console.enable_blur_behind()
console.set_title("My App")
```

### Available Methods

| Method | Description |
|--------|-------------|
| `init()` | Initialize console handles |
| `enable_vt()` | Enable VT100 terminal processing |
| `disable_vt()` | Disable VT100 terminal processing |
| `set_thin_cursor(size, visible)` | Set thin cursor |
| `set_block_cursor()` | Set block cursor |
| `hide_cursor()` | Hide cursor |
| `show_cursor()` | Show cursor |
| `disable_mouse_interaction()` | Disable mouse input |
| `enable_mouse_interaction()` | Enable mouse input |
| `lock_console_resize()` | Lock window resize |
| `unlock_console_resize()` | Unlock window resize |
| `hide_console_scrollbar()` | Hide scrollbar |
| `enable_blur_behind(gradient_color)` | Enable blur effect |
| `disable_blur_behind()` | Disable blur effect |
| `set_title(title)` | Set console title |
| `clear()` | Clear console |
| `reset()` | Reset console to defaults |
| `set_size(width, height)` | Set buffer size |
| `move_cursor(x, y)` | Move cursor position |
| `get_hwnd()` | Get window handle |
| `get_output_handle()` | Get output handle |
| `get_input_handle()` | Get input handle |

### Examples

**Custom blur effect:**
```python
from CConsole import Console

console = Console()
console.init(blur_behind=False)
console.enable_blur_behind(gradient_color=0x80000000)
```

**Reset everything:**
```python
console.reset()
```

**Access raw structures:**
```python
from CConsole import COORD, CONSOLE_SCREEN_BUFFER_INFO
```

## Requirements

- Windows OS
- Python >= 3.7

## License

MIT
