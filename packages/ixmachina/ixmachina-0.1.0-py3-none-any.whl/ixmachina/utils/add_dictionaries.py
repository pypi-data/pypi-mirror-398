"""
Dictionary addition utility function.
"""

from typing import Dict, Any


def add_dictionaries(
    dict1: Dict[str, Any],
    dict2: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Add two dictionaries by summing values of common keys and adding new keys.

    For common keys, numeric values are summed. For keys only in one dictionary,
    they are preserved. Non-numeric values in common keys will be overwritten
    by dict2's values.

    Args:
        dict1: First dictionary (base dictionary).
        dict2: Second dictionary (values to add to dict1).

    Returns:
        A new dictionary with combined values.

    Examples:
        >>> add_dictionaries({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {"a": 1, "b": 5, "c": 4}
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result:
            # If both values are numeric, add them
            if isinstance(result[key], (int, float)) and isinstance(value, (int, float)):
                result[key] = result[key] + value
            else:
                # Non-numeric or mixed types: use dict2's value
                result[key] = value
        else:
            # New key: add it
            result[key] = value
    
    return result

