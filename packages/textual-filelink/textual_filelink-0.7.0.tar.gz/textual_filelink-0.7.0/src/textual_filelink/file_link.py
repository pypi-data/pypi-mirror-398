from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

from textual import events
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Static

from .utils import format_keyboard_shortcuts


class FileLink(Static, can_focus=True):
    """Clickable filename that opens the real file using a configurable command.

    Event Bubbling Policy
    ---------------------
    - Internal click handlers stop event propagation with event.stop()
    - Widget-specific messages (Clicked) bubble up by default
    - Parent containers can handle or stop these messages as needed
    """

    BINDINGS = [
        Binding("enter", "open_file", "Open file", show=False),
        Binding("o", "open_file", "Open file", show=False),
    ]

    DEFAULT_CSS = """
    FileLink {
        width: auto;
        height: 1;
        color: $primary;
        text-style: underline;
        background: transparent;
        padding: 0;
        border: none;
    }
    FileLink:hover {
        text-style: bold underline;
        background: $boost;
    }
    FileLink:focus {
        background: $accent 30%;
    }
    """

    # Class-level default command builder
    default_command_builder: Callable | None = None

    class Opened(Message):
        """Posted after the file is opened.

        Attributes
        ----------
        widget : FileLink
            The FileLink widget that was opened.
        path : Path
            The file path that was opened.
        line : int | None
            The line number to navigate to, or None.
        column : int | None
            The column number to navigate to, or None.
        """

        def __init__(self, widget: FileLink, path: Path, line: int | None, column: int | None) -> None:
            super().__init__()
            self.widget = widget
            self.path = path
            self.line = line
            self.column = column

    # Backwards compatibility (will be removed in future versions)
    Clicked = Opened

    # Class-level default open keys
    DEFAULT_OPEN_KEYS = ["enter", "o"]

    def __init__(
        self,
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
    ) -> None:
        """
        Parameters
        ----------
        path : Path | str
            Full path to the file.
        display_name : str | None
            Text to display for the link. If None, defaults to the filename (path.name).
        line, column : int | None
            Optional cursor position to jump to.
        command_builder : Callable | None
            Function that takes (path, line, column) and returns a list of command arguments.
            If None, uses the class-level default_command_builder.
            If that's also None, uses VSCode's 'code --goto' command.
        open_keys : list[str] | None
            Custom keyboard shortcuts for opening the file. If None, uses DEFAULT_OPEN_KEYS.
            Example: ["f2"] or ["ctrl+o", "enter"]
        id : str | None
            Widget ID. If None, auto-generates from filename using sanitize_id().
            Example: "README.md" becomes "readme-md".
            Note: If you have multiple FileLinks with the same filename, provide explicit IDs.
        _embedded : bool
            Internal use only. If True, disables focus to prevent stealing focus from parent widget.
        tooltip : str | None
            Optional tooltip text. If provided, will be enhanced with keyboard shortcuts.
        """
        self._path = Path(path).resolve()
        self._display_name = display_name or self._path.name
        self._line = line
        self._column = column
        self._command_builder = command_builder

        # Store custom open keys if provided (will be applied in on_mount)
        self._custom_open_keys = open_keys

        # Auto-generate ID from filename if not provided
        if id is None:
            from .utils import sanitize_id

            id = sanitize_id(self._path.name)

        # Initialize Static with the display name as content
        super().__init__(
            self._display_name,
            name=name,
            id=id,
            classes=classes,
        )

        # Disable focus if embedded in parent widget to prevent focus stealing
        if _embedded:
            self.can_focus = False
        else:
            # Set enhanced tooltip for standalone FileLink
            default_tooltip = f"Open {self._path.name}"
            enhanced = self._enhance_tooltip(tooltip or default_tooltip, "open_file")
            self.tooltip = enhanced

    # ------------------------------------------------------------------ #
    # Keyboard handling
    # ------------------------------------------------------------------ #
    def on_mount(self) -> None:
        """Apply custom open_keys bindings at runtime."""
        if self._custom_open_keys is not None:
            for key in self._custom_open_keys:
                self._bindings.bind(key, "open_file", "Open file", show=False)

    def action_open_file(self) -> None:
        """Open file via keyboard (reuses existing click logic)."""
        self.open_file()

    def open_file(self) -> None:
        """Open the file in the configured editor.

        This is the public API method that can be called programmatically.
        It opens the file and posts the Opened message.
        """
        self._do_open_file()
        self.post_message(self.Opened(self, self._path, self._line, self._column))

    def _get_keys_for_action(self, action_name: str) -> list[str]:
        """Get all keys bound to an action.

        Args:
            action_name: The action name (e.g., 'open_file', 'toggle')

        Returns:
            List of key names bound to the action (e.g., ['o'], ['space', 't'])
        """
        # For open_file action, return custom keys if set
        if action_name == "open_file" and hasattr(self, "_custom_open_keys") and self._custom_open_keys is not None:
            return self._custom_open_keys

        # Otherwise, use class-level BINDINGS
        keys = []
        for binding in self.BINDINGS:
            if binding.action == action_name:
                keys.append(binding.key)
        return keys

    def _enhance_tooltip(self, base_tooltip: str | None, action_name: str) -> str:
        """Enhance tooltip with keyboard shortcut hints.

        Args:
            base_tooltip: The base tooltip text (or None)
            action_name: The action name to get keys for

        Returns:
            Enhanced tooltip with keyboard shortcuts appended

        Examples:
            _enhance_tooltip("Click to toggle", "toggle")
            → "Click to toggle (space/t)"

            _enhance_tooltip(None, "open_file")
            → "Open file (o)"
        """
        keys = self._get_keys_for_action(action_name)

        if not keys:
            # No keys bound, return base tooltip or empty string
            return base_tooltip or ""

        # Format keys using centralized utility
        key_hint = format_keyboard_shortcuts(keys)

        # If no base tooltip, generate sensible default
        if not base_tooltip:
            # Convert action_name to readable text
            # "open_file" → "Open file"
            # "play_stop" → "Play/Stop"
            readable = action_name.replace("_", " ").title()
            base_tooltip = readable

        return f"{base_tooltip} {key_hint}"

    # ------------------------------------------------------------------ #
    # Mouse handling for clickability
    # ------------------------------------------------------------------ #
    def on_click(self, event: events.Click) -> None:
        """Handle click event."""
        event.stop()
        self.open_file()

    def _do_open_file(self) -> None:
        """Open the file (shared logic for click and keyboard activation)."""
        # Determine which command builder to use
        command_builder = self._command_builder or self.default_command_builder or self.vscode_command

        # Open the file directly (it's fast enough not to block)
        try:
            cmd = command_builder(self._path, self._line, self._column)

            result = subprocess.run(
                cmd, env=os.environ.copy(), cwd=str(Path.cwd()), capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                self.app.notify(f"Opened {self._path.name}", title="FileLink", timeout=1.5)
            else:
                error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
                self.app.notify(f"Failed to open {self._path.name}: {error_msg}", severity="error", timeout=3)

        except subprocess.TimeoutExpired:
            self.app.notify(f"Timeout opening {self._path.name}", severity="error", timeout=3)
        except Exception as exc:
            self.app.notify(f"Failed to open {self._path.name}: {exc}", severity="error", timeout=3)

    # ------------------------------------------------------------------ #
    # Default command builders
    # ------------------------------------------------------------------ #
    @staticmethod
    def vscode_command(path: Path, line: int | None, column: int | None) -> list[str]:
        """Build VSCode 'code --goto' command."""
        try:
            cwd = Path.cwd()
            relative_path = path.relative_to(cwd)
            file_arg = str(relative_path)
        except ValueError:
            file_arg = str(path)

        if line is not None:
            goto_arg = f"{file_arg}:{line}"
            if column is not None:
                goto_arg += f":{column}"
        else:
            goto_arg = file_arg

        return ["code", "--goto", goto_arg]

    @staticmethod
    def vim_command(path: Path, line: int | None, column: int | None) -> list[str]:
        """Build vim command."""
        cmd = ["vim"]
        if line is not None:
            if column is not None:
                cmd.append(f"+call cursor({line},{column})")
            else:
                cmd.append(f"+{line}")
        cmd.append(str(path))
        return cmd

    @staticmethod
    def nano_command(path: Path, line: int | None, column: int | None) -> list[str]:
        """Build nano command."""
        cmd = ["nano"]
        if line is not None:
            if column is not None:
                cmd.append(f"+{line},{column}")
            else:
                cmd.append(f"+{line}")
        cmd.append(str(path))
        return cmd

    @staticmethod
    def eclipse_command(path: Path, line: int | None, column: int | None) -> list[str]:
        """Build Eclipse command."""
        cmd = ["eclipse"]
        if line is not None:
            cmd.extend(["--launcher.openFile", f"{path}:{line}"])
        else:
            cmd.extend(["--launcher.openFile", str(path)])
        return cmd

    @staticmethod
    def copy_path_command(path: Path, line: int | None, column: int | None) -> list[str]:
        """Copy the full path (with line:column) to clipboard."""
        import platform

        path_str = str(path)
        if line is not None:
            path_str += f":{line}"
            if column is not None:
                path_str += f":{column}"

        system = platform.system()
        if system == "Darwin":
            return ["bash", "-c", f"echo -n '{path_str}' | pbcopy"]
        elif system == "Windows":
            return ["cmd", "/c", f"echo {path_str} | clip"]
        else:
            return [
                "bash",
                "-c",
                f"echo -n '{path_str}' | xclip -selection clipboard 2>/dev/null || echo -n '{path_str}' | xsel --clipboard",
            ]

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def path(self) -> Path:
        """Get the file path."""
        return self._path

    @property
    def display_name(self) -> str:
        """Get the display name."""
        return self._display_name

    @property
    def line(self) -> int | None:
        """Get the line number."""
        return self._line

    @property
    def column(self) -> int | None:
        """Get the column number."""
        return self._column
