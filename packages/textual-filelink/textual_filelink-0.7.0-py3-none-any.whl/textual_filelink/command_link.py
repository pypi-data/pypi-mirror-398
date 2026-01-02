"""CommandLink widget - Command orchestration with status display (v0.4.0 refactor)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Static

from .file_link import FileLink
from .utils import format_keyboard_shortcuts, sanitize_id


class CommandLink(Horizontal, can_focus=True):
    """Command orchestration widget with status, play/stop, optional timer, and settings.

    Flat architecture (no inheritance), builds own layout:
    [status/spinner] [timer?] [▶️/⏹️] name [⚙️?]

    Toggle and remove controls are added by FileLinkList, not by CommandLink itself.

    Timer Display
    -------------
    When show_timer=True, displays elapsed time or time-ago in a fixed-width column:
    - Running command: shows duration (e.g., "12m 34s")
    - Completed command: shows time ago (e.g., "5s ago")
    - Updates automatically every 1 second
    - Use set_timer_data() to provide formatted time strings

    Event Bubbling Policy
    ---------------------
    - Internal click handlers stop event propagation
    - Command messages (PlayClicked, StopClicked, etc.) bubble up by default
    - Parent containers can handle or stop these messages as needed

    Example
    -------
    >>> link = CommandLink(
    ...     "Tests",
    ...     initial_status_icon="❓",
    ...     initial_status_tooltip="Not run",
    ...     show_timer=True,
    ... )
    >>> link.set_status(running=True, tooltip="Running...")
    >>> link.set_timer_data(duration_str="1m 23s")
    >>> link.set_status(icon="✅", running=False, tooltip="Passed")
    >>> link.set_timer_data(time_ago_str="30s ago")
    """

    DEFAULT_CSS = """
    CommandLink {
        width: auto;
        height: auto;
        padding: 0 1;
        border: none;
    }
    CommandLink > .status-icon {
        width: auto;
        height: 1;
        padding: 0 1;
    }
    CommandLink > .timer-display {
        width: auto;
        height: 1;
        padding: 0 1;
        color: $text-muted;
    }
    CommandLink > .play-stop-button {
        width: auto;
        height: 1;
        padding: 0 1;
        color: $primary;
    }
    CommandLink > .play-stop-button:hover {
        text-style: bold;
        background: $boost;
    }
    CommandLink > .settings-icon {
        width: auto;
        height: 1;
        padding: 0 1;
        color: $primary;
    }
    CommandLink > .settings-icon:hover {
        text-style: bold;
        background: $boost;
    }
    CommandLink:focus {
        background: $accent 20%;
    }
    CommandLink > .command-name {
        width: auto;
        height: 1;
        padding: 0 1;
    }
    CommandLink > FileLink {
        width: auto;
        height: 1;
        padding: 0 1;
    }
    """

    # Default spinner frames and interval for animation
    DEFAULT_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    DEFAULT_SPINNER_INTERVAL = 0.1  # seconds

    class PlayClicked(Message):
        """Posted when play button clicked.

        Attributes
        ----------
        widget : CommandLink
            The CommandLink widget that was clicked.
        name : str
            Command name.
        output_path : Path | None
            Output file path if set.
        """

        def __init__(self, widget: CommandLink, name: str, output_path: Path | None) -> None:
            super().__init__()
            self.widget = widget
            self.name = name
            self.output_path = output_path

    class StopClicked(Message):
        """Posted when stop button clicked.

        Attributes
        ----------
        widget : CommandLink
            The CommandLink widget that was clicked.
        name : str
            Command name.
        output_path : Path | None
            Output file path if set.
        """

        def __init__(self, widget: CommandLink, name: str, output_path: Path | None) -> None:
            super().__init__()
            self.widget = widget
            self.name = name
            self.output_path = output_path

    class SettingsClicked(Message):
        """Posted when settings icon clicked.

        Attributes
        ----------
        widget : CommandLink
            The CommandLink widget that was clicked.
        name : str
            Command name.
        output_path : Path | None
            Output file path if set.
        """

        def __init__(self, widget: CommandLink, name: str, output_path: Path | None) -> None:
            super().__init__()
            self.widget = widget
            self.name = name
            self.output_path = output_path

    class OutputClicked(Message):
        """Posted when command name clicked (opens output).

        Attributes
        ----------
        output_path : Path
            Output file path.
        """

        def __init__(self, output_path: Path) -> None:
            super().__init__()
            self.output_path = output_path

    # Default keyboard shortcuts
    DEFAULT_OPEN_KEYS = ["enter", "o"]
    DEFAULT_PLAY_STOP_KEYS = ["space", "p"]
    DEFAULT_SETTINGS_KEYS = ["s"]

    def __init__(
        self,
        command_name: str,
        *,
        output_path: Path | str | None = None,
        command_builder: Callable | None = None,
        initial_status_icon: str = "❓",
        initial_status_tooltip: str | None = None,
        show_settings: bool = False,
        show_timer: bool = False,
        timer_field_width: int = 12,
        tooltip: str | None = None,
        open_keys: list[str] | None = None,
        play_stop_keys: list[str] | None = None,
        settings_keys: list[str] | None = None,
        spinner_frames: list[str] | None = None,
        spinner_interval: float = 0.1,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        command_name : str
            Command name to display.
        output_path : Path | str | None
            Optional output file path. If set, clicking name opens the file.
        command_builder : Callable | None
            Optional command builder for opening output files.
        initial_status_icon : str
            Initial status icon (default: "❓").
        initial_status_tooltip : str | None
            Initial tooltip for status icon.
        show_settings : bool
            Whether to show settings icon (default: False).
        show_timer : bool
            Whether to show elapsed/time-ago timer in a fixed-width field (default: False).
        timer_field_width : int
            Fixed width of the timing column in characters (default: 12).
        tooltip : str | None
            Custom tooltip text for the command name. If provided, keyboard shortcuts
            will be appended. If None, uses command name as base.
        open_keys : list[str] | None
            Custom keyboard shortcuts for opening output. If None, uses DEFAULT_OPEN_KEYS.
        play_stop_keys : list[str] | None
            Custom keyboard shortcuts for play/stop. If None, uses DEFAULT_PLAY_STOP_KEYS.
        settings_keys : list[str] | None
            Custom keyboard shortcuts for settings. If None, uses DEFAULT_SETTINGS_KEYS.
        spinner_frames : list[str] | None
            Custom spinner animation frames (unicode characters).
            If None, uses DEFAULT_SPINNER_FRAMES (Braille pattern).
            Example: ["◐", "◓", "◑", "◒"] for circle spinner
        spinner_interval : float
            Seconds between spinner frame updates. Default: 0.1
            Lower values = faster spin. Example: 0.05 for 2x speed
        name : str | None
            Widget name for Textual's widget identification system (optional).
        id : str | None
            Widget ID. If None, auto-generated from command_name via sanitize_id().
        classes : str | None
            CSS classes.
        """
        self._command_name = command_name
        self._output_path = Path(output_path).resolve() if output_path else None
        self._command_builder = command_builder
        self._show_settings = show_settings
        self._show_timer = show_timer
        self._timer_field_width = timer_field_width
        self._custom_tooltip = tooltip  # Use _custom_tooltip to avoid conflict with Textual's _tooltip

        # Store custom keyboard shortcuts
        self._custom_open_keys = open_keys
        self._custom_play_stop_keys = play_stop_keys
        self._custom_settings_keys = settings_keys

        # Status state
        self._status_icon = initial_status_icon
        self._status_tooltip = initial_status_tooltip
        self._command_running = False

        # Custom tooltips for play/stop button (will be used if set)
        self._custom_run_tooltip: str | None = None
        self._custom_stop_tooltip: str | None = None
        self._custom_settings_tooltip: str | None = None

        # Spinner configuration and state
        self._spinner_frames = spinner_frames if spinner_frames is not None else self.DEFAULT_SPINNER_FRAMES
        self._spinner_interval = spinner_interval
        self._spinner_frame_index = 0
        self._spinner_timer = None

        # Timer state for elapsed/time-ago display
        self._timer_duration_str: str | None = None
        self._timer_time_ago_str: str | None = None
        self._timer_update_interval = None
        self._last_timer_display: str = ""  # Track last displayed timer to avoid unnecessary refreshes

        # Auto-generate ID if not provided
        widget_id = id or sanitize_id(command_name)

        # Initialize container
        super().__init__(
            name=name,
            id=widget_id,
            classes=classes,
        )

        # Create child widgets
        self._status_widget = Static(self._status_icon, classes="status-icon")
        if self._status_tooltip:
            self._status_widget.tooltip = self._status_tooltip

        # Timer widget (only created if show_timer is True)
        if self._show_timer:
            self._timer_widget = Static("", classes="timer-display")
            # Initial render of timer (empty or with current data)
            self._update_timer_display()

        # Play/stop button
        self._play_stop_widget = Static("▶️", classes="play-stop-button")
        self._play_stop_widget.tooltip = self._custom_run_tooltip or "Run command (space/p)"
        self._play_stop_widget._is_play_button = True  # type: ignore

        # Name (FileLink if output_path, Static otherwise)
        if self._output_path:
            self._name_widget = FileLink(
                self._output_path,
                display_name=self._command_name,
                command_builder=self._command_builder,
                _embedded=True,
            )
        else:
            self._name_widget = Static(self._command_name, classes="command-name")

        # Set tooltip on name widget with available keyboard shortcuts
        self._build_tooltip_with_shortcuts()

        # Settings icon (optional)
        if self._show_settings:
            self._settings_widget = Static("⚙️", classes="settings-icon")
            self._settings_widget.tooltip = self._custom_settings_tooltip or "Settings (s)"

    def compose(self):
        """Compose widget layout."""
        yield self._status_widget
        if self._show_timer:
            yield self._timer_widget
        yield self._play_stop_widget
        yield self._name_widget
        if self._show_settings:
            yield self._settings_widget

    def on_mount(self) -> None:
        """Set up runtime keyboard bindings and timer interval."""
        # Open output bindings (only if output_path is set)
        if self._output_path:
            open_keys = self._custom_open_keys if self._custom_open_keys is not None else self.DEFAULT_OPEN_KEYS
            for key in open_keys:
                self._bindings.bind(key, "open_output", "Open output", show=False)

        # Play/stop bindings
        play_stop_keys = (
            self._custom_play_stop_keys if self._custom_play_stop_keys is not None else self.DEFAULT_PLAY_STOP_KEYS
        )
        for key in play_stop_keys:
            self._bindings.bind(key, "play_stop", "Play/Stop", show=False)

        # Settings bindings (if enabled)
        if self._show_settings:
            settings_keys = (
                self._custom_settings_keys if self._custom_settings_keys is not None else self.DEFAULT_SETTINGS_KEYS
            )
            for key in settings_keys:
                self._bindings.bind(key, "settings", "Settings", show=False)

        # Timer update interval (if enabled)
        if self._show_timer:
            self._timer_update_interval = self.set_interval(1.0, self._update_timer_display)

    def on_unmount(self) -> None:
        """Clean up timer interval when widget is unmounted."""
        # Stop timer update interval if running
        if self._timer_update_interval:
            self._timer_update_interval.stop()
            self._timer_update_interval = None

    def on_click(self, event) -> None:
        """Handle clicks on child widgets."""
        event.stop()

        # Play/stop button
        if hasattr(event.widget, "_is_play_button"):
            if self._command_running:
                self.post_message(self.StopClicked(self, self._command_name, self._output_path))
            else:
                self.post_message(self.PlayClicked(self, self._command_name, self._output_path))

        # Settings icon
        elif event.widget == self._settings_widget if self._show_settings else False:
            self.post_message(self.SettingsClicked(self, self._command_name, self._output_path))

    def on_file_link_opened(self, event: FileLink.Opened) -> None:
        """Handle FileLink.Opened from embedded name widget."""
        # Re-post as OutputClicked for consistency
        if self._output_path:
            self.post_message(self.OutputClicked(self._output_path))

    # ------------------------------------------------------------------ #
    # Keyboard actions
    # ------------------------------------------------------------------ #
    def action_open_output(self) -> None:
        """Open output file (if set)."""
        if self._output_path and isinstance(self._name_widget, FileLink):
            self._name_widget.action_open_file()

    def action_play_stop(self) -> None:
        """Toggle play/stop."""
        if self._command_running:
            self.post_message(self.StopClicked(self, self._command_name, self._output_path))
        else:
            self.post_message(self.PlayClicked(self, self._command_name, self._output_path))

    def action_settings(self) -> None:
        """Open settings."""
        if self._show_settings:
            self.post_message(self.SettingsClicked(self, self._command_name, self._output_path))

    # ------------------------------------------------------------------ #
    # Helper methods
    # ------------------------------------------------------------------ #
    def _build_tooltip_with_shortcuts(self) -> None:
        """Build and set tooltip on name widget showing description with keyboard shortcuts."""
        shortcuts_str = self._get_shortcuts_string()

        # Build tooltip: use custom tooltip or command name as base
        base = self._custom_tooltip if self._custom_tooltip else self._command_name
        tooltip = f"{base} - {shortcuts_str}" if shortcuts_str else base

        self._name_widget.tooltip = tooltip

    def _get_shortcuts_string(self) -> str:
        """Get keyboard shortcuts as a formatted string.

        Returns
        -------
        str
            Comma-separated shortcuts, e.g., "Play/Stop (space/p), Settings (s)"
        """
        shortcuts = []

        # Add output opening if available
        if self._output_path:
            open_keys = self._custom_open_keys or self.DEFAULT_OPEN_KEYS
            shortcuts.append(f"Open output {format_keyboard_shortcuts(open_keys)}")

        # Add play/stop
        play_stop_keys = self._custom_play_stop_keys or self.DEFAULT_PLAY_STOP_KEYS
        shortcuts.append(f"Play/Stop {format_keyboard_shortcuts(play_stop_keys)}")

        # Add settings if available
        if self._show_settings:
            settings_keys = self._custom_settings_keys or self.DEFAULT_SETTINGS_KEYS
            shortcuts.append(f"Settings {format_keyboard_shortcuts(settings_keys)}")

        return ", ".join(shortcuts)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def set_status(
        self,
        *,
        icon: str | None = None,
        running: bool | None = None,
        tooltip: str | None = None,
        name_tooltip: str | None = None,
        run_tooltip: str | None = None,
        stop_tooltip: str | None = None,
        append_shortcuts: bool = True,
    ) -> None:
        """Update command status and optionally update tooltips.

        Parameters
        ----------
        icon : str | None
            New status icon. If None, keeps current icon.
        running : bool | None
            Whether command is running. If True, starts spinner.
        tooltip : str | None
            New tooltip for status icon.
        name_tooltip : str | None
            New tooltip for command name widget. Keyboard shortcuts appended based on append_shortcuts.
        run_tooltip : str | None
            New tooltip for play button (when not running).
        stop_tooltip : str | None
            New tooltip for stop button (when running).
        append_shortcuts : bool
            Whether to append keyboard shortcuts to name/run/stop tooltips. Default: True.

        Examples
        --------
        >>> # Basic status update
        >>> link.set_status(running=True, tooltip="Running...")

        >>> # Update status and tooltips together
        >>> link.set_status(
        ...     icon="✅",
        ...     running=False,
        ...     tooltip="Passed",
        ...     name_tooltip="Build successful"
        ... )

        >>> # Update all tooltips when transitioning states
        >>> link.set_status(
        ...     running=True,
        ...     tooltip="Building...",
        ...     run_tooltip="Start build",
        ...     stop_tooltip="Cancel build"
        ... )
        """
        # Update status icon
        if icon is not None:
            self._status_icon = icon
            # Update widget display (spinner will override if running)
            self._status_widget.update(icon)

        # Update status tooltip
        if tooltip is not None:
            self._status_tooltip = tooltip
            self._status_widget.tooltip = tooltip

        # Update name tooltip if provided
        if name_tooltip is not None:
            self.set_name_tooltip(name_tooltip, append_shortcuts=append_shortcuts)

        # Update play/stop tooltips if provided
        if run_tooltip is not None or stop_tooltip is not None:
            self.set_play_stop_tooltips(
                run_tooltip=run_tooltip,
                stop_tooltip=stop_tooltip,
                append_shortcuts=append_shortcuts,
            )

        # Update running state
        if running is not None:
            was_running = self._command_running
            self._command_running = running

            # Update play/stop button
            if running:
                self._play_stop_widget.update("⏹️")
                self._play_stop_widget.tooltip = self._custom_stop_tooltip or "Stop command (space/p)"
            else:
                self._play_stop_widget.update("▶️")
                self._play_stop_widget.tooltip = self._custom_run_tooltip or "Run command (space/p)"

            # Manage spinner
            if running and not was_running:
                # Start spinner
                self._spinner_frame_index = 0
                self._spinner_timer = self.set_interval(self._spinner_interval, self._animate_spinner)
            elif not running and was_running:
                # Stop spinner, show final icon
                if self._spinner_timer:
                    self._spinner_timer.stop()
                    self._spinner_timer = None
                self._status_widget.update(self._status_icon)

            # Update timer display when running state changes
            self._update_timer_display()

    def set_timer_data(
        self,
        *,
        duration_str: str | None = None,
        time_ago_str: str | None = None,
    ) -> None:
        """Update timer display with formatted time strings.

        Parameters
        ----------
        duration_str : str | None
            Formatted duration string for running commands (e.g., "12m 34s").
            If None, keeps current duration string.
        time_ago_str : str | None
            Formatted time-ago string for completed commands (e.g., "5s ago").
            If None, keeps current time-ago string.

        Examples
        --------
        >>> # Update duration while running
        >>> link.set_timer_data(duration_str="1m 23s")

        >>> # Update time-ago after completion
        >>> link.set_timer_data(time_ago_str="30s ago")

        >>> # Clear timer data
        >>> link.set_timer_data(duration_str="", time_ago_str="")

        Notes
        -----
        This method expects pre-formatted strings from external sources (e.g., textual-cmdorc's
        RunHandle). It does not perform any time formatting itself. The display will automatically
        choose between duration_str (when running) and time_ago_str (when not running).
        """
        if duration_str is not None:
            self._timer_duration_str = duration_str
        if time_ago_str is not None:
            self._timer_time_ago_str = time_ago_str

        # Update display immediately
        self._update_timer_display()

    def set_output_path(self, output_path: Path | str | None) -> None:
        """Set or update the output file path.

        Parameters
        ----------
        output_path : Path | str | None
            New output path. If None, removes output path.
        """
        self._output_path = Path(output_path).resolve() if output_path else None

        # Update name widget if needed
        if self._output_path and not isinstance(self._name_widget, FileLink):
            # Replace Static with FileLink
            self._name_widget.remove()
            self._name_widget = FileLink(
                self._output_path,
                display_name=self._command_name,
                command_builder=self._command_builder,
                _embedded=True,
            )
            # Mount before settings widget if it exists, otherwise at end
            if self._show_settings:
                self.mount(self._name_widget, before=self._settings_widget)
            else:
                self.mount(self._name_widget)

        # Update tooltip to reflect new output path availability
        self._build_tooltip_with_shortcuts()

    def set_name_tooltip(self, tooltip: str | None, append_shortcuts: bool = True) -> None:
        """Set custom tooltip for the command name widget.

        Parameters
        ----------
        tooltip : str | None
            Custom tooltip text. If None, uses command name as base.
        append_shortcuts : bool
            Whether to automatically append keyboard shortcuts to the tooltip.
            Default is True.

        Examples
        --------
        >>> link.set_name_tooltip("Build project")  # Shows "Build project - Play/Stop (space/p), ..."
        >>> link.set_name_tooltip("Build project", append_shortcuts=False)  # Shows "Build project"
        """
        self._custom_tooltip = tooltip
        if append_shortcuts:
            self._build_tooltip_with_shortcuts()
        else:
            # Set tooltip directly without shortcuts
            base = self._custom_tooltip if self._custom_tooltip else self._command_name
            self._name_widget.tooltip = base

    def set_play_stop_tooltips(
        self,
        *,
        run_tooltip: str | None = None,
        stop_tooltip: str | None = None,
        append_shortcuts: bool = True,
    ) -> None:
        """Set custom tooltips for play/stop button.

        Parameters
        ----------
        run_tooltip : str | None
            Tooltip shown when button is in "play" state (command not running).
            If None, keeps current run tooltip.
        stop_tooltip : str | None
            Tooltip shown when button is in "stop" state (command running).
            If None, keeps current stop tooltip.
        append_shortcuts : bool
            Whether to automatically append keyboard shortcuts to the tooltips.
            Default is True.

        Examples
        --------
        >>> link.set_play_stop_tooltips(
        ...     run_tooltip="Start build",
        ...     stop_tooltip="Cancel build"
        ... )  # Shows "Start build (space/p)" and "Cancel build (space/p)"
        >>> link.set_play_stop_tooltips(
        ...     run_tooltip="Start build",
        ...     stop_tooltip="Cancel build",
        ...     append_shortcuts=False
        ... )  # Shows "Start build" and "Cancel build"
        """
        # Get the play/stop keys for formatting
        play_stop_keys = self._custom_play_stop_keys or self.DEFAULT_PLAY_STOP_KEYS
        shortcuts_str = format_keyboard_shortcuts(play_stop_keys) if append_shortcuts else ""

        if run_tooltip is not None:
            if append_shortcuts and shortcuts_str:
                self._custom_run_tooltip = f"{run_tooltip} {shortcuts_str}"
            else:
                self._custom_run_tooltip = run_tooltip

        if stop_tooltip is not None:
            if append_shortcuts and shortcuts_str:
                self._custom_stop_tooltip = f"{stop_tooltip} {shortcuts_str}"
            else:
                self._custom_stop_tooltip = stop_tooltip

        # Update current tooltip based on running state
        if self._command_running:
            self._play_stop_widget.tooltip = self._custom_stop_tooltip or "Stop command (space/p)"
        else:
            self._play_stop_widget.tooltip = self._custom_run_tooltip or "Run command (space/p)"

    def set_settings_tooltip(self, tooltip: str | None, append_shortcuts: bool = True) -> None:
        """Set custom tooltip for settings icon.

        Parameters
        ----------
        tooltip : str | None
            Custom tooltip text. If None, uses default "Settings (s)".
        append_shortcuts : bool
            Whether to automatically append keyboard shortcuts to the tooltip.
            Default is True.

        Examples
        --------
        >>> link.set_settings_tooltip("Build options")  # Shows "Build options (s)"
        >>> link.set_settings_tooltip("Build options", append_shortcuts=False)  # Shows "Build options"
        """
        if tooltip is not None:
            settings_keys = self._custom_settings_keys or self.DEFAULT_SETTINGS_KEYS
            shortcuts_str = format_keyboard_shortcuts(settings_keys) if append_shortcuts else ""

            if append_shortcuts and shortcuts_str:
                self._custom_settings_tooltip = f"{tooltip} {shortcuts_str}"
            else:
                self._custom_settings_tooltip = tooltip
        else:
            self._custom_settings_tooltip = None

        if self._show_settings:
            self._settings_widget.tooltip = self._custom_settings_tooltip or "Settings (s)"

    def _animate_spinner(self) -> None:
        """Animate the spinner (called by timer)."""
        if self._command_running:
            frame = self._spinner_frames[self._spinner_frame_index]
            self._status_widget.update(frame)
            self._spinner_frame_index = (self._spinner_frame_index + 1) % len(self._spinner_frames)

    def _update_timer_display(self) -> None:
        """Update the timer display widget with current timer data.

        Only updates if the display string has changed to avoid unnecessary refreshes.
        """
        if not self._show_timer:
            return

        # Determine which time string to display
        if self._command_running and self._timer_duration_str:
            # Running: show duration
            time_str = self._timer_duration_str
        elif not self._command_running and self._timer_time_ago_str:
            # Not running with history: show time ago
            time_str = self._timer_time_ago_str
        else:
            # No timer data available
            time_str = ""

        # Right-justify within the fixed width
        padded_time = time_str.rjust(self._timer_field_width)

        # Only update if changed (avoid unnecessary redraws)
        if padded_time != self._last_timer_display:
            self._last_timer_display = padded_time
            self._timer_widget.update(padded_time)

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def command_name(self) -> str:
        """Get the command name.

        Returns
        -------
        str
            The command name displayed in the widget.
        """
        return self._command_name

    @property
    def output_path(self) -> Path | None:
        """Get output file path."""
        return self._output_path

    @property
    def is_running(self) -> bool:
        """Check if command is currently running."""
        return self._command_running
