"""
File system tools for cloning files or directories to exact paths.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

from ..path_utils import path_exists, path_is_file, path_is_dir
from .clone_file_to_path import clone_file_to_path
from .clone_dir_to_path import clone_dir_to_path

if TYPE_CHECKING:
    from ..memory import FileSystemMemory


def clone_to_path(
    source_path: str,
    destination_path: str,
    file_system_memory: Optional["FileSystemMemory"] = None,
) -> Dict[str, Any]:
    """
    Clone a file or directory to an exact destination path.

    Automatically detects whether the source is a file or directory and uses
    the appropriate operation. The source will be copied to the exact destination
    path, and the source remains unchanged.

    Args:
        source_path: Path to the source file or directory.
        destination_path: Exact path where the item should be copied to.
        file_system_memory: Optional FileSystemMemory instance to track actions.
            Default: None.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - source_path: Path to the source item.
            - destination_path: Final path where the item was copied.
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
        return clone_file_to_path(
            source_path=source_path,
            destination_path=destination_path,
            file_system_memory=file_system_memory,
        )
    elif path_is_dir(source_path):
        return clone_dir_to_path(
            source_path=source_path,
            destination_path=destination_path,
            file_system_memory=file_system_memory,
        )
    else:
        return {
            "success": False,
            "source_path": source_path,
            "destination_path": None,
            "error": f"Source path is neither a file nor a directory: {source_path}",
        }

