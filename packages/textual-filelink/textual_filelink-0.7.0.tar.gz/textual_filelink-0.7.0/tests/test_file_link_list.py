# tests/test_file_link_list.py
"""Tests for FileLinkList widget (v0.4.0)."""

import pytest
from textual.app import App, ComposeResult

from textual_filelink import CommandLink, FileLink, FileLinkList, FileLinkWithIcons, Icon


class FileLinkListTestApp(App):
    """Test app for FileLinkList."""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.item_toggled_events = []
        self.item_removed_events = []

    def compose(self) -> ComposeResult:
        yield self.widget

    def on_file_link_list_item_toggled(self, event: FileLinkList.ItemToggled):
        self.item_toggled_events.append(event)

    def on_file_link_list_item_removed(self, event: FileLinkList.ItemRemoved):
        self.item_removed_events.append(event)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary test file."""
    file = tmp_path / "test.py"
    file.write_text("print('test')")
    return file


class TestFileLinkListInitialization:
    """Test suite for FileLinkList initialization."""

    def test_initialization_defaults(self):
        """Test FileLinkList initializes with default values."""
        file_list = FileLinkList()

        assert file_list._show_toggles is False
        assert file_list._show_remove is False
        assert len(file_list) == 0

    def test_initialization_with_toggles(self):
        """Test FileLinkList initializes with toggles enabled."""
        file_list = FileLinkList(show_toggles=True)

        assert file_list._show_toggles is True

    def test_initialization_with_remove(self):
        """Test FileLinkList initializes with remove buttons enabled."""
        file_list = FileLinkList(show_remove=True)

        assert file_list._show_remove is True

    def test_initialization_with_both(self):
        """Test FileLinkList initializes with both toggles and remove."""
        file_list = FileLinkList(show_toggles=True, show_remove=True)

        assert file_list._show_toggles is True
        assert file_list._show_remove is True


class TestFileLinkListAddItem:
    """Test suite for adding items to FileLinkList."""

    async def test_add_filelink(self, temp_file):
        """Test adding a FileLink to the list."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            assert len(file_list) == 1
            assert link.id in file_list._item_ids
            assert link in file_list.get_items()

    async def test_add_filelink_with_icons(self, temp_file):
        """Test adding a FileLinkWithIcons to the list."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLinkWithIcons(
                temp_file,
                icons_before=[Icon(name="status", icon="✅")],
                id="test-with-icons",
            )
            file_list.add_item(link)

            assert len(file_list) == 1
            assert link.id in file_list._item_ids

    async def test_add_commandlink(self):
        """Test adding a CommandLink to the list."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            cmd = CommandLink("Build", id="build-cmd")
            file_list.add_item(cmd)

            assert len(file_list) == 1
            assert cmd.id in file_list._item_ids

    async def test_add_multiple_items(self, temp_file):
        """Test adding multiple items to the list."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")
            link3 = FileLink(temp_file, id="link3")

            file_list.add_item(link1)
            file_list.add_item(link2)
            file_list.add_item(link3)

            assert len(file_list) == 3
            assert link1 in file_list.get_items()
            assert link2 in file_list.get_items()
            assert link3 in file_list.get_items()

    async def test_add_item_with_toggle(self, temp_file):
        """Test adding item with initial toggle state."""
        file_list = FileLinkList(show_toggles=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link, toggled=True)

            wrapper = file_list._wrappers["test-py"]
            assert wrapper.is_toggled is True

    async def test_add_item_without_id_raises(self):
        """Test adding item without ID raises ValueError."""
        from textual.widgets import Static

        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            # Use a Static widget without an ID
            widget = Static("No ID")

            with pytest.raises(ValueError, match="must have an explicit ID"):
                file_list.add_item(widget)

    async def test_add_duplicate_id_raises(self, temp_file):
        """Test adding item with duplicate ID raises ValueError."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link1 = FileLink(temp_file, id="duplicate")
            file_list.add_item(link1)

            link2 = FileLink(temp_file, id="duplicate")
            with pytest.raises(ValueError, match="Duplicate item ID"):
                file_list.add_item(link2)


