"""Utility functions for textual-filelink."""


def sanitize_id(name: str) -> str:
    """Convert name to valid widget ID.

    Sanitizes for use as Textual widget ID: lowercase, spaces→hyphens,
    path separators→hyphens, keep only alphanumeric/hyphens/underscores.

    Parameters
    ----------
    name : str
        Name to sanitize (can contain spaces, paths, special characters)

    Returns
    -------
    str
        Sanitized ID containing only lowercase alphanumeric characters,
        hyphens, and underscores

    Examples
    --------
    >>> sanitize_id("Run Tests")
    'run-tests'
    >>> sanitize_id("src/main.py")
    'src-main-py'
    >>> sanitize_id("Build Project!")
    'build-project-'
    >>> sanitize_id("src\\\\file.py")
    'src-file-py'
    """
    # Convert to lowercase
    sanitized = name.lower()

    # Replace spaces and path separators with hyphens
    sanitized = sanitized.replace(" ", "-")
    sanitized = sanitized.replace("/", "-")
    sanitized = sanitized.replace("\\", "-")

    # Keep only alphanumeric, hyphens, and underscores
    return "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in sanitized)


def format_keyboard_shortcuts(keys: list[str]) -> str:
    """Format keyboard shortcuts as (key1/key2/key3).

    Parameters
    ----------
    keys : list[str]
        List of keyboard shortcut keys.

    Returns
    -------
    str
        Formatted string like "(enter/o)" or empty string if no keys.

    Examples
    --------
    >>> format_keyboard_shortcuts(["enter", "o"])
    '(enter/o)'
    >>> format_keyboard_shortcuts(["space", "p"])
    '(space/p)'
    >>> format_keyboard_shortcuts([])
    ''
    """
    if not keys:
        return ""
    return f"({'/'.join(keys)})"
