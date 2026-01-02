# Fixed conftest.py
# tests/conftest.py
"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_files(tmp_path):
    """Create a set of sample files for testing."""
    files = []

    # Create various test files
    file_names = ["document.txt", "script.py", "config.json", "readme.md", "data.csv"]

    for name in file_names:
        file_path = tmp_path / name
        file_path.write_text(f"Content of {name}")
        files.append(file_path)

    return files


@pytest.fixture
def sample_directory_structure(tmp_path):
    """Create a directory structure for testing."""
    # Create nested directories with files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("main content")
    (tmp_path / "src" / "utils.py").write_text("utils content")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("test content")

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("docs content")

    return tmp_path


@pytest.fixture
def long_filename(tmp_path):
    """Create a file with a very long name."""
    long_name = "a" * 100 + ".txt"
    file_path = tmp_path / long_name
    file_path.write_text("content")
    return file_path


@pytest.fixture
def special_char_filename(tmp_path):
    """Create a file with special characters in the name."""
    special_name = "test-file_with (special) chars & symbols.txt"
    file_path = tmp_path / special_name
    file_path.write_text("content")
    return file_path


@pytest.fixture
def unicode_filename(tmp_path):
    """Create a file with unicode characters."""
    unicode_name = "my_🔥_test.txt"
    file_path = tmp_path / unicode_name
    file_path.write_text("unicode content")
    return file_path


@pytest.fixture
def get_rendered_text():
    """Helper to get plain text from a rendered widget."""

    def _get(widget):
        content = widget.render()
        if content is None:
            return ""
        return content.plain

    return _get


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# Enable async tests
pytest_plugins = ["pytest_asyncio"]
