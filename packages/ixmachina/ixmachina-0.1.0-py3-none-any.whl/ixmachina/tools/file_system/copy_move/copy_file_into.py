"""
File system tools for copying files into directories.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import shutil

from ..path_utils import path_exists, path_is_file, path_is_dir
from ..memory import Action
from ..delete_file import delete_file

if TYPE_CHECKING:
    from ..memory import FileSystemMemory


def copy_file_into(
    source_path: str,
    destination_dir: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Copy a file into a destination directory.

    The source file will be copied into the destination directory with the same name.

    Args:
        source_path: Path to the source file.
        destination_dir: Path to the destination directory (must exist).
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - source_path: Path to the source file.
            - destination_path: Final path where the file was copied.
            - error: Error message if operation failed (None if successful).
    """
    try:
        if not path_exists(source_path):
            return {
                "success": False,
                "source_path": source_path,
                "destination_path": None,
                "error": f"Source file does not exist: {source_path}",
            }

        if not path_is_file(source_path):
            return {
                "success": False,
                "source_path": source_path,
                "destination_path": None,
                "error": f"Source path is not a file: {source_path}",
            }

        if not path_exists(destination_dir):
            return {
                "success": False,
                "source_path": source_path,
                "destination_path": None,
                "error": f"Destination directory does not exist: {destination_dir}",
            }

        if not path_is_dir(destination_dir):
            return {
                "success": False,
                "source_path": source_path,
                "destination_path": None,
                "error": f"Destination path is not a directory: {destination_dir}",
            }

        # Copy file into destination directory with same name
        source_filename = os.path.basename(source_path)
        final_destination = os.path.join(destination_dir, source_filename)

        # Check if destination exists
        if path_exists(final_destination):
            return {
                "success": False,
                "source_path": source_path,
                "destination_path": final_destination,
                "error": f"Destination already exists: {final_destination}. Overwrite is not allowed.",
            }

        # Copy the file
        shutil.copy2(source_path, final_destination)

        # Track action in memory if provided (only after operation succeeds)
        if file_system_memory is not None:
            try:
                undo_action = Action(
                    function_name="delete_file",
                    function=delete_file,
                    arguments={"file_path": final_destination},
                )

                action = Action(
                    function_name="copy_file_into",
                    function=copy_file_into,
                    arguments={
                        "source_path": source_path,
                        "destination_dir": destination_dir,
                    },
                )
                file_system_memory.add_action(action=action, undo_action=undo_action)
            except Exception:
                # If memory tracking fails, don't affect the operation result
                pass

        return {
            "success": True,
            "source_path": source_path,
            "destination_path": final_destination,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "source_path": source_path,
            "destination_path": None,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "source_path": source_path,
            "destination_path": None,
            "error": f"Error copying file: {str(e)}",
        }

