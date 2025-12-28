"""
File system tools for listing directory contents with separated files and directories.
"""

from typing import Dict, Any, List
import os

from .list_dir import list_dir


def list_dir_contents(
    directory_path: str,
    include_hidden: bool = False,
) -> Dict[str, Any]:
    """
    List the contents of a directory, separated into files and directories.

    Args:
        directory_path: Path to the directory to list.
        include_hidden: If True, include hidden files and directories (starting with '.').
            Default: False.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - files: List of dictionaries for files, each containing:
                - name: Name of the file.
                - path: Full path to the file.
            - directories: List of dictionaries for directories, each containing:
                - name: Name of the directory.
                - path: Full path to the directory.
            - error: Error message if operation failed (None if successful).
    """
    # Use list_dir to get all items
    result = list_dir(directory_path=directory_path, include_hidden=include_hidden)
    
    if not result["success"]:
        return {
            "success": False,
            "files": [],
            "directories": [],
            "error": result["error"],
        }

    # Separate files and directories
    files = []
    directories = []

    for item in result["items"]:
        item_dict = {
            "name": item["name"],
            "path": item["path"],
        }
        if item["type"] == "file":
            files.append(item_dict)
        else:
            directories.append(item_dict)

    return {
        "success": True,
        "files": files,
        "directories": directories,
        "error": None,
    }

