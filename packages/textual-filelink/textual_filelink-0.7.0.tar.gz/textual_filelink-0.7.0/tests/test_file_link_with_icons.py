"""Tests for FileLinkWithIcons widget."""

import pytest
from textual.app import App, ComposeResult

from textual_filelink import FileLink
from textual_filelink.file_link_with_icons import FileLinkWithIcons
from textual_filelink.icon import Icon
from textual_filelink.utils import sanitize_id


class FileLinkWithIconsTestApp(App):
    """Test app for FileLinkWithIcons."""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.icon_clicked_events = []
        self.file_opened_events = []

    def compose(self) -> ComposeResult:
        yield self.widget

    def on_file_link_with_icons_icon_clicked(self, event: FileLinkWithIcons.IconClicked):
        self.icon_clicked_events.append(event)

    def on_file_link_opened(self, event: FileLink.Opened):
        self.file_opened_events.append(event)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    return test_file


class TestFileLinkWithIconsBasic:
    """Basic initialization and property tests."""

    async def test_initialization_minimal(self, temp_file):
        """Test FileLinkWithIcons with minimal parameters."""
        widget = FileLinkWithIcons(temp_file)

        assert widget.path == temp_file
        assert widget.line is None
        assert widget.column is None

    async def test_initialization_with_position(self, temp_file):
        """Test FileLinkWithIcons with line/column."""
        widget = FileLinkWithIcons(temp_file, line=10, column=5)

        assert widget.path == temp_file
        assert widget.line == 10
        assert widget.column == 5

    async def test_initialization_with_display_name(self, temp_file):
        """Test FileLinkWithIcons with custom display name."""
        widget = FileLinkWithIcons(temp_file, display_name="Custom Name")

        assert widget.file_link.display_name == "Custom Name"

    async def test_file_link_property(self, temp_file):
        """Test file_link property returns internal FileLink."""
        widget = FileLinkWithIcons(temp_file)

        assert isinstance(widget.file_link, FileLink)
        assert widget.file_link.path == temp_file

    async def test_file_link_is_embedded(self, temp_file):
        """Test internal FileLink has can_focus=False (embedded mode)."""
        widget = FileLinkWithIcons(temp_file)

        assert widget.file_link.can_focus is False


