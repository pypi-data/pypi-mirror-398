"""
File system tools for undeleting files and directories from recycle bin.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import shutil

from .path_utils import path_exists
from .recycle_bin import (
    load_metadata,
    find_in_recycle_bin_index,
    remove_from_recycle_bin_index,
)

if TYPE_CHECKING:
    from .memory import FileSystemMemory


def undelete(
    recycle_bin_path: Optional[str] = None,
    original_path: Optional[str] = None,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Restore a file or directory from the recycle bin to its original location.

    Either recycle_bin_path or original_path must be provided.

    Args:
        recycle_bin_path: Path to the item in the recycle bin. Optional if original_path is provided.
        original_path: Original path of the deleted item. Optional if recycle_bin_path is provided.
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - original_path: Path where the item was restored.
            - recycle_bin_path: Path where the item was in the recycle bin.
            - error: Error message if operation failed (None if successful).
    """
    try:
        # If original_path is provided, look it up in the index
        if original_path and not recycle_bin_path:
            recycle_bin_path = find_in_recycle_bin_index(original_path)
            if not recycle_bin_path:
                return {
                    "success": False,
                    "original_path": original_path,
                    "recycle_bin_path": None,
                    "error": f"Item not found in recycle bin index: {original_path}",
                }

        if not recycle_bin_path:
            return {
                "success": False,
                "original_path": original_path,
                "recycle_bin_path": None,
                "error": "Either recycle_bin_path or original_path must be provided.",
            }

        if not path_exists(recycle_bin_path):
            return {
                "success": False,
                "original_path": original_path,
                "recycle_bin_path": recycle_bin_path,
                "error": f"Item does not exist in recycle bin: {recycle_bin_path}",
            }

        # Find metadata - check parent directory (hash folder)
        parent_dir = os.path.dirname(recycle_bin_path)
        metadata = load_metadata(parent_dir)

        if not metadata:
            return {
                "success": False,
                "original_path": None,
                "recycle_bin_path": recycle_bin_path,
                "error": f"Metadata not found for item: {recycle_bin_path}",
            }

        original_path = metadata["original_path"]

        # Check if original location already exists
        if path_exists(original_path):
            return {
                "success": False,
                "original_path": original_path,
                "recycle_bin_path": recycle_bin_path,
                "error": f"Original location already exists: {original_path}. Delete it first if you want to restore.",
            }

        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(original_path)
        if parent_dir and not path_exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # Move item back to original location
        shutil.move(recycle_bin_path, original_path)

        # Remove from index
        remove_from_recycle_bin_index(original_path)

        # Track action in memory if provided (only after operation succeeds)
        if file_system_memory is not None:
            try:
                from .memory import Action
                from .delete_file import delete_file
                from .delete_dir import delete_dir

                # Determine which delete function to use for undo
                item_type = metadata.get("item_type", "file")
                if item_type == "directory":
                    delete_func = delete_dir
                    delete_args = {"dir_path": original_path}
                else:
                    delete_func = delete_file
                    delete_args = {"file_path": original_path}

                undo_action = Action(
                    function_name=delete_func.__name__,
                    function=delete_func,
                    arguments=delete_args,
                )

                action = Action(
                    function_name="undelete",
                    function=undelete,
                    arguments={"recycle_bin_path": recycle_bin_path},
                )
                file_system_memory.add_action(action=action, undo_action=undo_action)
            except Exception:
                # If memory tracking fails, don't affect the operation result
                pass

        return {
            "success": True,
            "original_path": original_path,
            "recycle_bin_path": recycle_bin_path,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "original_path": None,
            "recycle_bin_path": recycle_bin_path,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "original_path": None,
            "recycle_bin_path": recycle_bin_path,
            "error": f"Error undeleting item: {str(e)}",
        }