class TestFileLinkListRemoveItem:
    """Test suite for removing items from FileLinkList."""

    async def test_remove_item(self, temp_file):
        """Test removing an item from the list."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            assert len(file_list) == 1

            file_list.remove_item(link)

            assert len(file_list) == 0
            assert link.id not in file_list._item_ids

    async def test_remove_item_posts_message(self, temp_file):
        """Test removing item posts ItemRemoved message."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test() as pilot:
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            file_list.remove_item(link)
            await pilot.pause()

            assert len(app.item_removed_events) == 1
            assert app.item_removed_events[0].item == link

    async def test_remove_nonexistent_item(self, temp_file):
        """Test removing non-existent item does nothing."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            # Don't add it

            file_list.remove_item(link)  # Should not raise

            assert len(file_list) == 0


class TestFileLinkListClearItems:
    """Test suite for clearing all items from FileLinkList."""

    async def test_clear_items(self, temp_file):
        """Test clearing all items from the list."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")
            link3 = FileLink(temp_file, id="link3")

            file_list.add_item(link1)
            file_list.add_item(link2)
            file_list.add_item(link3)

            assert len(file_list) == 3

            file_list.clear_items()

            assert len(file_list) == 0
            assert len(file_list._item_ids) == 0
            assert len(file_list._wrappers) == 0

    async def test_clear_empty_list(self):
        """Test clearing an empty list does nothing."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            file_list.clear_items()  # Should not raise

            assert len(file_list) == 0


class TestFileLinkListToggleOperations:
    """Test suite for toggle operations in FileLinkList."""

    async def test_toggle_all_true(self, temp_file):
        """Test toggling all items to True."""
        file_list = FileLinkList(show_toggles=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test() as pilot:
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")

            file_list.add_item(link1, toggled=False)
            file_list.add_item(link2, toggled=False)

            file_list.toggle_all(True)
            await pilot.pause()

            assert file_list._wrappers["link1"].is_toggled is True
            assert file_list._wrappers["link2"].is_toggled is True

            # Should post 2 ItemToggled messages
            assert len(app.item_toggled_events) == 2

    async def test_toggle_all_false(self, temp_file):
        """Test toggling all items to False."""
        file_list = FileLinkList(show_toggles=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test() as pilot:
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")

            file_list.add_item(link1, toggled=True)
            file_list.add_item(link2, toggled=True)

            file_list.toggle_all(False)
            await pilot.pause()

            assert file_list._wrappers["link1"].is_toggled is False
            assert file_list._wrappers["link2"].is_toggled is False

    async def test_toggle_all_without_toggles_enabled(self, temp_file):
        """Test toggle_all() does nothing if toggles not enabled."""
        file_list = FileLinkList(show_toggles=False)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="link1")
            file_list.add_item(link)

            file_list.toggle_all(True)  # Should not raise

            # No toggle checkbox, so wrapper won't have is_toggled
            assert len(file_list) == 1

    async def test_get_toggled_items(self, temp_file):
        """Test getting all toggled items."""
        file_list = FileLinkList(show_toggles=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")
            link3 = FileLink(temp_file, id="link3")

            file_list.add_item(link1, toggled=True)
            file_list.add_item(link2, toggled=False)
            file_list.add_item(link3, toggled=True)

            toggled = file_list.get_toggled_items()

            assert len(toggled) == 2
            assert link1 in toggled
            assert link3 in toggled
            assert link2 not in toggled

    async def test_get_toggled_items_without_toggles(self, temp_file):
        """Test get_toggled_items() returns empty list if toggles not enabled."""
        file_list = FileLinkList(show_toggles=False)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="link1")
            file_list.add_item(link)

            toggled = file_list.get_toggled_items()

            assert len(toggled) == 0

    async def test_remove_selected(self, temp_file):
        """Test removing all toggled items."""
        file_list = FileLinkList(show_toggles=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test() as pilot:
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")
            link3 = FileLink(temp_file, id="link3")

            file_list.add_item(link1, toggled=True)
            file_list.add_item(link2, toggled=False)
            file_list.add_item(link3, toggled=True)

            file_list.remove_selected()
            await pilot.pause()

            assert len(file_list) == 1
            assert link2 in file_list.get_items()
            assert link1 not in file_list.get_items()
            assert link3 not in file_list.get_items()

            # Should post 2 ItemRemoved messages
            assert len(app.item_removed_events) == 2

    async def test_remove_selected_without_toggles(self, temp_file):
        """Test remove_selected() does nothing if toggles not enabled."""
        file_list = FileLinkList(show_toggles=False)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="link1")
            file_list.add_item(link)

            file_list.remove_selected()  # Should not raise

            assert len(file_list) == 1


class TestFileLinkListIteration:
    """Test suite for iterating over FileLinkList."""

    async def test_len(self, temp_file):
        """Test __len__() returns correct count."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            assert len(file_list) == 0

            link1 = FileLink(temp_file, id="link1")
            file_list.add_item(link1)
            assert len(file_list) == 1

            link2 = FileLink(temp_file, id="link2")
            file_list.add_item(link2)
            assert len(file_list) == 2

            file_list.remove_item(link1)
            assert len(file_list) == 1

    async def test_iter(self, temp_file):
        """Test __iter__() allows iteration over items."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")
            link3 = FileLink(temp_file, id="link3")

            file_list.add_item(link1)
            file_list.add_item(link2)
            file_list.add_item(link3)

            items = list(file_list)

            assert len(items) == 3
            assert link1 in items
            assert link2 in items
            assert link3 in items

    async def test_get_items(self, temp_file):
        """Test get_items() returns all items."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link1 = FileLink(temp_file, id="link1")
            link2 = FileLink(temp_file, id="link2")

            file_list.add_item(link1)
            file_list.add_item(link2)

            items = file_list.get_items()

            assert len(items) == 2
            assert link1 in items
            assert link2 in items


