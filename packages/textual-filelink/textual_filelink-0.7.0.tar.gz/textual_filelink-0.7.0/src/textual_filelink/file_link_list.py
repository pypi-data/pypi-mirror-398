"""FileLinkList widget - Container for managing file link widgets with uniform controls (v0.4.0)."""

from __future__ import annotations

from collections.abc import Iterable

from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class FileLinkListItem(Horizontal):
    """Internal wrapper widget for items in FileLinkList.

    Layout: [toggle?] item [remove?]
    """

    DEFAULT_CSS = """
    FileLinkListItem {
        width: 100%;
        height: auto;
        padding: 0;
    }
    FileLinkListItem > .toggle-icon {
        width: auto;
        height: 1;
        padding: 0 1;
        color: $primary;
    }
    FileLinkListItem > .toggle-icon:hover {
        text-style: bold;
        background: $boost;
    }
    FileLinkListItem > .remove-button {
        width: auto;
        height: 1;
        padding: 0 1;
        color: $error;
    }
    FileLinkListItem > .remove-button:hover {
        text-style: bold;
        background: $boost;
    }
    """

    def __init__(
        self,
        item: Widget,
        *,
        show_toggle: bool = False,
        show_remove: bool = False,
        initial_toggle: bool = False,
    ) -> None:
        """Initialize the wrapper.

        Parameters
        ----------
        item : Widget
            The widget to wrap (FileLink, FileLinkWithIcons, CommandLink, etc.).
        show_toggle : bool
            Whether to show toggle checkbox.
        show_remove : bool
            Whether to show remove button.
        initial_toggle : bool
            Initial toggle state (default: False).
        """
        super().__init__()
        self._item = item
        self._show_toggle = show_toggle
        self._show_remove = show_remove
        self._is_toggled = initial_toggle

        # Create toggle icon if enabled
        if self._show_toggle:
            icon = "☑" if initial_toggle else "☐"
            self._toggle_icon = Static(icon, classes="toggle-icon")
            self._toggle_icon.tooltip = "Toggle selection"

        # Create remove button if enabled
        if self._show_remove:
            self._remove_button = Static("×", classes="remove-button")
            self._remove_button.tooltip = "Remove item"

    def compose(self):
        """Compose the wrapper layout."""
        if self._show_toggle:
            yield self._toggle_icon
        yield self._item
        if self._show_remove:
            yield self._remove_button

    def on_click(self, event) -> None:
        """Handle clicks on toggle icon and remove button."""
        # Handle toggle icon click - update visual state
        if self._show_toggle and event.widget == self._toggle_icon:
            self._is_toggled = not self._is_toggled
            self._toggle_icon.update("☑" if self._is_toggled else "☐")
            # Don't stop - let it bubble to FileLinkList for ItemToggled message

        # For remove button, don't stop - let it bubble to FileLinkList for removal

    @property
    def item(self) -> Widget:
        """Get the wrapped item."""
        return self._item

    @property
    def is_toggled(self) -> bool:
        """Get toggle state."""
        return self._is_toggled

    def set_toggled(self, value: bool) -> None:
        """Set toggle state."""
        if self._show_toggle:
            self._is_toggled = value
            self._toggle_icon.update("☑" if value else "☐")


