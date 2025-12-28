"""
Addable dictionary class for dictionaries that support addition operations.
"""

from typing import Dict, Any

from .add_dictionaries import add_dictionaries


class AddableDictionary(dict):
    """
    Dictionary subclass that supports addition operations.
    
    Allows dictionaries to be added together using the + operator,
    summing numeric values for common keys and adding new keys.
    """
    
    def __add__(self, other: Dict[str, Any]) -> "AddableDictionary":
        """
        Add another dictionary to this dictionary.

        Args:
            other: Dictionary to add to this one.

        Returns:
            New AddableDictionary with combined values.
        """
        return AddableDictionary(add_dictionaries(self, other))
    
    def __iadd__(self, other: Dict[str, Any]) -> "AddableDictionary":
        """
        In-place addition of another dictionary to this dictionary.

        Args:
            other: Dictionary to add to this one.

        Returns:
            Self with updated values.
        """
        result = add_dictionaries(self, other)
        self.update(result)
        return self

