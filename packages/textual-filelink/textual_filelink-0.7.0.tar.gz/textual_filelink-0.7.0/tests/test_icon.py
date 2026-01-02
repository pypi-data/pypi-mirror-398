"""Tests for Icon dataclass."""

import pytest

from textual_filelink.icon import Icon


class TestIcon:
    """Tests for Icon dataclass."""

    def test_icon_creation_with_required_fields_only(self):
        """Test creating icon with only required fields."""
        icon = Icon(name="status", icon="✅")

        assert icon.name == "status"
        assert icon.icon == "✅"
        assert icon.tooltip is None
        assert icon.clickable is False
        assert icon.key is None
        assert icon.visible is True

    def test_icon_creation_with_all_fields(self):
        """Test creating icon with all fields specified."""
        icon = Icon(
            name="settings",
            icon="⚙️",
            tooltip="Open settings",
            clickable=True,
            key="s",
            visible=False,
        )

        assert icon.name == "settings"
        assert icon.icon == "⚙️"
        assert icon.tooltip == "Open settings"
        assert icon.clickable is True
        assert icon.key == "s"
        assert icon.visible is False

    def test_icon_defaults(self):
        """Test that icon has correct default values."""
        icon = Icon(name="test", icon="📄")

        assert icon.clickable is False
        assert icon.visible is True
        assert icon.tooltip is None
        assert icon.key is None

    def test_icon_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Icon(name="", icon="✅")

    def test_icon_empty_icon_raises_error(self):
        """Test that empty icon raises ValueError."""
        with pytest.raises(ValueError, match="character cannot be empty"):
            Icon(name="status", icon="")

    def test_icon_none_name_raises_error(self):
        """Test that None name is treated as empty and raises ValueError."""
        with pytest.raises((ValueError, TypeError)):
            Icon(name=None, icon="✅")  # type: ignore

    def test_icon_none_icon_raises_error(self):
        """Test that None icon is treated as empty and raises ValueError."""
        with pytest.raises((ValueError, TypeError)):
            Icon(name="status", icon=None)  # type: ignore

    def test_icon_with_clickable_true(self):
        """Test icon with clickable=True."""
        icon = Icon(name="action", icon="▶️", clickable=True)

        assert icon.clickable is True

    def test_icon_with_keyboard_shortcut(self):
        """Test icon with keyboard shortcut."""
        icon = Icon(name="save", icon="💾", key="ctrl+s", clickable=True)

        assert icon.key == "ctrl+s"
        assert icon.clickable is True

    def test_icon_initially_hidden(self):
        """Test icon that is initially hidden."""
        icon = Icon(name="hidden", icon="👻", visible=False)

        assert icon.visible is False

    def test_icon_with_tooltip(self):
        """Test icon with tooltip."""
        icon = Icon(name="info", icon="ℹ️", tooltip="More information")

        assert icon.tooltip == "More information"

    def test_icon_repr(self):
        """Test icon string representation."""
        icon = Icon(name="test", icon="📌")
        repr_str = repr(icon)

        assert "Icon" in repr_str
        assert "name='test'" in repr_str
        assert "icon='📌'" in repr_str

    def test_icon_equality(self):
        """Test that two icons with same values are equal."""
        icon1 = Icon(name="status", icon="✅", clickable=True)
        icon2 = Icon(name="status", icon="✅", clickable=True)

        assert icon1 == icon2

    def test_icon_inequality(self):
        """Test that icons with different values are not equal."""
        icon1 = Icon(name="status", icon="✅")
        icon2 = Icon(name="status", icon="❌")

        assert icon1 != icon2

    def test_icon_mutation(self):
        """Test that icon fields can be mutated after creation."""
        icon = Icon(name="status", icon="⏳")

        # Mutate fields
        icon.icon = "✅"
        icon.tooltip = "Complete"
        icon.clickable = True
        icon.visible = False

        assert icon.icon == "✅"
        assert icon.tooltip == "Complete"
        assert icon.clickable is True
        assert icon.visible is False

    def test_icon_with_emoji(self):
        """Test icon with emoji characters."""
        icon = Icon(name="fire", icon="🔥")

        assert icon.icon == "🔥"

    def test_icon_with_unicode_symbols(self):
        """Test icon with various unicode symbols."""
        icons = [
            Icon(name="check", icon="✓"),
            Icon(name="cross", icon="✗"),
            Icon(name="star", icon="★"),
            Icon(name="arrow", icon="→"),
        ]

        assert icons[0].icon == "✓"
        assert icons[1].icon == "✗"
        assert icons[2].icon == "★"
        assert icons[3].icon == "→"

    def test_icon_number_keys(self):
        """Test icon with number keys for shortcuts."""
        for i in range(1, 10):
            icon = Icon(name=f"icon{i}", icon="•", key=str(i))
            assert icon.key == str(i)
