"""Tests for utility functions."""

from textual_filelink.utils import sanitize_id


class TestSanitizeId:
    """Tests for sanitize_id() function."""

    def test_sanitize_basic_string(self):
        """Test basic string sanitization."""
        assert sanitize_id("Run Tests") == "run-tests"
        assert sanitize_id("Build Project") == "build-project"

    def test_sanitize_path_forward_slash(self):
        """Test path sanitization with forward slashes."""
        assert sanitize_id("src/main.py") == "src-main-py"
        assert sanitize_id("tests/unit/test_file.py") == "tests-unit-test_file-py"

    def test_sanitize_path_backslash(self):
        """Test path sanitization with backslashes (Windows)."""
        assert sanitize_id("src\\file.py") == "src-file-py"
        assert sanitize_id("C:\\Users\\name\\file.txt") == "c--users-name-file-txt"

    def test_sanitize_special_characters(self):
        """Test sanitization of special characters."""
        assert sanitize_id("Build!") == "build-"
        assert sanitize_id("Test@Project#123") == "test-project-123"
        assert sanitize_id("File (copy).txt") == "file--copy--txt"

    def test_sanitize_already_clean(self):
        """Test sanitization of already-clean IDs."""
        assert sanitize_id("clean-id") == "clean-id"
        assert sanitize_id("my_widget_123") == "my_widget_123"
        assert sanitize_id("simple") == "simple"

    def test_sanitize_unicode_emoji(self):
        """Test sanitization of unicode and emoji characters."""
        assert sanitize_id("test🔥file") == "test-file"
        assert sanitize_id("my_✅_test") == "my_-_test"

    def test_sanitize_multiple_spaces(self):
        """Test sanitization of multiple consecutive spaces."""
        assert sanitize_id("test  file") == "test--file"
        assert sanitize_id("   spaces   ") == "---spaces---"

    def test_sanitize_mixed_separators(self):
        """Test sanitization with mixed separators."""
        assert sanitize_id("path/to\\file name.txt") == "path-to-file-name-txt"

    def test_sanitize_preserves_underscores(self):
        """Test that underscores are preserved."""
        assert sanitize_id("my_test_file") == "my_test_file"
        assert sanitize_id("TEST_CONSTANT") == "test_constant"

    def test_sanitize_preserves_hyphens(self):
        """Test that hyphens are preserved."""
        assert sanitize_id("my-test-file") == "my-test-file"
        assert sanitize_id("dash-separated-words") == "dash-separated-words"

    def test_sanitize_numbers(self):
        """Test sanitization with numbers."""
        assert sanitize_id("test123") == "test123"
        assert sanitize_id("123test") == "123test"
        assert sanitize_id("v1.2.3") == "v1-2-3"

    def test_sanitize_empty_string(self):
        """Test sanitization of empty string."""
        assert sanitize_id("") == ""

    def test_sanitize_only_special_chars(self):
        """Test sanitization of string with only special characters."""
        assert sanitize_id("!!!") == "---"
        assert sanitize_id("@#$") == "---"
