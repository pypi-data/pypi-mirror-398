"""
Utility functions for normalizing dictionary keys.
"""

from typing import Dict, Any


def normalize_key(key: str) -> str:
    """
    Normalize a single dictionary key for consistent lookup.
    
    Converts to lowercase and replaces hyphens with underscores.
    
    Args:
        key: The key to normalize.
    
    Returns:
        Normalized key (lowercase, hyphens replaced with underscores).
    
    Example:
        normalize_key("GPT-4.1") -> "gpt_4.1"
        normalize_key("gpt_4o_mini") -> "gpt_4o_mini"
    """
    return key.lower().replace("-", "_")


def normalize_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all keys in a dictionary.
    
    Converts all keys to lowercase and replaces hyphens with underscores.
    Preserves the original values.
    
    Args:
        data: Dictionary with keys to normalize.
    
    Returns:
        New dictionary with normalized keys.
    
    Example:
        normalize_keys({"GPT-4.1": 3.0, "gpt-4o": 2.5})
        -> {"gpt_4.1": 3.0, "gpt_4o": 2.5}
    """
    return {normalize_key(key): value for key, value in data.items()}

