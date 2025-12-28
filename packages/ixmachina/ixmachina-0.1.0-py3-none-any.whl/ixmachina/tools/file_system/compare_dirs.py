"""
File system tools for comparing directories.
"""

from typing import Dict, Any, List, Tuple
from collections import deque
import os

from .path_utils import path_exists, path_is_dir
from .list_dir_contents import list_dir_contents
from .compare_files import compare_files


def compare_dirs(
    dir_path_1: str,
    dir_path_2: str,
) -> Dict[str, Any]:
    """
    Compare two directories recursively to check if they have the same content.

    Compares directory structure and file contents level by level. Uses compare_files
    to compare individual files. Stops at the first difference found for efficiency.

    Note: File and directory name comparisons are case-sensitive. Symlinks are
    treated according to list_dir_contents behavior (typically as the type they
    point to).

    Args:
        dir_path_1: Path to the first directory.
        dir_path_2: Path to the second directory.

    Returns:
        A dictionary with the following keys:
            - success (bool): Whether the operation completed without internal error.
            - error: Error message if operation failed (None if successful).
            - are_equal (bool): Whether the directories are equal (only if success is True).
            - differences (List[Dict]): Description of the first difference found.
                Stops at the first difference found (early exit for efficiency).
                Each dictionary contains:
                    - type: Type of difference ("missing_in_dir1", "missing_in_dir2",
                      "file_different", "file_size_different", "file_error", "dir_error").
                    - path: Relative path to the item that differs.
                    - error: Error message (only present for "file_error" and "dir_error" types).
                Only present if success is True.
            - dir_path_1 (str): The first directory path.
            - dir_path_2 (str): The second directory path.
    """
    try:
        # Check if first directory exists
        if not path_exists(dir_path_1):
            return {
                "success": False,
                "dir_path_1": dir_path_1,
                "dir_path_2": dir_path_2,
                "error": f"First directory does not exist: {dir_path_1}",
            }

        # Check if first path is actually a directory
        if not path_is_dir(dir_path_1):
            return {
                "success": False,
                "dir_path_1": dir_path_1,
                "dir_path_2": dir_path_2,
                "error": f"First path is not a directory: {dir_path_1}",
            }

        # Check if second directory exists
        if not path_exists(dir_path_2):
            return {
                "success": False,
                "dir_path_1": dir_path_1,
                "dir_path_2": dir_path_2,
                "error": f"Second directory does not exist: {dir_path_2}",
            }

        # Check if second path is actually a directory
        if not path_is_dir(dir_path_2):
            return {
                "success": False,
                "dir_path_1": dir_path_1,
                "dir_path_2": dir_path_2,
                "error": f"Second path is not a directory: {dir_path_2}",
            }

        # Iteratively compare directories level by level
        differences: List[Dict[str, Any]] = []
        are_equal = _compare_dirs_iterative(
            root_dir_1=dir_path_1,
            root_dir_2=dir_path_2,
            differences=differences,
        )

        return {
            "success": True,
            "are_equal": are_equal,
            "differences": differences,
            "dir_path_1": dir_path_1,
            "dir_path_2": dir_path_2,
            "error": None,
        }
    except PermissionError as e:
        return {
            "success": False,
            "dir_path_1": dir_path_1,
            "dir_path_2": dir_path_2,
            "error": f"Permission denied: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "dir_path_1": dir_path_1,
            "dir_path_2": dir_path_2,
            "error": f"Error comparing directories: {str(e)}",
        }