class FileLinkList(VerticalScroll):
    """Container for managing file link widgets with uniform controls.

    Features
    --------
    - Automatic scrolling via VerticalScroll
    - Optional toggle checkboxes for each item
    - Optional remove buttons for each item
    - ID validation (all items must have explicit IDs, no duplicates)
    - Batch operations: toggle_all(), remove_selected()

    Example
    -------
    >>> from textual_filelink import FileLinkList, FileLink, FileLinkWithIcons, Icon
    >>>
    >>> file_list = FileLinkList(show_toggles=True, show_remove=True)
    >>>
    >>> # Add FileLink
    >>> link1 = FileLink("test.py", id="test-py")
    >>> file_list.add_item(link1, toggled=True)
    >>>
    >>> # Add FileLinkWithIcons
    >>> link2 = FileLinkWithIcons(
    ...     "main.py",
    ...     icons_before=[Icon(name="status", icon="✅")],
    ...     id="main-py"
    ... )
    >>> file_list.add_item(link2)
    """

    DEFAULT_CSS = """
    FileLinkList {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    class ItemToggled(Message):
        """Posted when an item's toggle state changes.

        Attributes
        ----------
        item : Widget
            The item that was toggled.
        is_toggled : bool
            New toggle state.
        """

        def __init__(self, item: Widget, is_toggled: bool) -> None:
            super().__init__()
            self.item = item
            self.is_toggled = is_toggled

    class ItemRemoved(Message):
        """Posted when an item is removed.

        Attributes
        ----------
        item : Widget
            The item that was removed.
        """

        def __init__(self, item: Widget) -> None:
            super().__init__()
            self.item = item

    def __init__(
        self,
        *,
        show_toggles: bool = False,
        show_remove: bool = False,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the file link list.

        Parameters
        ----------
        show_toggles : bool
            Whether to show toggle checkboxes for all items (default: False).
        show_remove : bool
            Whether to show remove buttons for all items (default: False).
        id : str | None
            Widget ID.
        classes : str | None
            CSS classes.
        """
        super().__init__(id=id, classes=classes)
        self._show_toggles = show_toggles
        self._show_remove = show_remove
        self._item_ids: set[str] = set()
        self._wrappers: dict[str, FileLinkListItem] = {}

    def add_item(
        self,
        item: Widget,
        *,
        toggled: bool = False,
    ) -> None:
        """Add an item to the list.

        Parameters
        ----------
        item : Widget
            The widget to add (must have an explicit ID set).
        toggled : bool
            Initial toggle state (default: False).

        Raises
        ------
        ValueError
            If item has no ID or ID is duplicate.
        """
        # Validate ID exists
        if not item.id:
            raise ValueError(f"Item must have an explicit ID set. Got: {item}")

        # Validate ID is unique
        if item.id in self._item_ids:
            raise ValueError(
                f"Duplicate item ID: '{item.id}'. "
                f"Each item in FileLinkList must have a unique ID. "
                f"Either use a different name or provide an explicit id parameter."
            )

        # Track ID
        self._item_ids.add(item.id)

        # Create wrapper
        wrapper = FileLinkListItem(
            item,
            show_toggle=self._show_toggles,
            show_remove=self._show_remove,
            initial_toggle=toggled,
        )
        self._wrappers[item.id] = wrapper

        # Mount the wrapper
        self.mount(wrapper)

    def remove_item(self, item: Widget) -> None:
        """Remove an item from the list.

        Parameters
        ----------
        item : Widget
            The item to remove (by ID).
        """
        if item.id not in self._item_ids:
            return

        # Get wrapper
        wrapper = self._wrappers[item.id]

        # Remove from tracking
        self._item_ids.remove(item.id)
        del self._wrappers[item.id]

        # Remove wrapper from DOM
        wrapper.remove()

        # Post message
        self.post_message(self.ItemRemoved(item))

    def clear_items(self) -> None:
        """Remove all items from the list."""
        # Remove all wrappers
        for wrapper in list(self._wrappers.values()):
            wrapper.remove()

        # Clear tracking
        self._item_ids.clear()
        self._wrappers.clear()

    def toggle_all(self, value: bool) -> None:
        """Set all toggle checkboxes to the same value.

        Parameters
        ----------
        value : bool
            Toggle state to set for all items.
        """
        if not self._show_toggles:
            return

        for wrapper in self._wrappers.values():
            wrapper.set_toggled(value)
            # Post message for each toggle
            self.post_message(self.ItemToggled(wrapper.item, value))

    def remove_selected(self) -> None:
        """Remove all toggled items from the list."""
        if not self._show_toggles:
            return

        # Collect items to remove
        to_remove = [wrapper.item for wrapper in self._wrappers.values() if wrapper.is_toggled]

        # Remove them
        for item in to_remove:
            self.remove_item(item)

    def get_toggled_items(self) -> list[Widget]:
        """Get all currently toggled items.

        Returns
        -------
        list[Widget]
            List of toggled items.
        """
        if not self._show_toggles:
            return []

        return [wrapper.item for wrapper in self._wrappers.values() if wrapper.is_toggled]

    def get_items(self) -> list[Widget]:
        """Get all items in the list.

        Returns
        -------
        list[Widget]
            List of all items.
        """
        return [wrapper.item for wrapper in self._wrappers.values()]

    def __len__(self) -> int:
        """Get number of items in the list."""
        return len(self._item_ids)

    def __iter__(self) -> Iterable[Widget]:
        """Iterate over items in the list."""
        return iter(self.get_items())

    # ------------------------------------------------------------------ #
    # Event handlers for wrapper events
    # ------------------------------------------------------------------ #
    def on_click(self, event) -> None:
        """Handle clicks on toggle icons and remove buttons in wrapper items."""
        # Check each wrapper for toggle icon or remove button clicks
        for wrapper in self._wrappers.values():
            # Handle toggle icon click
            if self._show_toggles and hasattr(wrapper, "_toggle_icon") and wrapper._toggle_icon == event.widget:
                # Post ItemToggled message
                self.post_message(self.ItemToggled(wrapper.item, wrapper.is_toggled))
                event.stop()
                return

            # Handle remove button click
            if self._show_remove and hasattr(wrapper, "_remove_button") and wrapper._remove_button == event.widget:
                # Remove the item
                self.remove_item(wrapper.item)
                event.stop()
                return
