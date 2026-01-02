"""FileLinkWithIcons widget - Composable file link with icon indicators."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Static

from .file_link import FileLink
from .icon import Icon
from .utils import format_keyboard_shortcuts


class FileLinkWithIcons(Horizontal, can_focus=True):
    """FileLink with customizable icon indicators before and after the filename.

    Composes a FileLink with icon lists using a horizontal layout:
    [icons_before] FileLink [icons_after]

    Icons can be:
    - Visible/hidden dynamically via set_icon_visible()
    - Updated dynamically via update_icon()
    - Clickable (emits IconClicked message)
    - Keyboard accessible (if icon.key is set)

    Event Bubbling Policy
    ---------------------
    - IconClicked messages bubble up by default
    - Internal FileLink.Opened messages bubble through this widget
    - Parent containers can handle or stop these messages as needed
    """

    DEFAULT_CSS = """
    FileLinkWithIcons {
        width: auto;
        height: auto;
        padding: 0;
        border: none;
    }
    FileLinkWithIcons:focus {
        background: $accent 30%;
    }
    FileLinkWithIcons > .icon-widget {
        width: auto;
        height: 1;
        padding: 0 1;
        border: none;
        background: transparent;
    }
    FileLinkWithIcons > .icon-widget.clickable {
        color: $primary;
    }
    FileLinkWithIcons > .icon-widget.clickable:hover {
        text-style: bold;
        background: $boost;
    }
    """

    BINDINGS = [
        Binding("enter", "open_file", "Open file", show=False),
        Binding("o", "open_file", "Open file", show=False),
    ]

    class IconClicked(Message):
        """Posted when a clickable icon is clicked.

        Attributes
        ----------
        widget : FileLinkWithIcons
            The widget that contains the clicked icon.
        path : Path
            The file path associated with the FileLink.
        icon_name : str
            The name identifier of the clicked icon.
        icon_char : str
            The unicode character displayed for the icon.
        """

        def __init__(
            self,
            widget: FileLinkWithIcons,
            path: Path,
            icon_name: str,
            icon_char: str,
        ) -> None:
            super().__init__()
            self.widget = widget
            self.path = path
            self.icon_name = icon_name
            self.icon_char = icon_char

    def __init__(
        self,
        path: Path | str,
        display_name: str | None = None,
        *,
        line: int | None = None,
        column: int | None = None,
        command_builder: Callable | None = None,
        icons_before: list[Icon] | None = None,
        icons_after: list[Icon] | None = None,
        open_keys: list[str] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        tooltip: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        path : Path | str
            Full path to the file.
        display_name : str | None
            Text to display for the link. If None, defaults to the filename.
        line, column : int | None
            Optional cursor position to jump to.
        command_builder : Callable | None
            Function that takes (path, line, column) and returns command arguments.
        icons_before : list[Icon] | None
            Icons to display before the filename. Order is preserved.
        icons_after : list[Icon] | None
            Icons to display after the filename. Order is preserved.
        open_keys : list[str] | None
            Custom keyboard shortcuts for opening the file. If None, uses ["enter", "o"].
            Example: ["f2"] or ["ctrl+o", "enter"]
        id : str | None
            Widget ID. If None, auto-generates from filename using sanitize_id().
            Example: "README.md" becomes "readme-md".
            Note: If you have multiple FileLinkWithIcons with the same filename, provide explicit IDs.
        name, classes : str | None
            Standard Textual widget parameters.
        tooltip : str | None
            Optional tooltip for the entire widget.
        """
        # Validate icons first (fail fast)
        self._icons_before = icons_before or []
        self._icons_after = icons_after or []
        self._validate_icons()

        # Store internal state
        self._path = Path(path).resolve()
        self._line = line
        self._column = column

        # Store custom open keys for forwarding to FileLink
        self._custom_open_keys = open_keys

        # Auto-generate ID from filename if not provided
        if id is None:
            from .utils import sanitize_id

            id = sanitize_id(self._path.name)

        # Initialize container (bindings will be added dynamically in on_mount)
        super().__init__(
            name=name,
            id=id,
            classes=classes,
        )

        # Store custom tooltip for later enhancement with all shortcuts
        self._custom_tooltip = tooltip

        # Create internal FileLink (embedded to prevent focus stealing)
        self._file_link = FileLink(
            path,
            display_name=display_name,
            line=line,
            column=column,
            command_builder=command_builder,
            open_keys=open_keys,  # Forward custom keys to embedded FileLink
            _embedded=True,
            tooltip=None,  # No tooltip on embedded FileLink
        )

        # Create icon widgets
        self._icon_widgets: dict[str, Static] = {}

    def _validate_icons(self) -> None:
        """Validate icon configuration (fail fast on errors)."""
        all_icons = self._icons_before + self._icons_after

        # Check for duplicate names
        names = [icon.name for icon in all_icons]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate icon names: {set(duplicates)}")

        # Check for duplicate keys (excluding None)
        keys = [icon.key for icon in all_icons if icon.key is not None]
        if len(keys) != len(set(keys)):
            duplicates = [key for key in keys if keys.count(key) > 1]
            raise ValueError(f"Duplicate icon keys: {set(duplicates)}")

        # Check for conflicts with FileLink bindings
        filelink_keys = {"o", "enter"}  # FileLink's default keys
        for icon in all_icons:
            if icon.key in filelink_keys:
                raise ValueError(
                    f"Icon key '{icon.key}' conflicts with FileLink binding. Reserved keys: {filelink_keys}"
                )

    def on_mount(self) -> None:
        """Create dynamic bindings and action methods after widget is mounted."""
        all_icons = self._icons_before + self._icons_after

        for icon in all_icons:
            if icon.key is not None:
                action_name = f"activate_icon_{icon.name}"
                description = icon.tooltip or f"Activate {icon.name}"

                # Add binding using runtime API
                self._bindings.bind(
                    icon.key,
                    action_name,
                    description,
                    show=False,
                )

                # Create action method for this icon
                def make_action(captured_icon):
                    def action_method():
                        if captured_icon.clickable:
                            self.post_message(
                                self.IconClicked(self, self._path, captured_icon.name, captured_icon.icon)
                            )

                    return action_method

                # Set the action method on this instance
                setattr(self, f"action_{action_name}", make_action(icon))

        # Build complete tooltip with all keyboard shortcuts
        self._build_tooltip_with_shortcuts()

    def compose(self):
        """Compose the widget layout: [icons_before] FileLink [icons_after]."""
        # Icons before
        for icon in self._icons_before:
            if icon.visible:
                widget = self._create_icon_widget(icon)
                self._icon_widgets[icon.name] = widget
                yield widget

        # FileLink (embedded)
        yield self._file_link

        # Icons after
        for icon in self._icons_after:
            if icon.visible:
                widget = self._create_icon_widget(icon)
                self._icon_widgets[icon.name] = widget
                yield widget

    def _create_icon_widget(self, icon: Icon) -> Static:
        """Create a Static widget for an icon."""
        classes = "icon-widget"
        if icon.clickable:
            classes += " clickable"

        # Create widget (no ID needed - we track by name in _icon_widgets dict)
        widget = Static(icon.icon, classes=classes)

        # Set tooltip (enhanced with keyboard shortcut if applicable)
        if icon.tooltip or icon.key:
            tooltip = icon.tooltip or f"Activate {icon.name}"
            if icon.key:
                tooltip = f"{tooltip} ({icon.key})"
            widget.tooltip = tooltip

        # Handle clicks if clickable - store metadata directly
        if icon.clickable:
            widget._icon_name = icon.name  # type: ignore
            widget._icon_char = icon.icon  # type: ignore

        return widget

    def on_click(self, event) -> None:
        """Handle clicks on icon widgets."""
        # Check if click target is an icon widget
        if hasattr(event.widget, "_icon_name"):
            event.stop()
            icon_name = event.widget._icon_name  # type: ignore
            icon_char = event.widget._icon_char  # type: ignore
            self.post_message(self.IconClicked(self, self._path, icon_name, icon_char))

    def action_open_file(self) -> None:
        """Open the file in the configured editor (keyboard shortcut handler)."""
        self._file_link.open_file()

    # ------------------------------------------------------------------ #
    # Helper methods
    # ------------------------------------------------------------------ #
    def _build_tooltip_with_shortcuts(self) -> None:
        """Build and set tooltip showing description with all keyboard shortcuts."""
        shortcuts_str = self._get_shortcuts_string()

        # Build tooltip: use custom tooltip or default description as base
        base = self._custom_tooltip if self._custom_tooltip else f"Open {self._path.name}"

        tooltip = f"{base} - {shortcuts_str}" if shortcuts_str else base

        self.tooltip = tooltip

    def _get_shortcuts_string(self) -> str:
        """Get keyboard shortcuts as a formatted string.

        Returns
        -------
        str
            Comma-separated shortcuts, e.g., "Open (enter/o), Status (1)"
        """
        shortcuts = []

        # Add open file shortcut (use custom keys if provided, else FileLink's defaults)
        open_keys = self._custom_open_keys if self._custom_open_keys is not None else FileLink.DEFAULT_OPEN_KEYS
        shortcuts.append(f"Open {format_keyboard_shortcuts(open_keys)}")

        # Add icon shortcuts (only for clickable icons with keys)
        all_icons = self._icons_before + self._icons_after
        for icon in all_icons:
            if icon.clickable and icon.key:
                icon_desc = icon.tooltip or icon.name.title()
                shortcuts.append(f"{icon_desc} {format_keyboard_shortcuts([icon.key])}")

        return ", ".join(shortcuts)

    # ------------------------------------------------------------------ #
    # Public API - Icon Management
    # ------------------------------------------------------------------ #
    def update_icon(self, name: str, **kwargs) -> None:
        """Update an icon's properties.

        Parameters
        ----------
        name : str
            Name of the icon to update.
        **kwargs
            Icon properties to update (icon, tooltip, clickable, visible, key).

        Raises
        ------
        ValueError
            If icon name not found or invalid property provided.

        Examples
        --------
        >>> widget.update_icon("status", icon="✅", tooltip="Passed")
        >>> widget.update_icon("warning", visible=True)
        """
        # Find the icon
        icon = self._get_icon_by_name(name)
        if icon is None:
            raise ValueError(f"Icon '{name}' not found")

        # Update properties
        valid_props = {"icon", "tooltip", "clickable", "visible", "key"}
        for key, value in kwargs.items():
            if key not in valid_props:
                raise ValueError(f"Invalid icon property: {key}")
            setattr(icon, key, value)

        # Re-render icons (visibility or content may have changed)
        self._rerender_icons()

    def set_icon_visible(self, name: str, visible: bool) -> None:
        """Set icon visibility.

        Parameters
        ----------
        name : str
            Name of the icon.
        visible : bool
            Whether the icon should be visible.

        Raises
        ------
        ValueError
            If icon name not found.
        """
        icon = self._get_icon_by_name(name)
        if icon is None:
            raise ValueError(f"Icon '{name}' not found")

        icon.visible = visible
        self._rerender_icons()

    def get_icon(self, name: str) -> Icon | None:
        """Get icon by name.

        Parameters
        ----------
        name : str
            Name of the icon.

        Returns
        -------
        Icon | None
            The icon if found, None otherwise.
        """
        return self._get_icon_by_name(name)

    def _get_icon_by_name(self, name: str) -> Icon | None:
        """Helper to find icon by name in both lists."""
        all_icons = self._icons_before + self._icons_after
        for icon in all_icons:
            if icon.name == name:
                return icon
        return None

    def _rerender_icons(self) -> None:
        """Re-render all icons (called after visibility/content changes)."""
        # Remove all current icon widgets
        for widget in list(self._icon_widgets.values()):
            widget.remove()
        self._icon_widgets.clear()

        # Re-create visible icons before FileLink
        for icon in self._icons_before:
            if icon.visible:
                widget = self._create_icon_widget(icon)
                self._icon_widgets[icon.name] = widget
                # Mount before FileLink
                self.mount(widget, before=self._file_link)

        # Re-create visible icons after FileLink
        for icon in self._icons_after:
            if icon.visible:
                widget = self._create_icon_widget(icon)
                self._icon_widgets[icon.name] = widget
                # Mount after FileLink
                self.mount(widget)

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def file_link(self) -> FileLink:
        """Get the internal FileLink widget (read-only access)."""
        return self._file_link

    @property
    def path(self) -> Path:
        """Get the file path."""
        return self._path

    @property
    def line(self) -> int | None:
        """Get the line number."""
        return self._line

    @property
    def column(self) -> int | None:
        """Get the column number."""
        return self._column
