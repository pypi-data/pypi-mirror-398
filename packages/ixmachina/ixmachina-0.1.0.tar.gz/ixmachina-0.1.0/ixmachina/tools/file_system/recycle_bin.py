"""
Recycle bin utilities for file system operations.
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .path_utils import path_exists


def get_recycle_bin_path() -> str:
    """
    Get the path to the recycle bin directory.

    Returns:
        Path to the recycle bin directory.
    """
    # Use ~/.ix_recycle_bin as the default location
    home_dir = os.path.expanduser("~")
    recycle_bin = os.path.join(home_dir, ".ix_recycle_bin")
    return recycle_bin


def get_recycle_bin_index_path() -> str:
    """
    Get the path to the recycle bin index file.

    Returns:
        Path to the recycle bin index file.
    """
    recycle_bin = get_recycle_bin_path()
    return os.path.join(recycle_bin, ".index.json")


def ensure_recycle_bin_exists() -> str:
    """
    Ensure the recycle bin directory exists.

    Returns:
        Path to the recycle bin directory.
    """
    recycle_bin = get_recycle_bin_path()
    os.makedirs(recycle_bin, exist_ok=True)
    return recycle_bin


def generate_hash_folder_name(original_path: str, timestamp: str) -> str:
    """
    Generate a unique hash-based folder name for the recycle bin.

    Args:
        original_path: The original path of the file/directory.
        timestamp: Timestamp string.

    Returns:
        Hash-based folder name.
    """
    # Create a hash from original path + timestamp
    hash_input = f"{original_path}:{timestamp}"
    hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
    # Use first 16 characters for folder name
    return hash_value[:16]


def create_metadata(
    original_path: str,
    recycle_bin_path: str,
    item_type: str,
) -> Dict[str, Any]:
    """
    Create metadata for a deleted item.

    Args:
        original_path: Original path of the deleted item.
        recycle_bin_path: Path where the item is stored in recycle bin.
        item_type: Type of item ("file" or "directory").

    Returns:
        Dictionary with metadata.
    """
    return {
        "original_path": original_path,
        "recycle_bin_path": recycle_bin_path,
        "item_type": item_type,
        "deleted_at": datetime.now().isoformat(),
    }


def save_metadata(
    hash_folder: str,
    metadata: Dict[str, Any],
) -> str:
    """
    Save metadata to a JSON file in the hash folder.

    Args:
        hash_folder: Path to the hash folder.
        metadata: Metadata dictionary to save.

    Returns:
        Path to the metadata file.
    """
    metadata_path = os.path.join(hash_folder, ".metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    return metadata_path


def load_metadata(hash_folder: str) -> Optional[Dict[str, Any]]:
    """
    Load metadata from a hash folder.

    Args:
        hash_folder: Path to the hash folder.

    Returns:
        Metadata dictionary if found, None otherwise.
    """
    metadata_path = os.path.join(hash_folder, ".metadata.json")
    if not path_exists(metadata_path):
        return None

    try:
        with open(metadata_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def load_recycle_bin_index() -> Dict[str, str]:
    """
    Load the recycle bin index that maps original paths to recycle bin paths.

    Returns:
        Dictionary mapping original paths to recycle bin paths.
    """
    index_path = get_recycle_bin_index_path()
    if not path_exists(index_path):
        return {}

    try:
        with open(index_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_recycle_bin_index(index: Dict[str, str]) -> None:
    """
    Save the recycle bin index.

    Uses file mode "w" which overwrites the file if it exists. This function
    will not fail because the file already exists - it will overwrite it.
    It may fail for other reasons (permissions, disk full, file locked), but
    not because the file cannot be overwritten.

    Args:
        index: Dictionary mapping original paths to recycle bin paths.
    """
    index_path = get_recycle_bin_index_path()
    ensure_recycle_bin_exists()
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def add_to_recycle_bin_index(original_path: str, recycle_bin_path: str) -> None:
    """
    Add an entry to the recycle bin index.

    Args:
        original_path: Original path of the deleted item.
        recycle_bin_path: Path where the item is stored in recycle bin.
    """
    index = load_recycle_bin_index()
    index[original_path] = recycle_bin_path
    save_recycle_bin_index(index)


def remove_from_recycle_bin_index(original_path: str) -> None:
    """
    Remove an entry from the recycle bin index.

    Args:
        original_path: Original path to remove from index.
    """
    index = load_recycle_bin_index()
    if original_path in index:
        del index[original_path]
        save_recycle_bin_index(index)


def find_in_recycle_bin_index(original_path: str) -> Optional[str]:
    """
    Find a recycle bin path by original path.

    Args:
        original_path: Original path to look up.

    Returns:
        Recycle bin path if found, None otherwise.
    """
    index = load_recycle_bin_index()
    return index.get(original_path)

