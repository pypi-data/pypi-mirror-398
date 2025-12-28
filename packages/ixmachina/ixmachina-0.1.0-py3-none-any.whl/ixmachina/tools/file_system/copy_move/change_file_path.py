"""
File system tools for changing file paths (moving to exact path).
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import shutil

from ..path_utils import path_exists, path_is_file
from ..memory import Action

if TYPE_CHECKING:
    from ..memory import FileSystemMemory


def change_file_path(
    source_path: str,
    destination_path: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Move a file to an exact destination path.

    The source file will be moved/renamed to the exact destination path.

    Args:
        source_path: Path to the source file.
        destination_path: Exact path where the file should be moved to.
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

        # Check if destination exists
        if path_exists(destination_path):
            return {
                "success": False,
                "source_path": source_path,
                "destination_path": destination_path,
                "error": f"Destination already exists: {destination_path}. Overwrite is not allowed.",
            }

        # Create destination directory if it doesn't exist
        destination_dir = os.path.dirname(destination_path)
        if destination_dir and not path_exists(destination_dir):
            os.makedirs(destination_dir, exist_ok=True)

        # Move the file
        shutil.move(source_path, destination_path)

        # Track action in memory if provided (only after operation succeeds)
        if file_system_memory is not None:
            try:
                undo_action = Action(
                    function_name="change_file_path",
                    function=change_file_path,
                    arguments={
                        "source_path": destination_path,
                        "destination_path": source_path,
                    },
                )

                action = Action(
                    function_name="change_file_path",
                    function=change_file_path,
                    arguments={
                        "source_path": source_path,
                        "destination_path": destination_path,
                    },
                )
                file_system_memory.add_action(action=action, undo_action=undo_action)
            except Exception:
                # If memory tracking fails, don't affect the operation result
                pass

        return {
            "success": True,
            "source_path": source_path,
            "destination_path": destination_path,
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

