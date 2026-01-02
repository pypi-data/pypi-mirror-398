# textual-filelink
[![CI](https://github.com/eyecantell/textual-filelink/actions/workflows/ci.yml/badge.svg)](https://github.com/eyecantell/textual-filelink/actions/runs/20478941078)
[![PyPI](https://img.shields.io/pypi/v/textual-filelink.svg)](https://pypi.org/project/textual-filelink/)
[![Python Versions](https://img.shields.io/pypi/pyversions/textual-filelink.svg)](https://pypi.org/project/textual-filelink/)
[![Downloads](https://pepy.tech/badge/textual-filelink)](https://pepy.tech/project/textual-filelink)
[![Coverage](https://codecov.io/gh/eyecantell/textual-filelink/branch/main/graph/badge.svg)](https://codecov.io/gh/eyecantell/textual-filelink)
[![License](https://img.shields.io/pypi/l/textual-filelink.svg)](https://github.com/eyecantell/textual-filelink/blob/main/LICENSE)

Clickable file links for [Textual](https://github.com/Textualize/textual) applications. Open files in your editor directly from your TUI.

## Features

- 🔗 **Clickable file links** that open in your preferred editor (VSCode, vim, nano, etc.)
- ☑️ **Toggle controls** for selecting/deselecting files
- ❌ **Remove buttons** for file management interfaces
- 🎨 **Multiple status icons** with unicode support for rich visual feedback
- 📍 **Icon positioning** - place icons before or after filenames
- 🔢 **Icon ordering** - control display order with explicit indices
- 👆 **Clickable icons** - make icons interactive with click events
- 👁️ **Dynamic visibility** - show/hide icons on the fly
- 🎯 **Jump to specific line and column** in your editor
- 🔧 **Customizable command builders** for any editor
- 🎭 **Flexible layouts** - show/hide controls as needed
- 💬 **Smart tooltips** - automatic keyboard shortcut hints with optional control
- 🚀 **Command orchestration** with play/stop controls and animated spinners
- ⌨️ **Keyboard accessible** - fully tabbable and navigable without a mouse
- 🔑 **Customizable keyboard shortcuts** - configure your own key bindings

## Installation

```bash
pip install textual-filelink
```

Or with PDM:

```bash
pdm add textual-filelink
```

## Quick Start

### Basic FileLink

```python
from pathlib import Path
from textual.app import App, ComposeResult
from textual_filelink import FileLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        # Auto-generates id="readme-md"
        yield FileLink("README.md", line=10, column=5)

        # Or provide explicit ID
        yield FileLink("script.py", id="main-script")

    def on_file_link_opened(self, event: FileLink.Opened):
        self.notify(f"Opened {event.path.name} at line {event.line}")

if __name__ == "__main__":
    MyApp().run()
```

### CommandLink for Command Orchestration

CommandLink displays command status with play/stop controls and optional timer display for elapsed time and time-ago:

- ○             ▶️ Lint        - Not run (no timer)
- ○ [1]         ▶️ Lint        - Not run with shortcut indicator
- ⏳ 12m 34s    ⏹️ Tests       - Running for 12 minutes 34 seconds
- ✅ 5s ago     ▶️ Format      - Completed 5 seconds ago
- ❌ 6d ago     ▶️ Build       - Failed 6 days ago

```python
from textual_filelink import CommandLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield CommandLink(
            "Run Tests",
            output_path="test_output.log",
            initial_status_icon="○",
            initial_status_tooltip="Not run yet",
            show_settings=True,
            show_timer=True,  # Enable timer display
        )

    def on_command_link_play_clicked(self, event: CommandLink.PlayClicked):
        link = self.query_one(CommandLink)
        link.set_status(running=True, tooltip="Running tests...")
        # Start your command here

    def on_command_link_stop_clicked(self, event: CommandLink.StopClicked):
        link = self.query_one(CommandLink)
        link.set_status(icon="⏹", running=False, tooltip="Stopped")

    def on_command_link_settings_clicked(self, event: CommandLink.SettingsClicked):
        self.notify(f"Settings for {event.name}")

if __name__ == "__main__":
    MyApp().run()
```

**With Timer (for textual-cmdorc integration):**

```python
from textual_filelink import CommandLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield CommandLink(
            "Build Project",
            show_timer=True,         # Show elapsed/time-ago column
            timer_field_width=12,    # Fixed width (default: 12)
        )

    def on_command_link_play_clicked(self, event: CommandLink.PlayClicked):
        link = self.query_one(CommandLink)
        link.set_status(running=True)
        # Update timer with pre-formatted strings (e.g., from textual-cmdorc)
        link.set_timer_data(duration_str="1m 23s")

    async def update_timer_periodically(self, link: CommandLink, duration_str: str):
        # Timer display updates automatically every 1 second
        link.set_timer_data(duration_str=duration_str)

    def on_completion(self, link: CommandLink):
        link.set_status(icon="✅", running=False)
        link.set_timer_data(time_ago_str="30s ago")
```

### FileLinkList for Managing Collections

```python
from textual_filelink import FileLinkList, FileLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        file_list = FileLinkList(show_toggles=True, show_remove=True)
        
        # Add items (all items must have explicit IDs)
        file_list.add_item(FileLink("test.py", id="test-py"), toggled=True)
        file_list.add_item(FileLink("main.py", id="main-py"))
        
        yield file_list
    
    def on_file_link_list_item_toggled(self, event: FileLinkList.ItemToggled):
        self.notify(f"Toggled: {event.item.path}")
    
    def on_file_link_list_item_removed(self, event: FileLinkList.ItemRemoved):
        self.notify(f"Removed: {event.item.path}")

if __name__ == "__main__":
    MyApp().run()
```

### FileLinkWithIcons for Composable File Links

```python
from textual_filelink import FileLinkWithIcons, Icon

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield FileLinkWithIcons(
            "script.py",
            line=42,
            icons_before=[
                Icon(name="status", icon="✅", tooltip="Validated"),
                Icon(name="type", icon="🐍", tooltip="Python file"),
            ],
            icons_after=[
                Icon(name="lock", icon="🔒", clickable=True, key="l", tooltip="Toggle lock"),
            ],
        )

        # Custom keyboard shortcuts
        yield FileLinkWithIcons(
            "config.yaml",
            open_keys=["f2"],  # Press F2 to open (instead of default Enter/O)
            icons_before=[Icon(name="status", icon="✓")],
        )

    def on_file_link_with_icons_icon_clicked(self, event: FileLinkWithIcons.IconClicked):
        self.notify(f"Clicked icon: {event.icon_name}")

if __name__ == "__main__":
    MyApp().run()
```

## Keyboard Navigation

### Tab Navigation
All FileLink widgets are fully keyboard accessible and can be navigated using standard terminal keyboard shortcuts:

- **Tab** - Move focus to the next widget
- **Shift+Tab** - Move focus to the previous widget

When a FileLink widget has focus, it displays a visual indicator (border with accent color). You can customize the focus appearance using CSS.

### Built-in Keyboard Shortcuts

All FileLink widgets support keyboard activation:

**FileLink:**
- `enter` or `o` - Open file in editor

**FileLinkWithIcons:**
- `enter` or `o` - Open file in editor (via embedded FileLink)
- `1-9` - Activate clickable icons (if defined with `key` parameter)

**CommandLink:**
- `enter` or `o` - Open output file (if path is set)
- `space` or `p` - Play/Stop command
- `s` - Settings (if show_settings=True)

**FileLinkWithIcons:**
- `enter` or `o` - Open file in editor
- Custom keys - If icons have `key` parameter set

### Default Keyboard Shortcuts

All widgets have class-level default keyboard shortcuts that can be customized:

**FileLink:**
```python
FileLink.DEFAULT_OPEN_KEYS = ["enter", "o"]
```

**FileLinkWithIcons:**
Uses `FileLink.DEFAULT_OPEN_KEYS` as its default (since it embeds a FileLink).

**CommandLink:**
```python
CommandLink.DEFAULT_OPEN_KEYS = ["enter", "o"]
CommandLink.DEFAULT_PLAY_STOP_KEYS = ["space", "p"]
CommandLink.DEFAULT_SETTINGS_KEYS = ["s"]
```

These defaults apply to all instances unless overridden with the `open_keys`, `play_stop_keys`, or `settings_keys` parameters.

### Customizing Keyboard Shortcuts

You can customize keyboard shortcuts per-widget using the `open_keys`, `play_stop_keys`, and `settings_keys` parameters:

```python
# FileLink with custom open keys
link = FileLink(
    "file.py",
    open_keys=["f2", "ctrl+o"]  # Override default "enter"/"o"
)

# CommandLink with custom shortcuts
cmd = CommandLink(
    "Build",
    open_keys=["enter"],
    play_stop_keys=["f5", "ctrl+r"],
    settings_keys=["f2"]
)
```

### Dynamic App-Level Bindings

Bind number keys to activate specific widgets in a list without requiring focus (useful for scrollable lists of commands):

```python
from textual import events
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual_filelink import CommandLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield CommandLink("Build", id="cmd-1")
            yield CommandLink("Test", id="cmd-2")
            yield CommandLink("Deploy", id="cmd-3")

    def on_key(self, event: events.Key) -> None:
        """Route number keys to commands - triggers play/stop toggle."""
        if event.key.isdigit():
            num = int(event.key)
            commands = list(self.query(CommandLink))
            if 0 < num <= len(commands):
                cmd = commands[num - 1]
                # Use action method to toggle play/stop automatically
                cmd.action_play_stop()
                event.prevent_default()
```

### Keyboard Shortcut Discoverability

All interactive elements automatically display their keyboard shortcuts in tooltips. This makes keyboard navigation discoverable without reading documentation. Note that if tooltips are too long, textual may not render them properly (they may blink or have other odd behavior).

**Examples:**
- Toggle checkbox: "Click to toggle (space/t)"
- Remove button: "Remove (delete/x)"
- Play button: "Run command (space/p)"
- Settings: "Settings (s)"
- Clickable icon 1: "Status (1)"

## FileLink API

### Constructor

```python
FileLink(
    path: Path | str,
    display_name: str | None = None,
    *,
    line: int | None = None,
    column: int | None = None,
    command_builder: Callable | None = None,
    open_keys: list[str] | None = None,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
    _embedded: bool = False,
    tooltip: str | None = None,
)
```

**Parameters:**
- `path`: Full path to the file
- `display_name`: Text to display for the link. If None, defaults to the filename
- `line`: Optional line number to jump to
- `column`: Optional column number to jump to
- `command_builder`: Custom function to build the editor command
- `open_keys`: Custom keyboard shortcuts for opening (default: ["enter", "o"])
- `name`: Widget name
- `id`: Widget ID
- `classes`: CSS classes
- `_embedded`: Internal use only. Internal use only. If True, disables focus to prevent stealing focus from parent widgets (used when FileLink is embedded in CommandLink or FileLinkWithIcons)
- `tooltip`: Optional tooltip text

### Properties

- `path: Path` - The file path
- `display_name: str` - The display name
- `line: int | None` - The line number
- `column: int | None` - The column number

### Methods

#### `open_file()`
Open the file in the configured editor (can be called programmatically).

### Messages

#### `FileLink.Opened`
Posted when the link is clicked or opened via keyboard.

**Attributes:**
- `widget: FileLink` - The FileLink widget that was opened
- `path: Path` - The file path that was opened
- `line: int | None` - The line number to navigate to (or None)
- `column: int | None` - The column number to navigate to (or None)

**Note:** `FileLink.Clicked` is deprecated but still available for backwards compatibility. Use `FileLink.Opened` instead.

### Class-Level Configuration

```python
# Set default command builder for all FileLink instances
FileLink.default_command_builder = FileLink.vim_command

# Set default open keys for all FileLink instances
FileLink.DEFAULT_OPEN_KEYS = ["enter", "f2"]
```

## CommandLink API

`CommandLink` is a widget for command orchestration and status display. It provides play/stop controls, animated spinner, status icons, and optional settings.

### Architecture

CommandLink is a standalone widget that extends `Horizontal`. It has a flat composition:
- Status icon (or animated spinner when running)
- Play/stop button (▶️/⏸️)
- Command name (clickable FileLink if output_path is set)
- Settings icon (optional, if show_settings=True)

**Note:** Toggle and remove controls are NOT part of CommandLink. If you need those, add the CommandLink to a FileLinkList with `show_toggles=True` and `show_remove=True`.

### Quick Start

```python
from textual_filelink import CommandLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield CommandLink(
            "Run Tests",
            output_path="test_output.log",
            initial_status_icon="○",
            initial_status_tooltip="Not run yet",
            show_settings=True,
        )

    def on_command_link_play_clicked(self, event: CommandLink.PlayClicked):
        link = self.query_one(CommandLink)
        link.set_status(running=True, tooltip="Running tests...")
        self.run_worker(self.run_tests(link))

    def on_command_link_stop_clicked(self, event: CommandLink.StopClicked):
        link = self.query_one(CommandLink)
        link.set_status(icon="⏹", running=False, tooltip="Stopped")

    def on_command_link_settings_clicked(self, event: CommandLink.SettingsClicked):
        self.notify(f"Settings for {event.name}")

    async def run_tests(self, link: CommandLink):
        # Simulate test run
        await asyncio.sleep(2)
        link.set_status(icon="✅", running=False, tooltip="All tests passed")
```

**Custom Spinner Example:**

```python
# Faster circle spinner for quick operations
yield CommandLink(
    "Quick Build",
    spinner_frames=["◐", "◓", "◑", "◒"],
    spinner_interval=0.05
)
```

### Constructor

```python
CommandLink(
    command_name: str,
    *,
    output_path: Path | str | None = None,
    command_builder: Callable | None = None,
    initial_status_icon: str = "○",
    initial_status_tooltip: str | None = None,
    show_settings: bool = False,
    tooltip: str | None = None,
    open_keys: list[str] | None = None,
    play_stop_keys: list[str] | None = None,
    settings_keys: list[str] | None = None,
    spinner_frames: list[str] | None = None,
    spinner_interval: float = 0.1,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
)
```

**Parameters:**
- `command_name`: Command display name (also used to generate widget ID if not provided)
- `output_path`: Path to output file. If set, clicking command name opens the file
- `command_builder`: Custom command builder for opening output files
- `initial_status_icon`: Initial status icon (default: "○")
- `initial_status_tooltip`: Initial tooltip for status icon
- `show_settings`: Whether to show the settings icon (default: False)
- `tooltip`: Custom tooltip for command name widget. If None, uses command name. Keyboard shortcuts are automatically appended
- `open_keys`: Custom keyboard shortcuts for opening output (default: ["enter", "o"])
- `play_stop_keys`: Custom keyboard shortcuts for play/stop (default: ["space", "p"])
- `settings_keys`: Custom keyboard shortcuts for settings (default: ["s"])
- `spinner_frames`: Custom spinner animation frames (unicode characters). If None, uses Braille pattern. Example: ["◐", "◓", "◑", "◒"]
- `spinner_interval`: Seconds between spinner frame updates. Default: 0.1. Lower = faster spin. Example: 0.05
- `name`: Widget name for Textual's widget identification system (optional)
- `id`: Widget ID. If None, auto-generated from command_name
- `classes`: CSS classes

### Layout

```
[status/spinner] [timer?] [▶️/⏸️] command_name [⚙️]
```

- **status/spinner**: Shows status icon, or animated spinner when running
- **timer**: Fixed-width elapsed/time-ago display (only if show_timer=True)
- **play/stop**: ▶️ when stopped, ⏸️ when running
- **command_name**: Clickable link to output file (if output_path is set)
- **settings**: ⚙️ icon (only if show_settings=True)

### Properties

- `command_name: str` - The command name
- `output_path: Path | None` - Current output file path
- `is_running: bool` - Whether the command is currently running
- `name: str | None` - Widget name (Textual's widget identification system)

### Methods

#### `set_timer_data(duration_str=None, time_ago_str=None)`
Update timer display with pre-formatted time strings.

```python
# Update duration while running
link.set_timer_data(duration_str="1m 23s")

# Update time-ago after completion
link.set_timer_data(time_ago_str="30s ago")

# Clear timer data
link.set_timer_data(duration_str="", time_ago_str="")
```

**Parameters:**
- `duration_str`: Formatted duration for running commands (e.g., "12m 34s")
- `time_ago_str`: Formatted time-ago for completed commands (e.g., "5s ago")

**Notes:**
- Timer automatically displays duration_str when running=True
- Timer automatically displays time_ago_str when running=False
- Updates every 1 second automatically
- Expects pre-formatted strings (for integration with textual-cmdorc)

#### `set_status(icon=None, running=None, tooltip=None, name_tooltip=None, run_tooltip=None, stop_tooltip=None, append_shortcuts=True)`
Update command status display and optionally update all tooltips at once.

```python
# Basic status update
link.set_status(running=True, tooltip="Running tests...")

# Complete with success
link.set_status(icon="✅", running=False, tooltip="All tests passed")

# Complete with failure
link.set_status(icon="❌", running=False, tooltip="3 tests failed")

# Update status and all tooltips together
link.set_status(
    icon="⏳",
    running=True,
    tooltip="Building project",
    name_tooltip="Project build",
    run_tooltip="Start building",
    stop_tooltip="Stop building"
)
# All tooltips get keyboard shortcuts appended automatically

# Disable keyboard shortcut appending
link.set_status(
    running=True,
    name_tooltip="⚠️ CRITICAL DEPLOY ⚠️",
    run_tooltip="Deploy now",
    stop_tooltip="Abort deployment",
    append_shortcuts=False
)
```

#### `set_output_path(output_path: Path | str | None)`
Update the output file path.

```python
link.set_output_path(Path("output.log"))
link.set_output_path(None)  # Clear output path
```

#### `set_name_tooltip(tooltip: str | None, append_shortcuts: bool = True)`
Set custom tooltip for the command name widget.

```python
# Tooltip with keyboard shortcuts (default)
link.set_name_tooltip("Build the project")
# Shows: "Build the project - Play/Stop (space/p), ..."

# Tooltip without shortcuts
link.set_name_tooltip("Build the project", append_shortcuts=False)
# Shows: "Build the project"

# Reset to default (command name)
link.set_name_tooltip(None)
```

#### `set_play_stop_tooltips(run_tooltip: str | None = None, stop_tooltip: str | None = None, append_shortcuts: bool = True)`
Set custom tooltips for the play/stop button. Tooltips automatically update based on running state.

```python
# Tooltips with keyboard shortcuts (default)
link.set_play_stop_tooltips(
    run_tooltip="Start build",
    stop_tooltip="Cancel build"
)
# Shows: "Start build (space/p)" when not running
#        "Cancel build (space/p)" when running

# Tooltips without shortcuts (useful for critical actions)
link.set_play_stop_tooltips(
    run_tooltip="⚠️ DEPLOY TO PROD ⚠️",
    stop_tooltip="⚠️ STOP DEPLOYMENT ⚠️",
    append_shortcuts=False
)

# Update only one tooltip
link.set_play_stop_tooltips(run_tooltip="Execute")
```

#### `set_settings_tooltip(tooltip: str | None, append_shortcuts: bool = True)`
Set custom tooltip for the settings icon.

```python
# Tooltip with keyboard shortcuts (default)
link.set_settings_tooltip("Build configuration")
# Shows: "Build configuration (s)"

# Tooltip without shortcuts
link.set_settings_tooltip("Build configuration", append_shortcuts=False)
# Shows: "Build configuration"

# Reset to default
link.set_settings_tooltip(None)
# Shows: "Settings (s)"
```

### Messages

#### `CommandLink.PlayClicked`
Posted when play button (▶️) is clicked.

**Attributes:**
- `widget: CommandLink` - The CommandLink widget that was clicked
- `name: str` - The command name
- `output_path: Path | None` - The output file path (or None if not set)

#### `CommandLink.StopClicked`
Posted when stop button (⏸️) is clicked.

**Attributes:**
- `widget: CommandLink` - The CommandLink widget that was clicked
- `name: str` - The command name
- `output_path: Path | None` - The output file path (or None if not set)

#### `CommandLink.SettingsClicked`
Posted when settings icon (⚙️) is clicked (only if show_settings=True).

**Attributes:**
- `widget: CommandLink` - The CommandLink widget that was clicked
- `name: str` - The command name
- `output_path: Path | None` - The output file path (or None if not set)

#### `CommandLink.OutputClicked`
Posted when command name is clicked (opens output file).

**Attributes:**
- `output_path: Path` - The output file path

### Status Icons

Common status icons for commands:

```python
"○"  # Not run / Unknown
"✅"  # Success / Passed
"❌"  # Failed / Error
"⚠️"  # Warning
"⭐️"  # Skipped
"🔄"  # Needs rerun
"⏹"  # Stopped
```

### Adding Toggle/Remove to CommandLink

CommandLink doesn't have built-in toggle/remove controls. Use FileLinkList to add them:

```python
from textual_filelink import FileLinkList, CommandLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        file_list = FileLinkList(show_toggles=True, show_remove=True)
        
        # Add CommandLinks (must have explicit IDs)
        file_list.add_item(
            CommandLink("Build", id="cmd-build"),
            toggled=True
        )
        file_list.add_item(
            CommandLink("Test", id="cmd-test"),
            toggled=False
        )
        
        yield file_list
```

### Complete Example

```python
from pathlib import Path
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static
from textual_filelink import CommandLink

class CommandRunnerApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    Vertical {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical():
            yield Static("🚀 Command Runner")

            yield CommandLink(
                "Unit Tests",
                initial_status_icon="○",
                initial_status_tooltip="Not run",
                show_settings=True,
                id="unit-tests",
            )

            yield CommandLink(
                "Lint",
                initial_status_icon="○",
                initial_status_tooltip="Not run",
                show_settings=False,
                id="lint",
            )

            yield CommandLink(
                "Build",
                initial_status_icon="○",
                initial_status_tooltip="Not run",
                show_settings=True,
                id="build",
            )

        yield Footer()

    def on_command_link_play_clicked(self, event: CommandLink.PlayClicked):
        link = self.query_one(f"#{event.name}", CommandLink)
        link.set_status(running=True, tooltip=f"Running {event.name}...")
        self.run_worker(self.simulate_command(link, event.name))

    def on_command_link_stop_clicked(self, event: CommandLink.StopClicked):
        link = self.query_one(f"#{event.name}", CommandLink)
        link.set_status(icon="⏹", running=False, tooltip="Stopped")
        self.notify(f"Stopped {event.name}", severity="warning")

    def on_command_link_settings_clicked(self, event: CommandLink.SettingsClicked):
        self.notify(f"Settings for {event.name}")

    async def simulate_command(self, link: CommandLink, name: str):
        await asyncio.sleep(2)
        # Simulate success/failure
        import random
        if random.random() > 0.3:
            link.set_status(icon="✅", running=False, tooltip="Passed")
            link.set_output_path(Path(f"{name.lower().replace(' ', '_')}.log"))
            self.notify(f"{name} passed!", severity="information")
        else:
            link.set_status(icon="❌", running=False, tooltip="Failed")
            self.notify(f"{name} failed!", severity="error")

if __name__ == "__main__":
    CommandRunnerApp().run()
```

## FileLinkList API

`FileLinkList` is a container for managing collections of file link widgets with uniform controls.

### Features
- Automatic scrolling via `VerticalScroll`
- Optional toggle checkboxes for each item
- Optional remove buttons for each item
- ID validation (all items must have explicit IDs, no duplicates)
- Batch operations: `toggle_all()`, `remove_selected()`
- Works with FileLink, FileLinkWithIcons, and CommandLink

### Constructor

```python
FileLinkList(
    *,
    show_toggles: bool = False,
    show_remove: bool = False,
    id: str | None = None,
    classes: str | None = None,
)
```

**Parameters:**
- `show_toggles`: Whether to show toggle checkboxes for all items
- `show_remove`: Whether to show remove buttons for all items
- `id`: Widget ID
- `classes`: CSS classes

### Methods

#### `add_item(item: Widget, *, toggled: bool = False)`
Add an item to the list.

```python
file_list.add_item(FileLink("test.py", id="test-py"), toggled=True)
file_list.add_item(CommandLink("Build", id="cmd-build"))
```

**Raises:**
- `ValueError` if item has no ID or ID is duplicate

#### `remove_item(item: Widget)`
Remove an item from the list.

```python
file_list.remove_item(item)
```

#### `clear_items()`
Remove all items from the list.

```python
file_list.clear_items()
```

#### `toggle_all(value: bool)`
Set all toggle checkboxes to the same value.

```python
file_list.toggle_all(True)   # Check all
file_list.toggle_all(False)  # Uncheck all
```

#### `remove_selected()`
Remove all toggled items from the list.

```python
file_list.remove_selected()
```

#### `get_toggled_items() -> list[Widget]`
Get all currently toggled items.

```python
selected = file_list.get_toggled_items()
for item in selected:
    print(item.path)
```

#### `get_items() -> list[Widget]`
Get all items in the list.

```python
all_items = file_list.get_items()
```

### Properties

- `len(file_list)` - Number of items in the list
- `iter(file_list)` - Iterate over items

### Messages

#### `FileLinkList.ItemToggled`
Posted when an item's toggle state changes.

**Attributes:**
- `item: Widget` - The item that was toggled
- `is_toggled: bool` - New toggle state

#### `FileLinkList.ItemRemoved`
Posted when an item is removed.

**Attributes:**
- `item: Widget` - The item that was removed

### Example

```python
from textual_filelink import FileLinkList, FileLink, CommandLink

class MyApp(App):
    def compose(self) -> ComposeResult:
        file_list = FileLinkList(show_toggles=True, show_remove=True)
        
        # Mix different widget types (all need IDs)
        file_list.add_item(FileLink("test.py", id="test-py"), toggled=True)
        file_list.add_item(FileLink("main.py", id="main-py"))
        file_list.add_item(CommandLink("Build", id="cmd-build"))
        
        yield file_list
    
    def on_mount(self):
        file_list = self.query_one(FileLinkList)
        
        # Batch operations
        file_list.toggle_all(True)
        
        selected = file_list.get_toggled_items()
        self.notify(f"Selected: {len(selected)} items")
```
## FileLinkWithIcons API

`FileLinkWithIcons` composes a FileLink with customizable icon indicators before and after the filename.

### Layout

```
[icons_before] FileLink [icons_after]
```

### Constructor

```python
FileLinkWithIcons(
    path: Path | str,
    display_name: str | None = None,
    *,
    line: int | None = None,
    column: int | None = None,
    command_builder: Callable | None = None,
    icons_before: list[Icon] | None = None,
    icons_after: list[Icon] | None = None,
    name: str | None = None,
    id: str | None = None,
    classes: str | None = None,
    tooltip: str | None = None,
)
```

**Parameters:**
- `path`: Full path to the file
- `display_name`: Text to display for the link. If None, defaults to filename
- `line`: Optional line number to jump to
- `column`: Optional column number to jump to
- `command_builder`: Function to build the editor command
- `icons_before`: Icons to display before the filename (order preserved)
- `icons_after`: Icons to display after the filename (order preserved)
- `name`: Widget name
- `id`: Widget ID
- `classes`: CSS classes
- `tooltip`: Optional tooltip for the entire widget

### Icon Class

Icons are specified using the `Icon` dataclass:

```python
from textual_filelink import Icon

Icon(
    name: str,           # REQUIRED: Unique identifier
    icon: str,           # REQUIRED: Unicode character
    tooltip: str | None = None,
    clickable: bool = False,
    key: str | None = None,
    visible: bool = True,
)
```

**Icon Properties:**
- `name` (str, **required**): Unique identifier for this icon within the widget
- `icon` (str, **required**): Unicode character to display (e.g., "✅", "⚙️", "🔒")
- `tooltip` (str | None): Optional tooltip text shown on hover
- `clickable` (bool): Whether clicking this icon emits IconClicked events (default: False)
- `key` (str | None): Optional keyboard shortcut to trigger this icon (e.g., "1", "s", "ctrl+x")
- `visible` (bool): Whether the icon is initially visible (default: True)

**Icon Validation:**
- Duplicate icon names raise `ValueError`
- Duplicate icon keys raise `ValueError`
- Icon keys cannot conflict with FileLink bindings ("o", "enter")

### Properties

- `path: Path` - The file path
- `line: int | None` - The line number
- `column: int | None` - The column number
- `file_link: FileLink` - The internal FileLink widget (read-only access)

### Methods

#### `update_icon(name: str, **kwargs)`
Update an icon's properties.

```python
widget.update_icon("status", icon="✅", tooltip="Passed")
widget.update_icon("warning", visible=True)
widget.update_icon("lock", clickable=True, key="l")
```

**Updatable properties:** `icon`, `tooltip`, `clickable`, `visible`, `key`

**Raises:**
- `ValueError` if icon name not found or invalid property provided

#### `set_icon_visible(name: str, visible: bool)`
Set icon visibility.

```python
widget.set_icon_visible("warning", True)   # Show
widget.set_icon_visible("warning", False)  # Hide
```

**Raises:**
- `ValueError` if icon name not found

#### `get_icon(name: str) -> Icon | None`
Get icon by name.

```python
icon = widget.get_icon("status")
if icon:
    print(f"Icon: {icon.icon}, Visible: {icon.visible}")
```

### Messages

#### `FileLinkWithIcons.IconClicked`
Posted when a clickable icon is clicked.

**Attributes:**
- `widget: FileLinkWithIcons` - The widget containing the clicked icon
- `path: Path` - The file path associated with the FileLink
- `icon_name: str` - The name identifier of the clicked icon
- `icon_char: str` - The unicode character displayed for the icon

### Icon Examples

#### Basic Icons

```python
from textual_filelink import FileLinkWithIcons, Icon

# Icons before filename
link = FileLinkWithIcons(
    "script.py",
    icons_before=[
        Icon(name="type", icon="🐍", tooltip="Python file"),
        Icon(name="status", icon="✅", tooltip="Validated"),
    ]
)
# Display: 🐍 ✅ script.py

# Icons after filename
link = FileLinkWithIcons(
    "script.py",
    icons_after=[
        Icon(name="size", icon="📊", tooltip="Large file"),
        Icon(name="sync", icon="☁️", tooltip="Synced"),
    ]
)
# Display: script.py 📊 ☁️

# Mixed positions
link = FileLinkWithIcons(
    "script.py",
    icons_before=[
        Icon(name="type", icon="🐍"),
    ],
    icons_after=[
        Icon(name="lock", icon="🔒"),
    ]
)
# Display: 🐍 script.py 🔒
```

#### Clickable Icons

```python
from textual_filelink import FileLinkWithIcons, Icon

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield FileLinkWithIcons(
            "config.json",
            icons_before=[
                Icon(
                    name="edit",
                    icon="✏️",
                    clickable=True,
                    key="e",
                    tooltip="Edit"
                ),
                Icon(
                    name="refresh",
                    icon="🔄",
                    clickable=True,
                    key="r",
                    tooltip="Refresh"
                ),
            ]
        )
    
    def on_file_link_with_icons_icon_clicked(
        self, 
        event: FileLinkWithIcons.IconClicked
    ):
        if event.icon_name == "edit":
            self.notify(f"Editing {event.path.name}")
        elif event.icon_name == "refresh":
            self.notify(f"Refreshing {event.path.name}")
```

#### Dynamic Icon Updates

```python
from textual_filelink import FileLinkWithIcons, Icon

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield FileLinkWithIcons(
            "process.py",
            id="task-file",
            icons_before=[
                Icon(name="status", icon="⏳", tooltip="Pending"),
            ],
            icons_after=[
                Icon(name="result", icon="⚪", visible=False),
            ]
        )
    
    def on_mount(self):
        # Simulate processing
        self.set_timer(2.0, self.complete_task)
    
    def complete_task(self):
        widget = self.query_one("#task-file", FileLinkWithIcons)
        widget.update_icon("status", icon="✓", tooltip="Complete")
        widget.set_icon_visible("result", True)
        widget.update_icon("result", icon="🟢", tooltip="Success")
```

#### Hidden Icons

```python
from textual_filelink import FileLinkWithIcons, Icon

# Start with hidden warning icon
link = FileLinkWithIcons(
    "data.csv",
    id="data-file",
    icons_before=[
        Icon(name="type", icon="📊"),
        Icon(name="warning", icon="⚠️", visible=False),  # Hidden initially
    ]
)

# Show warning later
def show_warning():
    widget = self.query_one("#data-file", FileLinkWithIcons)
    widget.set_icon_visible("warning", True)
    widget.update_icon("warning", tooltip="Validation failed!")
```

### Complete Example

```python
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static
from textual_filelink import FileLinkWithIcons, Icon

class IconFileApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    Vertical {
        width: 80;
        height: auto;
        border: solid green;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical():
            yield Static("📂 Project Files with Icons")
            
            # Python file with status
            yield FileLinkWithIcons(
                Path("main.py"),
                line=42,
                icons_before=[
                    Icon(name="type", icon="🐍", tooltip="Python file"),
                    Icon(name="status", icon="✅", tooltip="All checks passed"),
                ],
                icons_after=[
                    Icon(name="coverage", icon="💯", tooltip="100% coverage"),
                ]
            )
            
            # Config file with clickable edit icon
            yield FileLinkWithIcons(
                Path("config.json"),
                id="config-file",
                icons_before=[
                    Icon(name="type", icon="⚙️", tooltip="Config file"),
                    Icon(
                        name="edit",
                        icon="✏️",
                        clickable=True,
                        key="e",
                        tooltip="Edit config"
                    ),
                ],
                icons_after=[
                    Icon(name="lock", icon="🔒", tooltip="Read-only"),
                ]
            )
            
            # Data file with processing status
            yield FileLinkWithIcons(
                Path("data.csv"),
                id="data-file",
                icons_before=[
                    Icon(name="type", icon="📊", tooltip="Data file"),
                    Icon(name="status", icon="⏳", tooltip="Processing..."),
                ],
                icons_after=[
                    Icon(name="result", icon="⚪", visible=False),
                ]
            )
        
        yield Footer()
    
    def on_mount(self):
        # Simulate processing completion after 3 seconds
        self.set_timer(3.0, self.complete_processing)
    
    def complete_processing(self):
        widget = self.query_one("#data-file", FileLinkWithIcons)
        widget.update_icon("status", icon="✓", tooltip="Processing complete")
        widget.set_icon_visible("result", True)
        widget.update_icon("result", icon="🟢", tooltip="Success")
    
    def on_file_link_with_icons_icon_clicked(
        self, 
        event: FileLinkWithIcons.IconClicked
    ):
        if event.icon_name == "edit":
            self.notify(f"✏️ Editing {event.path.name}")
            # You could open an editor, show a modal, etc.

if __name__ == "__main__":
    IconFileApp().run()
```

## Custom Editor Commands

### Using Built-in Command Builders

```python
from textual_filelink import FileLink

# Set default for all FileLink instances
FileLink.default_command_builder = FileLink.vim_command

# Or per instance
link = FileLink(path, command_builder=FileLink.nano_command)
```

**Available builders:**
- `FileLink.vscode_command` - VSCode (default)
- `FileLink.vim_command` - Vim
- `FileLink.nano_command` - Nano
- `FileLink.eclipse_command` - Eclipse
- `FileLink.copy_path_command` - Copy path to clipboard

### Custom Command Builder

```python
def my_editor_command(path: Path, line: int | None, column: int | None) -> list[str]:
    """Build command for my custom editor."""
    cmd = ["myeditor"]
    if line:
        cmd.extend(["--line", str(line)])
    if column:
        cmd.extend(["--column", str(column)])
    cmd.append(str(path))
    return cmd

link = FileLink(path, command_builder=my_editor_command)
```

## Common Unicode Icons

```python
# Status indicators
"✓"  # Success/Complete
"⚠"  # Warning
"✗"  # Error/Failed
"⏳"  # In progress
"🔒"  # Locked
"📝"  # Modified
"➕"  # New/Added
"➖"  # Deleted
"🔄"  # Syncing

# File types
"📄"  # Document
"📁"  # Folder
"🐍"  # Python file
"📊"  # Data file
"⚙️"  # Config file
"🌐"  # Web file
"🎨"  # Image file
"📦"  # Package/Archive

# Actions
"✏️"  # Edit
"👁️"  # View
"🗑️"  # Delete
"💾"  # Save
"📋"  # Copy
"🔍"  # Search

# States
"🟢"  # Success/Green
"🟡"  # Warning/Yellow
"🔴"  # Error/Red
"⚪"  # Neutral/White
"🟣"  # Info/Purple
"⚫"  # Disabled/Black
"💯"  # Perfect score
"○"   # Empty/Not started
```

## Utility Functions

### sanitize_id

```python
from textual_filelink import sanitize_id

# Convert name to valid widget ID
widget_id = sanitize_id("Run Tests")  # Returns: "run-tests"
widget_id = sanitize_id("src/main.py")  # Returns: "src-main-py"
widget_id = sanitize_id("Build Project!")  # Returns: "build-project-"
```

**Description:**
Converts a name to a valid Textual widget ID by:
- Converting to lowercase
- Replacing spaces and path separators with hyphens
- Keeping only alphanumeric characters, hyphens, and underscores

## Development

```bash
# Clone the repository
git clone https://github.com/eyecantell/textual-filelink.git
cd textual-filelink

# Install with dev dependencies
pdm install -d

# Run tests
pdm run pytest

# Run tests with coverage
pdm run pytest --cov

# Lint
pdm run ruff check .

# Format
pdm run ruff format .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) by Textualize
- Inspired by the need for better file navigation in terminal applications

## Links

- **PyPI**: https://pypi.org/project/textual-filelink/
- **GitHub**: https://github.com/eyecantell/textual-filelink
- **Issues**: https://github.com/eyecantell/textual-filelink/issues
- **Changelog**: https://github.com/eyecantell/textual-filelink/blob/main/CHANGELOG.md
- **Textual Documentation**: https://textual.textualize.io/