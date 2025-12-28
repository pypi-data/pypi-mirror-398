"""
File system tools for moving files into directories.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import shutil

from ..path_utils import path_exists, path_is_file, path_is_dir
from ..memory import Action

if TYPE_CHECKING:
    from ..memory import FileSystemMemory
    from .change_file_path import change_file_path


def move_file_into(
    source_path: str,
    destination_dir: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Move a file into a destination directory.

    The source file will be moved into the destination directory with the same name.

    Args:
        source_path: Path to the source file.
        destination_dir: Path to the destination directory (must exist).
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - source_path: Path to the source file.
            - destination_path: Final path where the file was moved.
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

        # Move file into destination directory with same name
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

        # Move the file
        shutil.move(source_path, final_destination)

        # Track action in memory if provided (only after operation succeeds)
        if file_system_memory is not None:
            try:
                from ..copy_move.change_file_path import change_file_path
                undo_action = Action(
                    function_name="change_file_path",
                    function=change_file_path,
                    arguments={
                        "source_path": final_destination,
                        "destination_path": source_path,
                    },
                )

                action = Action(
                    function_name="move_file_into",
                    function=move_file_into,
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
            "error": f"Error moving file: {str(e)}",
        }

