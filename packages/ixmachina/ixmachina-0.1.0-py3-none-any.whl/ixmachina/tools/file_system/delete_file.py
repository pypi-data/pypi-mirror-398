"""
File system tools for deleting files.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import shutil
from datetime import datetime

from .path_utils import path_exists, path_is_file
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


def delete_file(
    file_path: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Delete a file by moving it to the recycle bin.

    Args:
        file_path: Path to the file to delete.
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - file_path: Path to the file that was deleted.
            - recycle_bin_path: Path where the file was moved in the recycle bin.
            - error: Error message if operation failed (None if successful).
    """
    try:
        if not path_exists(file_path):
            return {
                "success": False,
                "file_path": file_path,
                "recycle_bin_path": None,
                "error": f"File does not exist: {file_path}",
            }

        if not path_is_file(file_path):
            return {
                "success": False,
                "file_path": file_path,
                "recycle_bin_path": None,
                "error": f"Path is not a file: {file_path}",
            }

        # Ensure recycle bin exists
        recycle_bin = ensure_recycle_bin_exists()

        # Generate unique hash folder
        timestamp = datetime.now().isoformat()
        hash_folder_name = generate_hash_folder_name(file_path, timestamp)
        hash_folder = os.path.join(recycle_bin, hash_folder_name)
        os.makedirs(hash_folder, exist_ok=True)

        # Move file to recycle bin
        filename = os.path.basename(file_path)
        recycle_bin_file_path = os.path.join(hash_folder, filename)
        shutil.move(file_path, recycle_bin_file_path)

        # Save metadata
        metadata = create_metadata(
            original_path=file_path,
            recycle_bin_path=recycle_bin_file_path,
            item_type="file",
        )
        save_metadata(hash_folder, metadata)

        # Add to index for lookup
        add_to_recycle_bin_index(file_path, recycle_bin_file_path)

        # Track action in memory if provided (only after operation succeeds)
        if file_system_memory is not None:
            try:
                from .undelete import undelete

                undo_action = Action(
                    function_name="undelete",
                    function=undelete,
                    arguments={"recycle_bin_path": recycle_bin_file_path},
                )

                action = Action(
                    function_name="delete_file",
                    function=delete_file,
                    arguments={"file_path": file_path},
                )
                file_system_memory.add_action(action=action, undo_action=undo_action)
            except Exception:
                # If memory tracking fails, don't affect the operation result
                pass

        return {
            "success": True,
            "file_path": file_path,
            "recycle_bin_path": recycle_bin_file_path,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "file_path": file_path,
            "recycle_bin_path": None,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path,
            "recycle_bin_path": None,
            "error": f"Error deleting file: {str(e)}",
        }
