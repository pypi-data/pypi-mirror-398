"""
File system tools for emptying directories.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os

from .path_utils import path_exists, path_is_dir
from .list_dir_contents import list_dir_contents
from .delete_file import delete_file
from .delete_dir import delete_dir

if TYPE_CHECKING:
    from .memory import FileSystemMemory


def empty_dir(
    dir_path: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Delete all contents inside a directory by moving them to the recycle bin.

    This function uses delete_file and delete_dir to move all contents to the
    recycle bin. The directory itself remains empty after this operation.

    Args:
        dir_path: Path to the directory to empty.
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - dir_path: Path to the directory that was emptied.
            - deleted_items: List of paths that were deleted.
            - error: Error message if operation failed (None if successful).
    """
    try:
        if not path_exists(dir_path):
            return {
                "success": False,
                "dir_path": dir_path,
                "deleted_items": [],
                "error": f"Directory does not exist: {dir_path}",
            }

        if not path_is_dir(dir_path):
            return {
                "success": False,
                "dir_path": dir_path,
                "deleted_items": [],
                "error": f"Path is not a directory: {dir_path}",
            }

        # Get all items to delete using list_dir_contents (separates files and directories)
        list_result = list_dir_contents(directory_path=dir_path, include_hidden=True)
        if not list_result["success"]:
            return {
                "success": False,
                "dir_path": dir_path,
                "deleted_items": [],
                "error": f"Error listing directory: {list_result['error']}",
            }

        deleted_items = []
        errors = []

        # Delete files first
        for file_item in list_result["files"]:
            file_path = file_item["path"]
            result = delete_file(file_path=file_path, file_system_memory=file_system_memory)
            if result["success"]:
                deleted_items.append(file_path)
            else:
                errors.append(f"{file_path}: {result['error']}")

        # Delete directories
        for dir_item in list_result["directories"]:
            dir_path_item = dir_item["path"]
            result = delete_dir(dir_path=dir_path_item, file_system_memory=file_system_memory)
            if result["success"]:
                deleted_items.append(dir_path_item)
            else:
                errors.append(f"{dir_path_item}: {result['error']}")

        if errors:
            return {
                "success": False,
                "dir_path": dir_path,
                "deleted_items": deleted_items,
                "error": f"Some items could not be deleted: {'; '.join(errors)}",
            }

        return {
            "success": True,
            "dir_path": dir_path,
            "deleted_items": deleted_items,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "dir_path": dir_path,
            "deleted_items": [],
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "dir_path": dir_path,
            "deleted_items": [],
            "error": f"Error emptying directory: {str(e)}",
        }