class TestFileLinkListWrapperLayout:
    """Test suite for wrapper layout in FileLinkList."""

    async def test_wrapper_without_controls(self, temp_file):
        """Test wrapper layout without toggles or remove."""
        file_list = FileLinkList()
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            wrapper = file_list._wrappers["test-py"]
            assert wrapper._show_toggle is False
            assert wrapper._show_remove is False

    async def test_wrapper_with_toggle(self, temp_file):
        """Test wrapper layout with toggle enabled."""
        file_list = FileLinkList(show_toggles=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            wrapper = file_list._wrappers["test-py"]
            assert wrapper._show_toggle is True
            assert hasattr(wrapper, "_toggle_icon")

    async def test_wrapper_with_remove(self, temp_file):
        """Test wrapper layout with remove button enabled."""
        file_list = FileLinkList(show_remove=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            wrapper = file_list._wrappers["test-py"]
            assert wrapper._show_remove is True
            assert hasattr(wrapper, "_remove_button")

    async def test_wrapper_with_both_controls(self, temp_file):
        """Test wrapper layout with both toggle and remove."""
        file_list = FileLinkList(show_toggles=True, show_remove=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test():
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            wrapper = file_list._wrappers["test-py"]
            assert wrapper._show_toggle is True
            assert wrapper._show_remove is True
            assert hasattr(wrapper, "_toggle_icon")
            assert hasattr(wrapper, "_remove_button")


class TestFileLinkListClicks:
    """Test suite for FileLinkList click interactions."""

    async def test_clicking_remove_button_removes_item(self, temp_file):
        """Test clicking remove button removes item from list."""
        file_list = FileLinkList(show_remove=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test() as pilot:
            link = FileLink(temp_file, id="test-py")
            file_list.add_item(link)

            # Verify item is in list
            assert len(file_list) == 1

            # Get the wrapper and remove button
            wrapper = file_list._wrappers["test-py"]
            remove_button = wrapper._remove_button

            # Click the remove button
            await pilot.click(remove_button)
            await pilot.pause()

            # Verify item was removed
            assert len(file_list) == 0
            assert len(app.item_removed_events) == 1
            assert app.item_removed_events[0].item == link

    async def test_clicking_remove_with_both_controls_enabled(self, temp_file):
        """Test clicking remove when both toggle and remove are enabled."""
        file_list = FileLinkList(show_toggles=True, show_remove=True)
        app = FileLinkListTestApp(file_list)

        async with app.run_test() as pilot:
            link1 = FileLink(temp_file, id="test-py-1")
            link2 = FileLink(temp_file, id="test-py-2")
            file_list.add_item(link1)
            file_list.add_item(link2)

            # Verify both items are in list
            assert len(file_list) == 2

            # Remove second item
            wrapper2 = file_list._wrappers["test-py-2"]
            await pilot.click(wrapper2._remove_button)
            await pilot.pause()

            # Verify one item was removed
            assert len(file_list) == 1
            assert len(app.item_removed_events) == 1
            assert app.item_removed_events[0].item == link2
