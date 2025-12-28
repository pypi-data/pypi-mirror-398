"""
Advanced Agent class for chatbot-style interactions with LLMs.
"""

import json
from typing import List, Dict, Optional, Callable, Any, Union

from ..llm import LLM
from ..llm.tools import prepare_tools_for_provider
from ..utils.usage_tracker import UsageTracker
from ..utils.json_parser import parse_json_or_python_literal
from ..utils.fuzzy_match import fuzzy_match
from .base_agent import BaseAgent
from .save_objects import (
    ObjectToSave,
    ObjectsToSave,
    save_as,
    save_objects_if_they_need_to_be_saved,
)
from .verbose import (
    print_tool_result,
)


class SpecialObjectKeyError(KeyError):
    """
    Exception raised when a special object is not found.
    
    This is a subclass of KeyError to maintain compatibility while allowing
    specific error handling for special object lookups.
    """
    pass

class Agent(BaseAgent):
    """
    Advanced Agent class that works like a chatbot.

    Extends BaseAgent with:
    - Multiple conversation management
    - Special object system (system, global, conversation-scoped, tool call objects)
    - Object reference resolution in tool arguments
    - Built-in save/load tools
    - Advanced type conversion with JSON/Python literal parsing
    """

    def __init__(
        self,
        llm: Union[LLM, Dict[str, LLM]],
        default_llm: Optional[Union[LLM, str]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Callable]] = None,
        system_object_prefix: str = "sys:",
        global_object_prefix: str = "obj:",
        conversation_object_prefix: str = "conv_obj:",
        tool_call_object_prefix: str = "tool_obj:",
        verbose: bool = True,
    ) -> None:
        """
        Initialize an Agent.

        Args:
            llm: Either a single LLM instance, or a dictionary of LLMs (keyed by name).
            default_llm: The default LLM to use. Can be:
                - An LLM instance (if llm is a dict)
                - A string key to one of the LLMs in the dictionary
                - If not provided and llm is a single LLM, that LLM is used
                - If not provided and llm is a dict, the first LLM in the dict is used
            system_prompt: Optional system prompt for instructions.
            tools: Optional list of callable functions to use as tools.
            system_object_prefix: Prefix for system object references in tool arguments (default: "sys:").
                References must be wrapped in square brackets: [sys:key]. Examples: [sys:self], [sys:llm].
            global_object_prefix: Prefix for global saved object references in tool arguments (default: "obj:").
                References must be wrapped in square brackets: [obj:object_name] for global objects.
            conversation_object_prefix: Prefix for conversation-scoped saved object references (default: "conv_obj:").
                References must be wrapped in square brackets: [conv_obj:conversation_id:object_name].
            tool_call_object_prefix: Prefix for tool call result references in tool arguments (default: "tool_obj:").
                References must be wrapped in square brackets: [tool_obj:conversation_id:tool_call_id].
            verbose: If True, print detailed information about agent's thinking process.
        """
        # Add memory guidance to system prompt
        memory_guidance = (
            "\n\nMemory Management:\n"
            "When a user asks a question that seems to require information from previous conversations "
            "or saved data, you should retrieve saved objects using the 'remember' or 'load' function. "
            "IMPORTANT: If you don't know the exact name of the saved object, use 'list_objects' first "
            "to search for relevant saved objects. Use 'list_objects' with a name parameter for fuzzy matching "
            "when searching by partial name (e.g., if user asks about 'favorite color', search with 'color' or 'favorite'). "
            "After finding the object name with 'list_objects', use 'remember' or 'load' with that exact name. "
            "Remember that objects can be saved to conversation-scoped memory (default) or global memory. "
            "Use 'list_objects' with global_memory=True to search global memory, or False (default) for conversation-scoped memory."
        )
        
        enhanced_system_prompt = (
            (system_prompt + memory_guidance) if system_prompt else memory_guidance
        )
        
        # Initialize base agent (handles LLM, tools, basic conversation)
        super().__init__(
            llm=llm,
            default_llm=default_llm,
            system_prompt=enhanced_system_prompt,
            tools=None,  # We'll add tools after built-ins
            verbose=verbose,
        )
        
        # Store prefixes in lowercase for consistent matching
        self.system_object_prefix = system_object_prefix.lower()
        self.global_object_prefix = global_object_prefix.lower()
        self.conversation_object_prefix = conversation_object_prefix.lower()
        self.tool_call_object_prefix = tool_call_object_prefix.lower()
        
        # Store multiple conversations by ID (replaces single conversation_history from BaseAgent)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        # Current conversation ID (defaults to "default")
        self.current_conversation_id = "default"
        
        # Replace usage tracker with one that includes conversation_id
        self.usage_tracker = UsageTracker(include_conversation_id=True)
        
        # Track tool calls per conversation (preserved even when conversation is deleted)
        self.conversation_tool_calls: Dict[str, List[Dict[str, Any]]] = {}
        
        # Advanced object storage (extends _system_objects from BaseAgent)
        self._global_objects: Dict[str, Any] = {}
        # Store conversation-scoped objects (deleted when conversation is deleted)
        self._tool_call_objects: Dict[str, Dict[str, Any]] = {}
        # Store conversation-scoped saved objects (explicitly saved, deleted when conversation is deleted)
        self._conversation_objects: Dict[str, Dict[str, Any]] = {}
        
        # Add built-in save/load tools
        built_in_tools = self._create_built_in_tools()
        all_tools = (built_in_tools + tools) if tools else built_in_tools
        
        if all_tools:
            # Build tool function mapping (extends base tool_functions)
            for tool in all_tools:
                tool_name = tool.__name__
                self.tool_functions[tool_name] = tool
            
            # Prepare tools for current provider (conversion happens outside Agent)
            provider = self.llm.provider
            prepared = prepare_tools_for_provider(all_tools, provider)
            self.tools = prepared["tools"]
            self.tool_schemas = prepared["schemas"]
        
        # Initialize default conversation
        self.start_conversation()
    

    @staticmethod
    def save_as(*, name: Optional[str] = None, value: Optional[Any] = None, **kwargs: Any) -> Union[ObjectToSave, ObjectsToSave]:
        """
        Save an object or multiple objects as saved objects that can be referenced later.

        Can be called in two ways:
        1. Single object: save_as(name="key", value=obj)
        2. Multiple objects: save_as(key1=obj1, key2=obj2, ...)

        Args:
            name: Name to save the object under (for single save).
            value: The object to save (for single save).
            **kwargs: Named objects to save (for multiple save).

        Returns:
            ObjectToSave wrapper for single save, or ObjectsToSave for multiple save.
        """
        return save_as(name=name, value=value, **kwargs)

    def switch_default_llm(self, default_llm: Union[LLM, str]) -> None:
        """
        Switch the default LLM to use for queries.
        
        Args:
            default_llm: Either an LLM instance or a string key to one of the LLMs in self.llms.
        """
        super().switch_default_llm(default_llm=default_llm)
    
    def _create_built_in_tools(self) -> List[Callable]:
        """
        Create built-in save/load tools with aliases.
        
        Returns:
            List of tool functions (save, load, memorize, remember).
        """
        def save(name: str, value: Any, global_memory: bool = False):
            """
            Save an object to conversation-scoped or global storage.
            
            Args:
                name: Name to save the object under.
                value: The object to save.
                global_memory: If True, save to global storage.
                             If False, save to conversation-scoped storage (default).
            
            Returns:
                ObjectToSave wrapper that will be processed by the agent.
            """
            return save_as(name=name, value=value, conversation_scoped=not global_memory)
        
        def load(name: str, global_memory: bool = False) -> any:
            """
            Load an object from conversation-scoped or global storage.
            
            Args:
                name: Name of the object to load.
                global_memory: If True, load from global storage.
                             If False, load from conversation-scoped storage (default).
            
            Returns:
                The loaded object.
            """
            if global_memory:
                if name in self._global_objects:
                    return self._global_objects[name]
                raise KeyError(f"Global object '{name}' not found")
            else:
                conversation_id = self.current_conversation_id
                if conversation_id in self._conversation_objects and name in self._conversation_objects[conversation_id]:
                    return self._conversation_objects[conversation_id][name]
                raise KeyError(f"Conversation-scoped object '{name}' not found in conversation '{conversation_id}'")
        
        def list_objects(name: Optional[str] = None, global_memory: bool = False, max_results: Optional[int] = 20) -> List[str]:
            """
            List saved object names, optionally filtered by fuzzy name matching.
            
            Args:
                name: Optional name to fuzzy match against. If provided, returns only
                     objects whose names match the query. If None, returns all objects.
                global_memory: If True, list from global storage.
                             If False, list from conversation-scoped storage (default).
                max_results: Maximum number of results to return when name is provided.
                           Default: 20. Ignored if name is None.
            
            Returns:
                List of object names, sorted by relevance if name is provided.
            """
            if global_memory:
                all_names = list(self._global_objects.keys())
            else:
                conversation_id = self.current_conversation_id
                if conversation_id in self._conversation_objects:
                    all_names = list(self._conversation_objects[conversation_id].keys())
                else:
                    all_names = []
            
            if not name:
                # Return all names, sorted alphabetically
                return sorted(all_names)
            
            # Use fuzzy matching to find relevant names
            matched_names = fuzzy_match(
                query=name,
                candidates=all_names,
                threshold=0.5,  # Lower threshold for more lenient matching
                max_results=max_results,
            )
            return matched_names
        
        # Aliases
        memorize = save
        memorize.__name__ = 'memorize'
        remember = load
        remember.__name__ = 'remember'
        
        return [save, load, memorize, remember, list_objects]
    
    def _add_system_object(self, key: str, value: Any) -> None:
        """
        Add a special object to the special objects dictionary.
        
        Special objects can be referenced in tool arguments using the format:
        {prefix}{key}{suffix}. For example, with default prefix "use:", 
        a tool can request "use:self" to receive the agent instance.
        If there is space between the prefix and the key or the suffix, it will be ignored.
        
        Args:   
            key: Name of the special object.
            value: The object to store.
        """
        self._system_objects[key.strip()] = value

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Add a special object to the special objects dictionary.
        
        Allows dict-like syntax: agent['my_object'] = obj
        
        Args:
            key: Name of the special object.
            value: The object to store.
        """
        self._add_system_object(key=key, value=value)

    def _convert_arguments_to_types(
        self,
        arguments: Dict[str, Any],
        tool_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert function arguments to appropriate Python types based on schema.
        
        Extends BaseAgent's implementation with JSON/Python literal parsing.

        Args:
            arguments: Parsed JSON arguments dictionary.
            tool_schema: Tool schema in provider-specific format.

        Returns:
            Arguments dictionary with properly typed values.
        """
        # Call base implementation for basic type conversion
        converted = super()._convert_arguments_to_types(arguments=arguments, tool_schema=tool_schema)
        
        properties = tool_schema.get("function", {}).get("parameters", {}).get("properties", {})
        
        for param_name, param_schema in properties.items():
            if param_name in converted:
                param_type = param_schema.get("type", "string")
                value = converted[param_name]
                
                # Advanced: If schema says "string" but value looks like JSON or Python literal, try to parse it
                # This handles cases where the type annotation is unknown (like "any")
                # and the LLM passes complex objects as JSON strings or Python literals
                if param_type == "string" and isinstance(value, str):
                    parsed = parse_json_or_python_literal(value)
                    if parsed != value:  # Only replace if parsing succeeded
                        converted[param_name] = parsed
        
        return converted

    def _extract_content_after_prefix(
        self,
        content: str,
        prefix: str,
    ) -> str:
        """
        Extract content after a prefix.
        
        Args:
            content: The content to parse (should be lowercase).
            prefix: The prefix to look for.
            
        Returns:
            The extracted content after prefix.
        """
        return content[len(prefix):].strip()

    def _resolve_system_object_reference(self, content: str, original_value: str) -> Any:
        """
        Resolve a system object reference: [sys:key].
        
        Args:
            content: Content between brackets (e.g., "sys:self").
            original_value: Original full value including brackets (for error messages).
            
        Returns:
            Resolved system object.
            
        Raises:
            SpecialObjectKeyError: If the system object is not found.
            ValueError: If the content doesn't match the system object pattern.
        """
        content_lower = content.lower()
        
        if not content_lower.startswith(self.system_object_prefix):
            raise ValueError("Not a system object reference")
        
        # Extract the system object key
        system_object_key = self._extract_content_after_prefix(
            content=content_lower,
            prefix=self.system_object_prefix,
        )
        
        # Lookup is case-insensitive - normalize to lowercase for lookup
        if system_object_key in self._system_objects:
            return self._system_objects[system_object_key]
        else:
            raise SpecialObjectKeyError(f"System object '{system_object_key}' not found. Available: {list(self._system_objects.keys())}")

    def _resolve_tool_call_result_reference(self, content: str, original_value: str) -> Any:
        """
        Resolve a tool call result reference: [tool_obj:conversation_id:tool_call_id].

        Args:
            content: Content between brackets (e.g., "tool_obj:default:call_abc123").
            original_value: Original full value including brackets (for error messages).

        Returns:
            Resolved tool call result object.

        Raises:
            SpecialObjectKeyError: If the tool call result is not found.
            ValueError: If the content doesn't match the tool call result pattern.
        """
        content_lower = content.lower()

        if not content_lower.startswith(self.tool_call_object_prefix):
            raise ValueError("Not a tool call result reference")

        # Extract the part after "tool_obj:" - use original case for tool_call_id lookup
        tool_ref_lower = self._extract_content_after_prefix(
            content=content_lower,
            prefix=self.tool_call_object_prefix,
        )
        
        # Extract from original content to preserve case
        tool_ref_original = self._extract_content_after_prefix(
            content=content,
            prefix=self.tool_call_object_prefix,
        )

        # Split by colon to get conversation_id and tool_call_id
        parts_lower = tool_ref_lower.split(':', 1)
        parts_original = tool_ref_original.split(':', 1)
        if len(parts_lower) != 2:
            raise SpecialObjectKeyError(
                f"Invalid tool reference format: '{original_value}'. Expected [tool_obj:conversation_id:tool_call_id]"
            )

        conversation_id = parts_lower[0].strip().lower()  # Use lowercase for lookup
        tool_call_id = parts_original[1].strip()  # Preserve original case for key lookup

        # Check conversation-scoped objects
        if conversation_id in self._tool_call_objects:
            conversation_objects = self._tool_call_objects[conversation_id]
            if tool_call_id in conversation_objects:
                return conversation_objects[tool_call_id]
            else:
                raise SpecialObjectKeyError(
                    f"Tool call result '{tool_call_id}' not found in conversation '{conversation_id}'. "
                    f"Available: {list(conversation_objects.keys())}"
                )
        else:
            raise SpecialObjectKeyError(
                f"Conversation '{conversation_id}' has no stored tool results. "
                f"Available conversations: {list(self._tool_call_objects.keys())}"
            )

    def _resolve_conversation_scoped_saved_object_reference(self, content: str, original_value: str) -> Any:
        """
        Resolve a conversation-scoped saved object reference: [conv_obj:conversation_id:object_name].
        
        Args:
            content: Content between brackets (e.g., "conv_obj:default:my_data").
            original_value: Original full value including brackets (for error messages).
            
        Returns:
            Resolved conversation-scoped saved object.
            
        Raises:
            SpecialObjectKeyError: If the conversation-scoped saved object is not found.
            ValueError: If the content doesn't match the conversation-scoped saved object pattern.
        """
        content_lower = content.lower()
        
        if not content_lower.startswith(self.conversation_object_prefix):
            raise ValueError("Not a conversation-scoped saved object reference")
        
        # Extract the part after "conv_obj:"
        obj_ref = self._extract_content_after_prefix(
            content=content_lower,
            prefix=self.conversation_object_prefix,
        )
        
        # Split by colon to check if conversation_id is present
        parts = obj_ref.split(':', 1)
        
        if len(parts) != 2:
            raise ValueError("Not a conversation-scoped saved object reference (missing conversation_id)")
        
        # Format: [conv_obj:conversation_id:object_name]
        conversation_id, object_name = parts[0].strip(), parts[1].strip()
        
        # Check conversation-scoped saved objects
        if conversation_id in self._conversation_objects:
            conversation_objects = self._conversation_objects[conversation_id]
            if object_name in conversation_objects:
                return conversation_objects[object_name]
            else:
                raise SpecialObjectKeyError(
                    f"Conversation-scoped saved object '{object_name}' not found in conversation '{conversation_id}'. "
                    f"Available: {list(conversation_objects.keys())}"
                )
        else:
            raise SpecialObjectKeyError(
                f"Conversation '{conversation_id}' has no saved objects. "
                f"Available conversations: {list(self._conversation_objects.keys())}"
            )

    def _resolve_global_saved_object_reference(self, content: str, original_value: str) -> Any:
        """
        Resolve a global saved object reference: [obj:object_name].
        
        Args:
            content: Content between brackets (e.g., "obj:my_data").
            original_value: Original full value including brackets (for error messages).
            
        Returns:
            Resolved global saved object.
            
        Raises:
            SpecialObjectKeyError: If the global saved object is not found.
            ValueError: If the content doesn't match the global saved object pattern.
        """
        content_lower = content.lower()
        
        if not content_lower.startswith(self.global_object_prefix):
            raise ValueError("Not a saved object reference")
        
        # Extract the part after "obj:"
        obj_ref = self._extract_content_after_prefix(
            content=content_lower,
            prefix=self.global_object_prefix,
        )
        
        # Split by colon to check if conversation_id is present
        parts = obj_ref.split(':', 1)
        
        if len(parts) == 2:
            raise ValueError("Not a global saved object reference (has conversation_id)")
        
        # Format: [obj:object_name] - global saved object
        object_name = obj_ref.strip()
        
        # Lookup is case-insensitive - normalize to lowercase for lookup
        if object_name in self._global_objects:
            return self._global_objects[object_name]
        else:
            raise SpecialObjectKeyError(f"Global saved object '{object_name}' not found. Available: {list(self._global_objects.keys())}")

    def _add_system_objects_to_tool_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace special object references in tool arguments with actual objects.
        
        Arguments with values matching the bracket pattern `[prefix:...]` (as strings) are
        replaced with the corresponding special object. References must be wrapped in square
        brackets to avoid conflicts with normal strings.
        
        Supported reference formats:
        - `[sys:key]` - System objects (system-level, predefined), e.g., [sys:self], [sys:llm]
        - `[tool_obj:conversation_id:tool_call_id]` - Tool call results, e.g., [tool_obj:default:call_abc123]
        - `[conv_obj:conversation_id:object_name]` - Conversation-scoped saved objects
        - `[obj:object_name]` - Global saved objects (persist across conversations)
        
        Args:
            arguments: Dictionary of tool arguments.
            
        Returns:
            Dictionary with special object references replaced.
            
        Raises:
            SpecialObjectKeyError: If a referenced special object is not found.
        """
        result = {}
        for key, value in arguments.items():
            # Check if value is a string matching the bracket-wrapped reference pattern
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                # Extract content between brackets
                content = value[1:-1].strip()
                
                # Try each resolver in order
                resolved = None
                try:
                    resolved = self._resolve_system_object_reference(content=content, original_value=value)
                except ValueError:
                    # Not a system object, try next
                    try:
                        resolved = self._resolve_tool_call_result_reference(content=content, original_value=value)
                    except ValueError:
                        # Not a tool call result, try next
                        try:
                            resolved = self._resolve_conversation_scoped_saved_object_reference(content=content, original_value=value)
                        except ValueError:
                            # Not a conversation-scoped saved object, try next
                            try:
                                resolved = self._resolve_global_saved_object_reference(content=content, original_value=value)
                            except ValueError:
                                # Not a global saved object either - pass through as-is
                                result[key] = value
                
                if resolved is not None:
                    result[key] = resolved
                elif key not in result:
                    # String has brackets but doesn't match any known pattern - pass through as-is
                    result[key] = value
            else:
                # Not a bracket-wrapped reference - pass through as-is
                result[key] = value
        return result

    def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        return_raw: bool = False,
        conversation_id: Optional[str] = None,
    ) -> Any:
        """
        Execute a tool function with given arguments.
        
        Extends BaseAgent's implementation with special object resolution and object saving.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.
            return_raw: If True, return raw result; if False, return as string.
            conversation_id: ID of the conversation (for conversation-scoped saved objects).

        Returns:
            Tool execution result as a string (default) or raw result.
        """
        if tool_name not in self.tool_functions:
            error_msg = f"Error: Tool '{tool_name}' not found"
            return error_msg
        
        try:
            func = self.tool_functions[tool_name]
            # Resolve special object references
            arguments = self._add_system_objects_to_tool_arguments(arguments)
            result = func(**arguments)
            # Save objects if they need to be saved
            result = self._save_objects_if_they_need_to_be_saved(
                result_of_function_call=result,
                conversation_id=conversation_id,
            )
            return result if return_raw else str(result)
        except SpecialObjectKeyError as e:
            # Re-raise SpecialObjectKeyError - it's a configuration error
            raise
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def _save_objects_if_they_need_to_be_saved(
        self,
        result_of_function_call: Any,
        conversation_id: Optional[str] = None,
    ) -> Any:
        """
        Save objects if they need to be saved (instance method wrapper).

        Args:
            result_of_function_call: The result of the function call.
            conversation_id: ID of the conversation (for conversation-scoped saved objects).

        Returns:
            The processed result of the function call (with ObjectToSave instances replaced).
        """
        conversation_saved_objects = None
        if conversation_id is not None:
            if conversation_id not in self._conversation_objects:
                self._conversation_objects[conversation_id] = {}
            conversation_saved_objects = self._conversation_objects[conversation_id]
        
        return save_objects_if_they_need_to_be_saved(
            result_of_function_call=result_of_function_call,
            saved_objects=self._global_objects,
            conversation_saved_objects=conversation_saved_objects,
            conversation_id=conversation_id,
        )

    def _process_tool_call(
        self,
        tool_call: Dict[str, Any],
        conversation_id: Optional[str] = None,
    ) -> Any:
        """
        Process a single tool call: extract, parse, convert types, execute, and track.
        
        Extends BaseAgent's implementation with object saving and tracking.

        Args:
            tool_call: The tool call dictionary from the LLM response.
            conversation_id: ID of the conversation.

        Returns:
            Raw result from the tool execution.
        """
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        function_name = tool_call["function"]["name"]
        arguments_json = tool_call["function"]["arguments"]
        
        # Parse JSON string to get arguments
        # Use our centralized parser to handle both JSON and Python literal formats
        function_args = parse_json_or_python_literal(arguments_json)
        if isinstance(function_args, str):
            # If it's still a string, try json.loads as fallback (for proper JSON)
            try:
                function_args = json.loads(function_args)
            except (json.JSONDecodeError, ValueError):
                # If that also fails, it's not valid JSON or Python literal
                raise ValueError(f"Invalid JSON in tool arguments: {arguments_json}")
        
        # Convert types based on schema if available
        if function_name in self.tool_schemas:
            function_args = self._convert_arguments_to_types(
                function_args,
                self.tool_schemas[function_name]
            )
        
        # Execute the function - get raw result for tracking, string for conversation
        raw_result = self._execute_tool(function_name, function_args, return_raw=True, conversation_id=conversation_id)
        string_result = str(raw_result)
        
        if self.verbose:
            print_tool_result(tool_name=function_name, result=raw_result)
        
        # Store tool result in conversation objects for later reference
        if conversation_id not in self._tool_call_objects:
            self._tool_call_objects[conversation_id] = {}
        self._tool_call_objects[conversation_id][tool_call["id"]] = raw_result
        
        # Track tool call with raw result
        self._track_tool_call(
            conversation_id=conversation_id,
            tool_name=function_name,
            arguments=function_args,
            result=raw_result,
            tool_call_id=tool_call["id"],
        )
        
        # Add tool response with matching tool_call_id (as string for LLM)
        conversation_history = self._get_conversation(conversation_id)
        self._add_tool_response_to_history(
            conversation_history=conversation_history,
            tool_call_id=tool_call["id"],
            result=string_result,
        )
        
        return raw_result

    def _track_tool_call(
        self,
        conversation_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        tool_call_id: str,
    ) -> None:
        """
        Track a tool call in conversation_tool_calls.

        Args:
            conversation_id: ID of the conversation.
            tool_name: Name of the tool that was called.
            arguments: Arguments passed to the tool.
            result: Raw result from the tool execution.
            tool_call_id: ID of the tool call.
        """
        if conversation_id not in self.conversation_tool_calls:
            self.conversation_tool_calls[conversation_id] = []
        
        self.conversation_tool_calls[conversation_id].append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "tool_call_id": tool_call_id,
        })

    def _add_tool_response_to_history(
        self,
        conversation_history: List[Dict[str, Any]],
        tool_call_id: str,
        result: str,
    ) -> None:
        """
        Add tool response to conversation history.

        Args:
            conversation_history: The conversation history list to append to.
            tool_call_id: ID of the tool call (must match original tool_call.id).
            result: String result from the tool execution.
        """
        conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        })

    def start_conversation(self, conversation_id: Optional[str] = None) -> None:
        """
        Start a new conversation with the given ID.

        Initializes the conversation with the system prompt if available.
        Sets this conversation as the current one.

        Args:
            conversation_id: Optional conversation ID. Uses current_conversation_id if not provided.
        """
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        # Initialize conversation with system prompt if available
        if self.system_prompt:
            self.conversations[conversation_id] = [
                {"role": "system", "content": self.system_prompt}
            ]
        else:
            self.conversations[conversation_id] = []
        
        # Set as current conversation
        self.current_conversation_id = conversation_id

    def _get_conversation(self, conversation_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get conversation history for a given ID.

        Args:
            conversation_id: Optional conversation ID. Uses current_conversation_id if not provided.

        Returns:
            List of conversation messages.

        Raises:
            ValueError: If conversation doesn't exist.
        """
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        if conversation_id not in self.conversations:
            raise ValueError(
                f"Conversation '{conversation_id}' does not exist. "
                f"Call start_conversation('{conversation_id}') first."
            )
        
        return self.conversations[conversation_id]

    def reset_conversation(self, conversation_id: Optional[str] = None) -> None:
        """
        Reset a conversation, clearing all messages except system prompt.

        Args:
            conversation_id: Optional conversation ID. Uses current_conversation_id if not provided.
        """
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        if conversation_id not in self.conversations:
            raise ValueError(
                f"Conversation '{conversation_id}' does not exist. "
                f"Call start_conversation('{conversation_id}') first."
            )
        
        # Reset to just system prompt if available
        if self.system_prompt:
            self.conversations[conversation_id] = [
                {"role": "system", "content": self.system_prompt}
            ]
        else:
            self.conversations[conversation_id] = []
        
        # Clear conversation-scoped objects
        if conversation_id in self._tool_call_objects:
            self._tool_call_objects[conversation_id].clear()
        if conversation_id in self._conversation_objects:
            self._conversation_objects[conversation_id].clear()

    def forget_conversation(self, conversation_id: Optional[str] = None) -> None:
        """
        Forget a conversation completely, or all conversations if no ID provided.

        Note: Usage tracking and tool call tracking for deleted conversations are preserved.

        Args:
            conversation_id: Optional conversation ID. If None, forgets all conversations.
        """
        if conversation_id is None:
            # Forget all conversations
            self.conversations.clear()
            self._tool_call_objects.clear()
            self._conversation_objects.clear()
        else:
            # Forget specific conversation
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                # If we deleted the current conversation, reset to default
                if conversation_id == self.current_conversation_id:
                    self.current_conversation_id = "default"
            # Delete conversation-scoped objects
            if conversation_id in self._tool_call_objects:
                del self._tool_call_objects[conversation_id]
            if conversation_id in self._conversation_objects:
                del self._conversation_objects[conversation_id]
            # Note: usage_records and conversation_tool_calls are NOT deleted - tracking is preserved

    def run(
        self,
        input_text: str,
        conversation_id: Optional[str] = None,
        return_raw_tool_result: bool = False,
        llm_instance: Union[str, LLM] = "default",
        max_iterations: int = 10,
    ) -> Any:
        """
        Process input and return response, maintaining conversation history.

        Extends BaseAgent's implementation with multi-conversation support.

        Args:
            input_text: The user's input message.
            conversation_id: Optional conversation ID. Uses default if not provided.
            return_raw_tool_result: If True, return raw tool result(s) instead of the LLM's
                interpretation. For single tool call, returns the result directly. For multiple
                tool calls, returns a list of results. Default: False.
            llm_instance: LLM instance to use for this run. Can be:
                - A string key to one of the LLMs in self.llms (default: "default")
                - An LLM instance from self.llms

        Returns:
            The agent's response text, or raw tool result(s) if return_raw_tool_result is True.
        """
        # Determine which LLM to use for this run
        run_llm, llm_key = self._get_llm_for_run(llm_instance=llm_instance)
        
        # Resolve conversation_id if not provided
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        # Set as current conversation for tool execution context
        # (Built-in tools like load/remember use current_conversation_id)
        self.current_conversation_id = conversation_id
        
        # Get conversation history for this ID
        conversation_history = self._get_conversation(conversation_id)
        
        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": input_text})

        # Query LLM with full conversation history and tools
        # Tools are cached in __init__ to avoid repeated conversion
        iteration = 0
        accumulated_tool_results = []  # Accumulate results across iterations when return_raw_tool_result=True
        
        while iteration < max_iterations:
            iteration += 1
            
            if self.verbose:
                from .verbose import print_iteration, print_conversation_context, print_llm_response, print_tool_calls
                print_iteration(iteration=iteration, max_iterations=max_iterations)
                print_conversation_context(conversation_history=conversation_history)
            
            # Query LLM - use cached tools if available
            if self.tools is not None:
                response = run_llm.query(
                    messages=conversation_history,
                    tools=self.tools,
                )
            else:
                response = run_llm.query(messages=conversation_history)
            
            if self.verbose:
                from .verbose import print_llm_response
                print_llm_response(response=response)
            
            # Track usage for this conversation
            if run_llm.last_usage:
                self.usage_tracker.add_record(
                    usage=run_llm.last_usage,
                    cost=run_llm.last_cost,
                    llm=llm_key,
                    conversation_id=conversation_id,
                )

            # Check if response contains tool calls
            if isinstance(response, dict) and "tool_calls" in response:
                # Handle tool calling - can be multiple tool calls
                tool_calls = response["tool_calls"]
                
                if self.verbose:
                    from .verbose import print_tool_calls
                    print_tool_calls(tool_calls=tool_calls)
                
                # Add assistant message with tool_calls to conversation
                conversation_history.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls,
                })
                
                # Execute each tool call and add results
                tool_results = []
                for tool_call in tool_calls:
                    raw_result = self._process_tool_call(
                        tool_call=tool_call,
                        conversation_id=conversation_id,
                    )
                    tool_results.append(raw_result)
                
                # If return_raw_tool_result is True, accumulate results and continue
                if return_raw_tool_result:
                    accumulated_tool_results.extend(tool_results)
                    # Continue loop - may have more tool calls or final response
                    continue
                
                # Continue the loop to get final response
                continue
            
            # Regular text response - ensure it's a string
            if isinstance(response, str) and len(response) > 0:
                conversation_history.append({"role": "assistant", "content": response})
                # If return_raw_tool_result is True and we have accumulated results, return them
                if return_raw_tool_result and accumulated_tool_results:
                    if self.verbose:
                        print(f"[Agent] Returning {len(accumulated_tool_results)} accumulated tool result(s)")
                    if len(accumulated_tool_results) == 1:
                        return accumulated_tool_results[0]
                    else:
                        return accumulated_tool_results
                return response
            elif isinstance(response, str):
                # Empty string response - still add it and return
                conversation_history.append({"role": "assistant", "content": response})
                # If return_raw_tool_result is True and we have accumulated results, return them
                if return_raw_tool_result and accumulated_tool_results:
                    if len(accumulated_tool_results) == 1:
                        return accumulated_tool_results[0]
                    else:
                        return accumulated_tool_results
                return response
            else:
                # Unexpected response type
                response_str = str(response) if response else "Error: Empty response"
                conversation_history.append({"role": "assistant", "content": response_str})
                # If return_raw_tool_result is True and we have accumulated results, return them
                if return_raw_tool_result and accumulated_tool_results:
                    if len(accumulated_tool_results) == 1:
                        return accumulated_tool_results[0]
                    else:
                        return accumulated_tool_results
                return response_str
        
        # If we've exceeded max iterations, return accumulated tool results or error
        if return_raw_tool_result and accumulated_tool_results:
            if len(accumulated_tool_results) == 1:
                return accumulated_tool_results[0]
            else:
                return accumulated_tool_results
        return "Error: Maximum iterations exceeded"
    
    def get_total_usage(
        self,
        llm: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Optional[int]]:
        """
        Get total usage (tokens) optionally filtered by llm and/or conversation_id.
        
        Args:
            llm: Optional LLM identifier (key) to filter by. If None, includes all LLMs.
            conversation_id: Optional conversation ID to filter by. If None, includes all conversations.
        
        Returns:
            Dictionary with "input_tokens", "output_tokens", and "total_tokens".
        """
        return self.usage_tracker.get_total_usage(llm=llm, conversation_id=conversation_id)
    
    def get_total_cost(
        self,
        llm: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Get total cost optionally filtered by llm and/or conversation_id.
        
        Args:
            llm: Optional LLM identifier (key) to filter by. If None, includes all LLMs.
            conversation_id: Optional conversation ID to filter by. If None, includes all conversations.
        
        Returns:
            Dictionary with "input_cost", "output_cost", and "total_cost".
        """
        return self.usage_tracker.get_total_cost(llm=llm, conversation_id=conversation_id)

