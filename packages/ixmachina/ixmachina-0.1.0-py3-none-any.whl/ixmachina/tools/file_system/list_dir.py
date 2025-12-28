"""
File system tools for listing directory contents.
"""

from typing import Dict, Any, List, Optional
import os

from .path_utils import path_exists, path_is_dir


def list_dir(
    directory_path: str,
    include_hidden: bool = False,
) -> Dict[str, Any]:
    """
    List the contents of a directory.

    Args:
        directory_path: Path to the directory to list.
        include_hidden: If True, include hidden files and directories (starting with '.').
            Default: False.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - items: List of dictionaries, each containing:
                - name: Name of the item (file or directory).
                - type: Type of item ("file" or "directory").
                - path: Full path to the item.
            - error: Error message if operation failed (None if successful).
    """
    try:
        if not path_exists(directory_path):
            return {
                "success": False,
                "items": [],
                "error": f"Directory does not exist: {directory_path}",
            }

        if not path_is_dir(directory_path):
            return {
                "success": False,
                "items": [],
                "error": f"Path is not a directory: {directory_path}",
            }

        items = []
        for item_name in os.listdir(directory_path):
            # Skip hidden files if include_hidden is False
            if not include_hidden and item_name.startswith("."):
                continue

            item_path = os.path.join(directory_path, item_name)
            item_type = "directory" if path_is_dir(item_path) else "file"

            items.append({
                "name": item_name,
                "type": item_type,
                "path": item_path,
            })

        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

        return {
            "success": True,
            "items": items,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "items": [],
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "items": [],
            "error": f"Error listing directory: {str(e)}",
        }