def _compare_dirs_iterative(
    root_dir_1: str,
    root_dir_2: str,
    differences: List[Dict[str, Any]],
) -> bool:
    """
    Iteratively compare two directories level by level using a while loop.

    Processes directories one level at a time, comparing files and queuing
    subdirectories for the next level. Stops early at the first difference found
    for efficiency.

    Args:
        root_dir_1: Path to the first root directory.
        root_dir_2: Path to the second root directory.
        differences: List to accumulate differences found.

    Returns:
        True if directories are equal, False otherwise.
    """
    # Queue of directory pairs to compare: (dir_path_1, dir_path_2, relative_path)
    # Using deque for O(1) popleft() instead of O(n) pop(0)
    dir_queue: deque[Tuple[str, str, str]] = deque([(root_dir_1, root_dir_2, "")])

    while dir_queue:
        dir_path_1, dir_path_2, relative_path = dir_queue.popleft()

        # List contents of both directories
        list_result_1 = list_dir_contents(directory_path=dir_path_1, include_hidden=True)
        list_result_2 = list_dir_contents(directory_path=dir_path_2, include_hidden=True)

        if not list_result_1["success"] or not list_result_2["success"]:
            # Record directory listing errors in differences
            if not list_result_1["success"]:
                differences.append({
                    "type": "dir_error",
                    "path": relative_path if relative_path else ".",
                    "error": f"Failed to list directory {dir_path_1}: {list_result_1.get('error', 'Unknown error')}",
                })
            if not list_result_2["success"]:
                differences.append({
                    "type": "dir_error",
                    "path": relative_path if relative_path else ".",
                    "error": f"Failed to list directory {dir_path_2}: {list_result_2.get('error', 'Unknown error')}",
                })
            return False

        # Create dictionaries mapping file/directory names to paths
        files_1 = {f["name"]: f["path"] for f in list_result_1["files"]}
        dirs_1 = {d["name"]: d["path"] for d in list_result_1["directories"]}
        files_2 = {f["name"]: f["path"] for f in list_result_2["files"]}
        dirs_2 = {d["name"]: d["path"] for d in list_result_2["directories"]}

        # Compare file names separately from directory names
        file_names_1 = set(files_1.keys())
        file_names_2 = set(files_2.keys())
        dir_names_1 = set(dirs_1.keys())
        dir_names_2 = set(dirs_2.keys())

        # Check if file lists have the same names
        if file_names_1 != file_names_2:
            # Files missing in dir_1
            missing_files_in_1 = file_names_2 - file_names_1
            for file_name in missing_files_in_1:
                missing_rel_path = os.path.join(relative_path, file_name) if relative_path else file_name
                differences.append({
                    "type": "missing_in_dir1",
                    "path": missing_rel_path,
                })

            # Files missing in dir_2
            missing_files_in_2 = file_names_1 - file_names_2
            for file_name in missing_files_in_2:
                missing_rel_path = os.path.join(relative_path, file_name) if relative_path else file_name
                differences.append({
                    "type": "missing_in_dir2",
                    "path": missing_rel_path,
                })
            # Found differences, stop here
            return False

        # Check if directory lists have the same names
        if dir_names_1 != dir_names_2:
            # Directories missing in dir_1
            missing_dirs_in_1 = dir_names_2 - dir_names_1
            for dir_name in missing_dirs_in_1:
                missing_rel_path = os.path.join(relative_path, dir_name) if relative_path else dir_name
                differences.append({
                    "type": "missing_in_dir1",
                    "path": missing_rel_path,
                })

            # Directories missing in dir_2
            missing_dirs_in_2 = dir_names_1 - dir_names_2
            for dir_name in missing_dirs_in_2:
                missing_rel_path = os.path.join(relative_path, dir_name) if relative_path else dir_name
                differences.append({
                    "type": "missing_in_dir2",
                    "path": missing_rel_path,
                })
            # Found differences, stop here
            return False

        # Pair files by name and compare them
        common_files = set(files_1.keys()) & set(files_2.keys())
        for file_name in common_files:
            file_path_1 = files_1[file_name]
            file_path_2 = files_2[file_name]
            file_relative_path = os.path.join(relative_path, file_name) if relative_path else file_name

            # Compare files using compare_files
            compare_result = compare_files(file_path_1=file_path_1, file_path_2=file_path_2)

            if not compare_result["success"]:
                differences.append({
                    "type": "file_error",
                    "path": file_relative_path,
                    "error": compare_result["error"],
                })
                # Found difference, stop here
                return False
            elif not compare_result["are_equal"]:
                if not compare_result["sizes_equal"]:
                    differences.append({
                        "type": "file_size_different",
                        "path": file_relative_path,
                    })
                else:
                    differences.append({
                        "type": "file_different",
                        "path": file_relative_path,
                    })
                # Found difference, stop here
                return False

        # Pair directories by name and add them to queue for next level
        common_dirs = set(dirs_1.keys()) & set(dirs_2.keys())
        for dir_name in common_dirs:
            subdir_path_1 = dirs_1[dir_name]
            subdir_path_2 = dirs_2[dir_name]
            subdir_relative_path = os.path.join(relative_path, dir_name) if relative_path else dir_name

            # Add to queue for next iteration
            dir_queue.append((subdir_path_1, subdir_path_2, subdir_relative_path))

    # All levels compared successfully
    return True