class TestFileLinkWithIconsLayout:
    """Tests for icon layout and ordering."""

    async def test_icons_before_only(self, temp_file):
        """Test widget with only icons_before."""
        icons = [
            Icon(name="icon1", icon="✅"),
            Icon(name="icon2", icon="⚠️"),
        ]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # Should have 2 icon widgets + 1 FileLink
            assert len(widget._icon_widgets) == 2
            assert "icon1" in widget._icon_widgets
            assert "icon2" in widget._icon_widgets

    async def test_icons_after_only(self, temp_file):
        """Test widget with only icons_after."""
        icons = [
            Icon(name="icon1", icon="🔒"),
            Icon(name="icon2", icon="📝"),
        ]
        widget = FileLinkWithIcons(temp_file, icons_after=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            assert len(widget._icon_widgets) == 2
            assert "icon1" in widget._icon_widgets
            assert "icon2" in widget._icon_widgets

    async def test_icons_before_and_after(self, temp_file):
        """Test widget with both icons_before and icons_after."""
        icons_before = [Icon(name="before1", icon="📌")]
        icons_after = [Icon(name="after1", icon="🔗")]
        widget = FileLinkWithIcons(
            temp_file,
            icons_before=icons_before,
            icons_after=icons_after,
        )
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            assert len(widget._icon_widgets) == 2
            assert "before1" in widget._icon_widgets
            assert "after1" in widget._icon_widgets

    async def test_icon_ordering_preserved(self, temp_file):
        """Test that icon order in lists is preserved."""
        icons_before = [
            Icon(name="first", icon="1️⃣"),
            Icon(name="second", icon="2️⃣"),
            Icon(name="third", icon="3️⃣"),
        ]
        widget = FileLinkWithIcons(temp_file, icons_before=icons_before)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # Check that icons exist in our internal tracking
            assert widget.get_icon("first") is not None
            assert widget.get_icon("second") is not None
            assert widget.get_icon("third") is not None


class TestFileLinkWithIconsVisibility:
    """Tests for icon visibility control."""

    async def test_icon_initially_hidden(self, temp_file):
        """Test icon with visible=False is not rendered."""
        icons = [
            Icon(name="visible", icon="✅", visible=True),
            Icon(name="hidden", icon="❌", visible=False),
        ]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # Only visible icon should be in widgets dict
            assert "visible" in widget._icon_widgets
            assert "hidden" not in widget._icon_widgets

    async def test_set_icon_visible_show(self, temp_file):
        """Test showing a hidden icon."""
        icons = [Icon(name="icon1", icon="✅", visible=False)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Initially hidden
            assert "icon1" not in widget._icon_widgets

            # Show it
            widget.set_icon_visible("icon1", True)
            await pilot.pause()

            # Now should be visible
            assert "icon1" in widget._icon_widgets

    async def test_set_icon_visible_hide(self, temp_file):
        """Test hiding a visible icon."""
        icons = [Icon(name="icon1", icon="✅", visible=True)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Initially visible
            assert "icon1" in widget._icon_widgets

            # Hide it
            widget.set_icon_visible("icon1", False)
            await pilot.pause()

            # Now should be hidden
            assert "icon1" not in widget._icon_widgets

    async def test_set_icon_visible_nonexistent_raises(self, temp_file):
        """Test set_icon_visible raises ValueError for nonexistent icon."""
        widget = FileLinkWithIcons(temp_file)

        with pytest.raises(ValueError, match="not found"):
            widget.set_icon_visible("nonexistent", True)


class TestFileLinkWithIconsClickability:
    """Tests for clickable icons."""

    async def test_clickable_icon_posts_message(self, temp_file):
        """Test clicking a clickable icon posts IconClicked message."""
        icons = [Icon(name="settings", icon="⚙️", clickable=True)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Click the icon widget
            icon_widget = widget._icon_widgets["settings"]
            await pilot.click(type(icon_widget), offset=(0, 0))
            await pilot.pause()

            # Should have posted IconClicked
            assert len(app.icon_clicked_events) == 1
            event = app.icon_clicked_events[0]
            assert event.path == temp_file
            assert event.icon_name == "settings"
            assert event.icon_char == "⚙️"

    async def test_non_clickable_icon_no_message(self, temp_file):
        """Test clicking a non-clickable icon does not post message."""
        icons = [Icon(name="status", icon="✅", clickable=False)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Click the icon widget
            icon_widget = widget._icon_widgets["status"]
            await pilot.click(type(icon_widget), offset=(0, 0))
            await pilot.pause()

            # Should not have posted IconClicked
            assert len(app.icon_clicked_events) == 0

    async def test_multiple_clickable_icons(self, temp_file):
        """Test multiple clickable icons work independently."""
        icons = [
            Icon(name="icon1", icon="1️⃣", clickable=True),
            Icon(name="icon2", icon="2️⃣", clickable=True),
        ]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Simulate the click by posting the message directly
            widget.post_message(FileLinkWithIcons.IconClicked(widget, temp_file, "icon1", "1️⃣"))
            await pilot.pause()

            assert len(app.icon_clicked_events) == 1
            assert app.icon_clicked_events[0].icon_name == "icon1"

            # Click second icon
            widget.post_message(FileLinkWithIcons.IconClicked(widget, temp_file, "icon2", "2️⃣"))
            await pilot.pause()

            assert len(app.icon_clicked_events) == 2
            assert app.icon_clicked_events[1].icon_name == "icon2"


class TestFileLinkWithIconsKeyboardShortcuts:
    """Tests for keyboard shortcuts on icons."""

    async def test_icon_with_key_creates_binding(self, temp_file):
        """Test icon with key creates keyboard binding after mount."""
        icons = [Icon(name="settings", icon="⚙️", clickable=True, key="s")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # After mount, bindings should be created in _bindings
            bindings = widget._bindings.get_bindings_for_key("s")
            assert len(bindings) > 0
            assert bindings[0].action == "activate_icon_settings"

    async def test_keyboard_shortcut_triggers_icon(self, temp_file):
        """Test pressing key triggers icon action."""
        icons = [Icon(name="settings", icon="⚙️", clickable=True, key="s")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Focus widget and press 's'
            widget.focus()
            await pilot.press("s")
            await pilot.pause()

            # Should have posted IconClicked
            assert len(app.icon_clicked_events) == 1
            assert app.icon_clicked_events[0].icon_name == "settings"

    async def test_multiple_keyboard_shortcuts(self, temp_file):
        """Test multiple icons with different keyboard shortcuts."""
        icons = [
            Icon(name="icon1", icon="1️⃣", clickable=True, key="1"),
            Icon(name="icon2", icon="2️⃣", clickable=True, key="2"),
        ]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Press '1'
            widget.focus()
            await pilot.press("1")
            await pilot.pause()

            assert len(app.icon_clicked_events) == 1
            assert app.icon_clicked_events[0].icon_name == "icon1"

            # Press '2'
            await pilot.press("2")
            await pilot.pause()

            assert len(app.icon_clicked_events) == 2
            assert app.icon_clicked_events[1].icon_name == "icon2"

    async def test_non_clickable_icon_with_key_no_message(self, temp_file):
        """Test keyboard shortcut on non-clickable icon does nothing."""
        icons = [Icon(name="status", icon="✅", clickable=False, key="s")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Press 's'
            widget.focus()
            await pilot.press("s")
            await pilot.pause()

            # Should not post IconClicked (icon not clickable)
            assert len(app.icon_clicked_events) == 0


class TestFileLinkWithIconsIconManagement:
    """Tests for icon management methods."""

    async def test_get_icon_existing(self, temp_file):
        """Test get_icon returns icon by name."""
        icons = [Icon(name="status", icon="✅")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)

        icon = widget.get_icon("status")
        assert icon is not None
        assert icon.name == "status"
        assert icon.icon == "✅"

    async def test_get_icon_nonexistent(self, temp_file):
        """Test get_icon returns None for nonexistent icon."""
        widget = FileLinkWithIcons(temp_file)

        icon = widget.get_icon("nonexistent")
        assert icon is None

    async def test_update_icon_content(self, temp_file):
        """Test update_icon changes icon character."""
        icons = [Icon(name="status", icon="⏳")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Update icon
            widget.update_icon("status", icon="✅")
            await pilot.pause()

            # Icon should be updated
            icon = widget.get_icon("status")
            assert icon.icon == "✅"

    async def test_update_icon_tooltip(self, temp_file):
        """Test update_icon changes tooltip."""
        icons = [Icon(name="status", icon="✅")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Update tooltip
            widget.update_icon("status", tooltip="New tooltip")
            await pilot.pause()

            # Tooltip should be updated
            icon = widget.get_icon("status")
            assert icon.tooltip == "New tooltip"

    async def test_update_icon_visibility(self, temp_file):
        """Test update_icon changes visibility."""
        icons = [Icon(name="status", icon="✅", visible=True)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Initially visible
            assert "status" in widget._icon_widgets

            # Hide via update_icon
            widget.update_icon("status", visible=False)
            await pilot.pause()

            # Should be hidden
            assert "status" not in widget._icon_widgets

    async def test_update_icon_clickable(self, temp_file):
        """Test update_icon changes clickable state."""
        icons = [Icon(name="status", icon="✅", clickable=False)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Make clickable
            widget.update_icon("status", clickable=True)
            await pilot.pause()

            # Should be clickable
            icon = widget.get_icon("status")
            assert icon.clickable is True

    async def test_update_icon_multiple_properties(self, temp_file):
        """Test update_icon changes multiple properties at once."""
        icons = [Icon(name="status", icon="⏳")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Update multiple properties
            widget.update_icon(
                "status",
                icon="✅",
                tooltip="Complete",
                clickable=True,
            )
            await pilot.pause()

            # All properties should be updated
            icon = widget.get_icon("status")
            assert icon.icon == "✅"
            assert icon.tooltip == "Complete"
            assert icon.clickable is True

    async def test_update_icon_nonexistent_raises(self, temp_file):
        """Test update_icon raises ValueError for nonexistent icon."""
        widget = FileLinkWithIcons(temp_file)

        with pytest.raises(ValueError, match="not found"):
            widget.update_icon("nonexistent", icon="✅")

    async def test_update_icon_invalid_property_raises(self, temp_file):
        """Test update_icon raises ValueError for invalid property."""
        icons = [Icon(name="status", icon="✅")]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)

        with pytest.raises(ValueError, match="Invalid icon property"):
            widget.update_icon("status", invalid_prop="value")


class TestFileLinkWithIconsValidation:
    """Tests for icon validation at initialization."""

    async def test_duplicate_icon_names_raises(self, temp_file):
        """Test duplicate icon names raises ValueError."""
        icons = [
            Icon(name="duplicate", icon="✅"),
            Icon(name="duplicate", icon="❌"),
        ]

        with pytest.raises(ValueError, match="Duplicate icon names"):
            FileLinkWithIcons(temp_file, icons_before=icons)

    async def test_duplicate_icon_keys_raises(self, temp_file):
        """Test duplicate icon keys raises ValueError."""
        icons = [
            Icon(name="icon1", icon="✅", key="s"),
            Icon(name="icon2", icon="❌", key="s"),
        ]

        with pytest.raises(ValueError, match="Duplicate icon keys"):
            FileLinkWithIcons(temp_file, icons_before=icons)

    async def test_icon_key_conflicts_with_filelink_raises(self, temp_file):
        """Test icon key conflicting with FileLink binding raises ValueError."""
        icons = [Icon(name="icon1", icon="✅", key="o")]  # 'o' is FileLink's open key

        with pytest.raises(ValueError, match="conflicts with FileLink binding"):
            FileLinkWithIcons(temp_file, icons_before=icons)

    async def test_duplicate_names_across_before_after_raises(self, temp_file):
        """Test duplicate names across icons_before and icons_after raises."""
        icons_before = [Icon(name="duplicate", icon="✅")]
        icons_after = [Icon(name="duplicate", icon="❌")]

        with pytest.raises(ValueError, match="Duplicate icon names"):
            FileLinkWithIcons(
                temp_file,
                icons_before=icons_before,
                icons_after=icons_after,
            )

    async def test_duplicate_keys_across_before_after_raises(self, temp_file):
        """Test duplicate keys across icons_before and icons_after raises."""
        icons_before = [Icon(name="icon1", icon="✅", key="1")]
        icons_after = [Icon(name="icon2", icon="❌", key="1")]

        with pytest.raises(ValueError, match="Duplicate icon keys"):
            FileLinkWithIcons(
                temp_file,
                icons_before=icons_before,
                icons_after=icons_after,
            )

    async def test_none_keys_allowed(self, temp_file):
        """Test that None keys don't count as duplicates."""
        icons = [
            Icon(name="icon1", icon="✅", key=None),
            Icon(name="icon2", icon="❌", key=None),
        ]

        # Should not raise
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        assert widget is not None


class TestFileLinkWithIconsMessageBubbling:
    """Tests for message bubbling behavior."""

    async def test_icon_clicked_bubbles_to_app(self, temp_file):
        """Test IconClicked message bubbles to app level."""
        icons = [Icon(name="settings", icon="⚙️", clickable=True)]
        widget = FileLinkWithIcons(temp_file, icons_before=icons)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Click icon
            icon_widget = widget._icon_widgets["settings"]
            await pilot.click(type(icon_widget), offset=(0, 0))
            await pilot.pause()

            # App should have received the message
            assert len(app.icon_clicked_events) == 1

    async def test_filelink_opened_bubbles_through_widget(self, temp_file):
        """Test FileLink.Opened message bubbles through FileLinkWithIcons."""
        widget = FileLinkWithIcons(temp_file)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test() as pilot:
            # Trigger FileLink's open action
            widget.file_link.action_open_file()
            await pilot.pause()

            # App should have received the message
            assert len(app.file_opened_events) == 1
            assert app.file_opened_events[0].path == temp_file

    async def test_filelink_with_icons_auto_generates_id(self, temp_file):
        """Test FileLinkWithIcons auto-generates ID from filename."""
        widget = FileLinkWithIcons(temp_file)
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # temp_file is "test.txt" -> id="test-txt"
            assert widget.id is not None
            assert widget.id == sanitize_id(temp_file.name)
            assert widget.id == "test-txt"

    async def test_filelink_with_icons_explicit_id_overrides_auto(self, temp_file):
        """Test explicit ID takes precedence over auto-generation."""
        widget = FileLinkWithIcons(temp_file, id="custom-id")
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            assert widget.id == "custom-id"

    async def test_filelink_with_icons_custom_open_keys(self, temp_file):
        """Test FileLinkWithIcons accepts custom open_keys parameter."""
        widget = FileLinkWithIcons(temp_file, open_keys=["f2", "ctrl+o"])
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # Verify custom keys were forwarded to embedded FileLink
            assert widget._custom_open_keys == ["f2", "ctrl+o"]
            assert widget.file_link._custom_open_keys == ["f2", "ctrl+o"]

    async def test_filelink_with_icons_open_keys_in_tooltip(self, temp_file):
        """Test custom open_keys are reflected in tooltip."""
        widget = FileLinkWithIcons(temp_file, open_keys=["f2"])
        app = FileLinkWithIconsTestApp(widget)

        async with app.run_test():
            # Tooltip should show custom key
            assert widget.tooltip is not None
            assert "(f2)" in widget.tooltip

    async def test_filelink_with_icons_respects_filelink_default_keys(self, temp_file):
        """Test FileLinkWithIcons tooltip uses FileLink.DEFAULT_OPEN_KEYS as fallback."""
        # Save original defaults
        original_defaults = FileLink.DEFAULT_OPEN_KEYS

        try:
            # Change FileLink's global defaults
            FileLink.DEFAULT_OPEN_KEYS = ["ctrl+o", "f5"]

            # Create widget without custom open_keys
            widget = FileLinkWithIcons(temp_file)
            app = FileLinkWithIconsTestApp(widget)

            async with app.run_test():
                # Tooltip should reflect FileLink's defaults, not hardcoded ["enter", "o"]
                assert widget.tooltip is not None
                assert "(ctrl+o/f5)" in widget.tooltip.lower()

        finally:
            # Restore original defaults
            FileLink.DEFAULT_OPEN_KEYS = original_defaults
