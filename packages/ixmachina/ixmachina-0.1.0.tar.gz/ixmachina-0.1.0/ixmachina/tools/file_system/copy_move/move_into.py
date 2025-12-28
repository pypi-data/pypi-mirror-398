"""
File system tools for moving files or directories into other directories.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

from ..path_utils import path_exists, path_is_file, path_is_dir
from .move_file_into import move_file_into
from .move_dir_into import move_dir_into

if TYPE_CHECKING:
    from ..memory import FileSystemMemory


def move_into(
    source_path: str,
    destination_dir: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Move a file or directory into a destination directory.

    Automatically detects whether the source is a file or directory and uses
    the appropriate operation. The source will be moved inside the destination
    directory, keeping its original name.

    Args:
        source_path: Path to the source file or directory.
        destination_dir: Path to the destination directory (must exist).
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - source_path: Path to the source item.
            - destination_path: Final path where the item was moved.
            - error: Error message if operation failed (None if successful).
    """
    if not path_exists(source_path):
        return {
            "success": False,
            "source_path": source_path,
            "destination_path": None,
            "error": f"Source does not exist: {source_path}",
        }

    if path_is_file(source_path):
        return move_file_into(
            source_path=source_path,
            destination_dir=destination_dir,
            file_system_memory=file_system_memory,
        )
    elif path_is_dir(source_path):
        return move_dir_into(
            source_path=source_path,
            destination_dir=destination_dir,
            file_system_memory=file_system_memory,
        )
    else:
        return {
            "success": False,
            "source_path": source_path,
            "destination_path": None,
            "error": f"Source path is neither a file nor a directory: {source_path}",
        }

