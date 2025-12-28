"""
Classes and functions for saving objects in the agent.
"""

from typing import List, Dict, Optional, Any, Union


class ObjectToSave:
    """
    Object to save to the agent's saved objects dictionary.
    """
    def __init__(self, name: str, value: Any, conversation_scoped: bool = False):
        self.name = name
        self.value = value
        self.conversation_scoped = conversation_scoped


class ObjectsToSave(List[ObjectToSave]):
    """
    List of objects to save to the agent's saved objects dictionary.
    """
    def __init__(self, objects: Optional[List[ObjectToSave]] = None):
        """
        Initialize ObjectsToSave.
        
        Args:
            objects: Optional list of ObjectToSave instances.
        """
        super().__init__()
        if objects:
            self.extend(objects)

    def get_values(self) -> List[Any]:
        """
        Get the values from all ObjectToSave instances.
        
        Returns:
            List of values from the saved objects.
        """
        return [object_to_save.value for object_to_save in self]


def save_as(
    *,
    name: Optional[str] = None,
    value: Optional[Any] = None,
    conversation_scoped: bool = False,
    **kwargs: Any,
) -> Union[ObjectToSave, ObjectsToSave]:
    """
    Save an object or multiple objects as saved objects that can be referenced later.

    Can be called in two ways:
    1. Single object: save_as(name="key", value=obj, conversation_scoped=False)
    2. Multiple objects: save_as(key1=obj1, key2=obj2, ..., conversation_scoped=False)

    Args:
        name: Name to save the object under (for single save).
        value: The object to save (for single save).
        conversation_scoped: If True, save as conversation-scoped object (deleted when conversation ends).
                          If False, save as global object (persists across conversations).
        **kwargs: Named objects to save (for multiple save). conversation_scoped applies to all.

    Returns:
        ObjectToSave wrapper for single save, or ObjectsToSave for multiple save.
    """
    if name is not None and value is not None:
        return ObjectToSave(name=name, value=value, conversation_scoped=conversation_scoped)
    elif name is None and value is None:
        result = ObjectsToSave()
        for key, val in kwargs.items():
            if isinstance(val, ObjectToSave):
                raise ValueError("Cannot save an object that is already a saved object")
            
            result.append(ObjectToSave(name=key, value=val, conversation_scoped=conversation_scoped))
        return result
    else:
        raise ValueError("Either both name and value must be provided, or names and values must be provided as kwargs")


def save_objects_if_they_need_to_be_saved(
    *,
    result_of_function_call: Any,
    saved_objects: Dict[str, Any],
    conversation_saved_objects: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None,
) -> Any:
    """
    Save objects if they need to be saved.

    Args:
        result_of_function_call: The result of the function call.
        saved_objects: The dictionary to save global objects to.
        conversation_saved_objects: The dictionary to save conversation-scoped objects to (optional).
        conversation_id: The conversation ID for conversation-scoped objects (optional).

    Returns:
        The processed result of the function call (with ObjectToSave instances replaced).
    """
    if isinstance(result_of_function_call, ObjectToSave):
        if result_of_function_call.conversation_scoped:
            if conversation_saved_objects is None:
                raise ValueError("conversation_saved_objects must be provided for conversation-scoped objects")
            if conversation_id is None:
                raise ValueError("conversation_id must be provided for conversation-scoped objects")
            conversation_saved_objects[result_of_function_call.name] = result_of_function_call.value
        else:
            saved_objects[result_of_function_call.name] = result_of_function_call.value
        return result_of_function_call.value

    elif isinstance(result_of_function_call, ObjectsToSave):
        values = []
        for object_to_save in result_of_function_call:
            if object_to_save.conversation_scoped:
                if conversation_saved_objects is None:
                    raise ValueError("conversation_saved_objects must be provided for conversation-scoped objects")
                if conversation_id is None:
                    raise ValueError("conversation_id must be provided for conversation-scoped objects")
                conversation_saved_objects[object_to_save.name] = object_to_save.value
            else:
                saved_objects[object_to_save.name] = object_to_save.value
            values.append(object_to_save.value)
        return values

    elif isinstance(result_of_function_call, list):
        result = []
        for item in result_of_function_call:
            item_result = save_objects_if_they_need_to_be_saved(
                result_of_function_call=item,
                saved_objects=saved_objects,
                conversation_saved_objects=conversation_saved_objects,
                conversation_id=conversation_id,
            )
            result.append(item_result)
        return result
    elif isinstance(result_of_function_call, dict):
        result = {}
        for key, value in result_of_function_call.items():
            item_result = save_objects_if_they_need_to_be_saved(
                result_of_function_call=value,
                saved_objects=saved_objects,
                conversation_saved_objects=conversation_saved_objects,
                conversation_id=conversation_id,
            )
            result[key] = item_result
        return result
    else:
        return result_of_function_call

