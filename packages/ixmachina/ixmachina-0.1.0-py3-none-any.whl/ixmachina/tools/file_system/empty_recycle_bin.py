"""
File system tools for permanently emptying the recycle bin.
"""

from typing import Dict, Any
import os
import shutil

from .path_utils import path_exists
from .list_dir_contents import list_dir_contents
from .recycle_bin import get_recycle_bin_path, get_recycle_bin_index_path


def empty_recycle_bin() -> Dict[str, Any]:
    """
    Permanently delete all contents of the recycle bin.

    This function permanently deletes all files and directories in the recycle bin
    and clears the index. This operation cannot be undone.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - deleted_count: Number of items permanently deleted.
            - error: Error message if operation failed (None if successful).
    """
    try:
        recycle_bin = get_recycle_bin_path()
        index_path = get_recycle_bin_index_path()

        if not path_exists(recycle_bin):
            return {
                "success": True,
                "deleted_count": 0,
                "error": None,
            }

        deleted_count = 0
        errors = []

        # Get all items in recycle bin using list_dir_contents (separates files and directories)
        list_result = list_dir_contents(directory_path=recycle_bin, include_hidden=True)
        if not list_result["success"]:
            return {
                "success": False,
                "deleted_count": 0,
                "error": f"Error listing recycle bin: {list_result['error']}",
            }

        # Delete all files in recycle bin (skip index file)
        for file_item in list_result["files"]:
            file_path = file_item["path"]
            # Skip the index file
            if file_item["name"] == ".index.json":
                continue

            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

        # Delete all directories in recycle bin
        for dir_item in list_result["directories"]:
            dir_path = dir_item["path"]
            try:
                shutil.rmtree(dir_path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{dir_path}: {str(e)}")

        # Delete the index file
        if path_exists(index_path):
            try:
                os.remove(index_path)
            except Exception as e:
                errors.append(f"Index file: {str(e)}")

        if errors:
            return {
                "success": False,
                "deleted_count": deleted_count,
                "error": f"Some items could not be deleted: {'; '.join(errors)}",
            }

        return {
            "success": True,
            "deleted_count": deleted_count,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "deleted_count": 0,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "deleted_count": 0,
            "error": f"Error emptying recycle bin: {str(e)}",
        }

