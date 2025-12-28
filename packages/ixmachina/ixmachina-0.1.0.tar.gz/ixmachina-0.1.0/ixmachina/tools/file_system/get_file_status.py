"""
File system tools for getting file status information.
"""

from typing import Dict, Any, Optional
import os
import stat
from datetime import datetime

from .path_utils import path_exists, path_is_file, path_is_dir


def get_file_status(
    file_path: str,
) -> Dict[str, Any]:
    """
    Get status information about a file or directory.

    Args:
        file_path: Path to the file or directory.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - exists: Boolean indicating if the path exists.
            - is_file: Boolean indicating if the path is a file (None if path doesn't exist).
            - is_directory: Boolean indicating if the path is a directory (None if path doesn't exist).
            - size: Size in bytes (None if path doesn't exist or is a directory).
            - created_time: Creation time as ISO format string (None if not available).
            - modified_time: Last modification time as ISO format string (None if path doesn't exist).
            - accessed_time: Last access time as ISO format string (None if path doesn't exist).
            - permissions: File permissions as octal string (e.g., "0644") (None if path doesn't exist).
            - error: Error message if operation failed (None if successful).
    """
    try:
        if not path_exists(file_path):
            return {
                "success": True,
                "exists": False,
                "is_file": None,
                "is_directory": None,
                "size": None,
                "created_time": None,
                "modified_time": None,
                "accessed_time": None,
                "permissions": None,
                "error": None,
            }

        stat_info = os.stat(file_path)
        is_file = path_is_file(file_path)
        is_directory = path_is_dir(file_path)

        # Get times
        modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        accessed_time = datetime.fromtimestamp(stat_info.st_atime).isoformat()

        # Try to get creation time (platform-dependent)
        try:
            created_time = datetime.fromtimestamp(stat_info.st_birthtime).isoformat()
        except AttributeError:
            # st_birthtime not available on this platform, use st_ctime as fallback
            created_time = datetime.fromtimestamp(stat_info.st_ctime).isoformat()

        # Get permissions as octal string
        permissions = oct(stat_info.st_mode)[-3:]

        # Get size (only for files)
        size = stat_info.st_size if is_file else None

        return {
            "success": True,
            "exists": True,
            "is_file": is_file,
            "is_directory": is_directory,
            "size": size,
            "created_time": created_time,
            "modified_time": modified_time,
            "accessed_time": accessed_time,
            "permissions": permissions,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "exists": None,
            "is_file": None,
            "is_directory": None,
            "size": None,
            "created_time": None,
            "modified_time": None,
            "accessed_time": None,
            "permissions": None,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "exists": None,
            "is_file": None,
            "is_directory": None,
            "size": None,
            "created_time": None,
            "modified_time": None,
            "accessed_time": None,
            "permissions": None,
            "error": f"Error getting file status: {str(e)}",
        }

