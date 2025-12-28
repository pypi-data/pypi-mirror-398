"""
File system tools for comparing files.
"""

from typing import Dict, Any
import os
import filecmp

from .path_utils import path_exists, path_is_file


def compare_files(
    file_path_1: str,
    file_path_2: str,
) -> Dict[str, Any]:
    """
    Compare two files to check if they have the same content.

    Args:
        file_path_1: Path to the first file.
        file_path_2: Path to the second file.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the operation was successful.
            - are_equal: Boolean indicating if the files have the same content.
                Only present if success is True.
            - sizes_equal: Boolean indicating if the files have the same size.
                Only present if success is True.
            - file_path_1: Path to the first file.
            - file_path_2: Path to the second file.
            - error: Error message if operation failed (None if successful).
    """
    try:
        # Check if first file exists
        if not path_exists(file_path_1):
            return {
                "success": False,
                "file_path_1": file_path_1,
                "file_path_2": file_path_2,
                "error": f"First file does not exist: {file_path_1}",
            }

        # Check if first file is actually a file
        if not path_is_file(file_path_1):
            return {
                "success": False,
                "file_path_1": file_path_1,
                "file_path_2": file_path_2,
                "error": f"First path is not a file: {file_path_1}",
            }

        # Check if second file exists
        if not path_exists(file_path_2):
            return {
                "success": False,
                "file_path_1": file_path_1,
                "file_path_2": file_path_2,
                "error": f"Second file does not exist: {file_path_2}",
            }

        # Check if second file is actually a file
        if not path_is_file(file_path_2):
            return {
                "success": False,
                "file_path_1": file_path_1,
                "file_path_2": file_path_2,
                "error": f"Second path is not a file: {file_path_2}",
            }

        # Check file sizes first - if different, files are definitely not equal
        size_1 = os.path.getsize(file_path_1)
        size_2 = os.path.getsize(file_path_2)
        sizes_equal = size_1 == size_2
        
        if not sizes_equal:
            return {
                "success": True,
                "are_equal": False,
                "sizes_equal": False,
                "file_path_1": file_path_1,
                "file_path_2": file_path_2,
                "error": None,
            }

        # Compare files using filecmp (handles both text and binary files)
        are_equal = filecmp.cmp(file_path_1, file_path_2, shallow=False)

        return {
            "success": True,
            "are_equal": are_equal,
            "sizes_equal": True,
            "file_path_1": file_path_1,
            "file_path_2": file_path_2,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "file_path_1": file_path_1,
            "file_path_2": file_path_2,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "file_path_1": file_path_1,
            "file_path_2": file_path_2,
            "error": f"Error comparing files: {str(e)}",
        }

