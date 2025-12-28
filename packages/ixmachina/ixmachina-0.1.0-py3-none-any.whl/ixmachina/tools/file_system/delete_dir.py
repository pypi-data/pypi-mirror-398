"""
File system tools for deleting directories.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import shutil
from datetime import datetime

from .path_utils import path_exists, path_is_dir
from .memory import Action
from .recycle_bin import (
    ensure_recycle_bin_exists,
    generate_hash_folder_name,
    create_metadata,
    save_metadata,
    add_to_recycle_bin_index,
)

if TYPE_CHECKING:
    from .memory import FileSystemMemory


def delete_dir(
    dir_path: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Delete a directory by moving it to the recycle bin.

    Args:
        dir_path: Path to the directory to delete.
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - dir_path: Path to the directory that was deleted.
            - recycle_bin_path: Path where the directory was moved in the recycle bin.
            - error: Error message if operation failed (None if successful).
    """
    try:
        if not path_exists(dir_path):
            return {
                "success": False,
                "dir_path": dir_path,
                "recycle_bin_path": None,
                "error": f"Directory does not exist: {dir_path}",
            }

        if not path_is_dir(dir_path):
            return {
                "success": False,
                "dir_path": dir_path,
                "recycle_bin_path": None,
                "error": f"Path is not a directory: {dir_path}",
            }

        # Ensure recycle bin exists
        recycle_bin = ensure_recycle_bin_exists()

        # Generate unique hash folder
        timestamp = datetime.now().isoformat()
        hash_folder_name = generate_hash_folder_name(dir_path, timestamp)
        hash_folder = os.path.join(recycle_bin, hash_folder_name)
        os.makedirs(hash_folder, exist_ok=True)

        # Move directory to recycle bin
        dirname = os.path.basename(dir_path.rstrip(os.sep))
        recycle_bin_dir_path = os.path.join(hash_folder, dirname)
        shutil.move(dir_path, recycle_bin_dir_path)

        # Save metadata
        metadata = create_metadata(
            original_path=dir_path,
            recycle_bin_path=recycle_bin_dir_path,
            item_type="directory",
        )
        save_metadata(hash_folder, metadata)

        # Add to index for lookup
        add_to_recycle_bin_index(dir_path, recycle_bin_dir_path)

        # Track action in memory if provided (only after operation succeeds)
        if file_system_memory is not None:
            try:
                from .undelete import undelete

                undo_action = Action(
                    function_name="undelete",
                    function=undelete,
                    arguments={"recycle_bin_path": recycle_bin_dir_path},
                )

                action = Action(
                    function_name="delete_dir",
                    function=delete_dir,
                    arguments={"dir_path": dir_path},
                )
                file_system_memory.add_action(action=action, undo_action=undo_action)
            except Exception:
                # If memory tracking fails, don't affect the operation result
                pass

        return {
            "success": True,
            "dir_path": dir_path,
            "recycle_bin_path": recycle_bin_dir_path,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "dir_path": dir_path,
            "recycle_bin_path": None,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "dir_path": dir_path,
            "recycle_bin_path": None,
            "error": f"Error deleting directory: {str(e)}",
        }
