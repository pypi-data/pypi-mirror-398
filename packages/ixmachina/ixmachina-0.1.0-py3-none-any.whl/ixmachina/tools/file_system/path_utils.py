"""
Path utility functions for file system operations.
"""

import os


def path_exists(path: str) -> bool:
    """
    Check if a path exists.

    Args:
        path: Path to check.

    Returns:
        True if path exists, False otherwise.
    """
    return os.path.exists(path)


def path_is_dir(path: str) -> bool:
    """
    Check if a path is a directory.

    Args:
        path: Path to check.

    Returns:
        True if path exists and is a directory, False otherwise.
    """
    return os.path.isdir(path)


def path_is_file(path: str) -> bool:
    """
    Check if a path is a file.

    Args:
        path: Path to check.

    Returns:
        True if path exists and is a file, False otherwise.
    """
    return os.path.isfile(path)

