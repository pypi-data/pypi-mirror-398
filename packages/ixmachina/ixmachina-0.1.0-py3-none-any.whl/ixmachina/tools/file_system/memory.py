"""
File system memory for tracking actions and their undo operations.
"""

from typing import Optional, Dict, Any, List, Tuple, Callable
import os
import shutil
import os
import shutil


class Action:
    """
    Represents a file system action.

    Attributes:
        function_name: Name of the function that was called.
        function: The callable function.
        arguments: Dictionary of arguments passed to the function.
    """

    def __init__(
        self,
        function_name: str,
        function: Callable,
        arguments: Dict[str, Any],
    ) -> None:
        """
        Initialize an Action.

        Args:
            function_name: Name of the function that was called.
            function: The callable function.
            arguments: Dictionary of arguments passed to the function.
        """
        self.function_name = function_name
        self.function = function
        self.arguments = arguments


class FileSystemMemory:
    """
    Memory class for tracking file system actions and their undo operations.

    Maintains a stack of (action, undo_action) pairs where actions are added
    to the top and can be undone in reverse order. Some actions may not have
    undo operations (e.g., overwrite operations).

    Attributes:
        _stack: List of tuples containing (action, undo_action) pairs.
            undo_action can be None if the action cannot be undone.
    """

    def __init__(self) -> None:
        """
        Initialize an empty FileSystemMemory.
        """
        self._stack: List[Tuple[Action, Optional[Action]]] = []

    def add_action(
        self,
        action: Action,
        undo_action: Optional[Action] = None,
    ) -> None:
        """
        Add an action and its undo operation to the top of the stack.

        Args:
            action: The action that was performed.
            undo_action: Optional undo action. If None, the action cannot be undone.
        """
        self._stack.append((action, undo_action))

    def get_last_action(self) -> Optional[Tuple[Action, Optional[Action]]]:
        """
        Get the last action and its undo operation without removing it.

        Returns:
            Tuple of (action, undo_action) if stack is not empty, None otherwise.
        """
        if not self._stack:
            return None
        return self._stack[-1]

    def pop_action(self) -> Optional[Tuple[Action, Optional[Action]]]:
        """
        Remove and return the last action and its undo operation from the stack.

        Returns:
            Tuple of (action, undo_action) if stack is not empty, None otherwise.
        """
        if not self._stack:
            return None
        return self._stack.pop()

    def clear(self) -> None:
        """
        Clear all actions from the stack.
        """
        self._stack.clear()

    def is_empty(self) -> bool:
        """
        Check if the stack is empty.

        Returns:
            True if stack is empty, False otherwise.
        """
        return len(self._stack) == 0

    def size(self) -> int:
        """
        Get the number of actions in the stack.

        Returns:
            Number of actions in the stack.
        """
        return len(self._stack)

    def undo(self) -> Dict[str, Any]:
        """
        Undo the last action by executing its undo operation.

        Only removes the action from the stack if the undo operation succeeds.
        If undo fails, the action remains on the stack for potential retry.

        Returns:
            Dictionary with:
                - success: Boolean indicating if the undo was successful.
                - error: Error message if undo failed (None if successful).
                - action_name: Name of the action that was undone (only if success is True).
        """
        if not self._stack:
            return {
                "success": False,
                "error": "No actions to undo.",
            }

        action, undo_action = self._stack[-1]  # Peek at the top without removing

        if undo_action is None:
            return {
                "success": False,
                "error": f"Action '{action.function_name}' cannot be undone.",
            }

        try:
            undo_result = undo_action.function(**undo_action.arguments)
            if not undo_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Undo operation failed: {undo_result.get('error', 'Unknown error')}",
                }

            # Only pop from stack if undo succeeded
            self._stack.pop()

            return {
                "success": True,
                "error": None,
                "action_name": action.function_name,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing undo operation: {str(e)}",
            }


def undo(file_system_memory: FileSystemMemory) -> Dict[str, Any]:
    """
    Undo the last action in the given FileSystemMemory.

    Args:
        file_system_memory: FileSystemMemory instance to undo from.

    Returns:
        Dictionary with:
            - success: Boolean indicating if the undo was successful.
            - error: Error message if undo failed (None if successful).
            - action_name: Name of the action that was undone (only if success is True).
    """
    return file_system_memory.undo()

