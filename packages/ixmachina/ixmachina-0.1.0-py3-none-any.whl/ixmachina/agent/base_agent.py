"""
Base Agent class for basic chatbot-style interactions with LLMs.
"""

from typing import List, Dict, Optional, Callable, Any, Union

from ..llm import LLM
from ..llm.tools import prepare_tools_for_provider
from ..utils.usage_tracker import UsageTracker
from .verbose import (
    print_iteration,
    print_conversation_context,
    print_llm_response,
    print_tool_calls,
    print_tool_result,
)


class BaseAgent:
    """
    Basic Agent class that works like a chatbot.

    Maintains a single conversation history and allows repeated interactions
    through a single run() method. Each call adds to the conversation
    and returns a response. Supports function calling with tools.
    """

    def __init__(
        self,
        llm: Union[LLM, Dict[str, LLM]],
        default_llm: Optional[Union[LLM, str]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Callable]] = None,
        verbose: bool = True,
    ) -> None:
        """
        Initialize a BaseAgent.

        Args:
            llm: Either a single LLM instance, or a dictionary of LLMs (keyed by name).
            default_llm: The default LLM to use. Can be:
                - An LLM instance (if llm is a dict)
                - A string key to one of the LLMs in the dictionary
                - If not provided and llm is a single LLM, that LLM is used
                - If not provided and llm is a dict, the first LLM in the dict is used
            system_prompt: Optional system prompt for instructions.
            tools: Optional list of callable functions to use as tools.
            verbose: If True, print detailed information about agent's thinking process.
        """
        # Handle LLM initialization
        self._initialize_llms(llm=llm, default_llm=default_llm)
        self.system_prompt = system_prompt
        self.verbose = verbose
        # Usage tracker
        self.usage_tracker = UsageTracker(include_conversation_id=False)
        
        # Store original functions for execution
        self.tool_functions: Dict[str, Callable] = {}
        # Store converted tools for LLM (provider-specific format)
        self.tools: Optional[List[Dict[str, Any]]] = None
        # Store schemas for type conversion
        self.tool_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Basic system objects (just self and llm)
        self._system_objects: Dict[str, Any] = {'self': self, 'llm': self.llm}
        
        # Update special objects when default LLM changes
        self._update_llm_special_objects()
        
        # Initialize conversation history (single conversation)
        if self.system_prompt:
            self.conversation_history: List[Dict[str, str]] = [
                {"role": "system", "content": self.system_prompt}
            ]
        else:
            self.conversation_history: List[Dict[str, str]] = []
        
        if tools:
            # Build tool function mapping
            for tool in tools:
                tool_name = tool.__name__
                self.tool_functions[tool_name] = tool
            
            # Prepare tools for current provider (conversion happens outside Agent)
            provider = self.llm.provider
            prepared = prepare_tools_for_provider(tools, provider)
            self.tools = prepared["tools"]
            self.tool_schemas = prepared["schemas"]
    
    def _initialize_llms(
        self,
        llm: Union[LLM, Dict[str, LLM]],
        default_llm: Optional[Union[LLM, str]],
    ) -> None:
        """
        Initialize LLMs dictionary and set default LLM.
        
        Args:
            llm: Either a single LLM instance, or a dictionary of LLMs (keyed by name).
            default_llm: The default LLM to use. Can be:
                - An LLM instance (if llm is a dict)
                - A string key to one of the LLMs in the dictionary
                - If None and llm is a single LLM, that LLM is used
                - If None and llm is a dict, the first LLM in the dict is used
        """
        # Determine the LLMs dictionary
        if isinstance(llm, dict):
            self.llms = llm
        else:
            # Single LLM provided - wrap it in a dict for consistency
            self.llms = {"default": llm}
        
        # Determine the default LLM
        if default_llm is None:
            # Use first LLM in dictionary if no default specified
            if len(self.llms) == 0:
                raise ValueError("At least one LLM must be provided")
            self.llm = next(iter(self.llms.values()))
        elif isinstance(default_llm, str):
            # default_llm is a key
            if default_llm not in self.llms:
                raise KeyError(
                    f"Default LLM key '{default_llm}' not found in llms dictionary. "
                    f"Available keys: {list(self.llms.keys())}"
                )
            self.llm = self.llms[default_llm]
        else:
            # default_llm is an LLM instance - find it in the dictionary
            found = False
            for llm_instance in self.llms.values():
                if llm_instance is default_llm:
                    self.llm = default_llm
                    found = True
                    break
            if not found:
                raise KeyError("Default LLM instance not found in llms dictionary")

    def _update_llm_special_objects(self) -> None:
        """Update special objects for LLMs: 'llm' (default) and 'llm:name' for each LLM."""
        # Update the default 'llm' special object
        self._system_objects['llm'] = self.llm
        
        # Remove old llm: prefixed special objects
        keys_to_remove = [key for key in self._system_objects.keys() if key.startswith('llm:')]
        for key in keys_to_remove:
            del self._system_objects[key]
        
        # Add all LLMs as special objects with 'llm:' prefix
        for llm_key, llm_instance in self.llms.items():
            self._system_objects[f'llm:{llm_key}'] = llm_instance
    
    def _get_llm_for_run(
        self,
        llm_instance: Union[str, LLM],
    ) -> tuple[LLM, str]:
        """
        Get the LLM instance to use for a run and its key.
        
        Args:
            llm_instance: Either a string key to one of the LLMs in self.llms,
                or an LLM instance from self.llms.
        
        Returns:
            Tuple of (LLM instance, key string).
        
        Raises:
            KeyError: If the key or instance is not found in self.llms.
        """
        if isinstance(llm_instance, str):
            if llm_instance == "default" and llm_instance not in self.llms:
                # "default" key doesn't exist, use current default LLM
                # Find the key for self.llm
                for key, llm_inst in self.llms.items():
                    if llm_inst is self.llm:
                        return self.llm, key
                # If not found, use model_name as key
                return self.llm, self.llm.model_name
            elif llm_instance not in self.llms:
                raise KeyError(
                    f"LLM key '{llm_instance}' not found in llms dictionary. "
                    f"Available keys: {list(self.llms.keys())}"
                )
            else:
                return self.llms[llm_instance], llm_instance
        else:
            # llm_instance is an LLM instance - verify it's in self.llms
            for key, llm_inst in self.llms.items():
                if llm_inst is llm_instance:
                    return llm_instance, key
            raise KeyError("LLM instance not found in llms dictionary")
    
    def switch_default_llm(self, default_llm: Union[LLM, str]) -> None:
        """
        Switch the default LLM to use for queries.
        
        Args:
            default_llm: Either an LLM instance or a string key to one of the LLMs in self.llms.
        """
        if isinstance(default_llm, str):
            if default_llm not in self.llms:
                raise KeyError(
                    f"LLM key '{default_llm}' not found in llms dictionary. "
                    f"Available keys: {list(self.llms.keys())}"
                )
            self.llm = self.llms[default_llm]
        else:
            # default_llm is an LLM instance - find it in the dictionary
            found = False
            for llm_instance in self.llms.values():
                if llm_instance is default_llm:
                    self.llm = default_llm
                    found = True
                    break
            if not found:
                raise KeyError("LLM instance not found in llms dictionary")
        
        # Update special objects
        self._update_llm_special_objects()

    def _convert_arguments_to_types(
        self,
        arguments: Dict[str, Any],
        tool_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert function arguments to appropriate Python types based on schema.

        Args:
            arguments: Parsed JSON arguments dictionary.
            tool_schema: Tool schema in provider-specific format.

        Returns:
            Arguments dictionary with properly typed values.
        """
        properties = tool_schema.get("function", {}).get("parameters", {}).get("properties", {})
        converted = arguments.copy()
        
        for param_name, param_schema in properties.items():
            if param_name in converted:
                param_type = param_schema.get("type", "string")
                value = converted[param_name]
                
                # Coerce types if needed (JSON parsing usually handles this, but be safe)
                if param_type == "integer" and not isinstance(value, int):
                    try:
                        converted[param_name] = int(value)
                    except (ValueError, TypeError):
                        pass  # Keep original if conversion fails
                elif param_type == "number" and not isinstance(value, (int, float)):
                    try:
                        converted[param_name] = float(value)
                    except (ValueError, TypeError):
                        pass
                elif param_type == "boolean" and not isinstance(value, bool):
                    if isinstance(value, str):
                        converted[param_name] = value.lower() in ("true", "1", "yes")
                    else:
                        converted[param_name] = bool(value)
        
        return converted

    def add_tools(self, tools: List[Callable]) -> None:
        """
        Add tools to the agent mid-conversation.
        
        Args:
            tools: List of callable functions to add as tools.
        """
        if not tools:
            return
        
        # Add tool functions to mapping
        for tool in tools:
            tool_name = tool.__name__
            self.tool_functions[tool_name] = tool
        
        # Re-prepare all tools for current provider
        all_tools = list(self.tool_functions.values())
        provider = self.llm.provider
        prepared = prepare_tools_for_provider(all_tools, provider)
        self.tools = prepared["tools"]
        self.tool_schemas = prepared["schemas"]
    
    def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        return_raw: bool = False,
    ) -> Any:
        """
        Execute a tool function with given arguments.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.
            return_raw: If True, return raw result; if False, return as string.

        Returns:
            Tool execution result as a string (default) or raw result.
        """
        if tool_name not in self.tool_functions:
            error_msg = f"Error: Tool '{tool_name}' not found"
            return error_msg
        
        try:
            func = self.tool_functions[tool_name]
            result = func(**arguments)
            return result if return_raw else str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def run(
        self,
        input_text: str,
        return_raw_tool_result: bool = False,
        llm_instance: Union[str, LLM] = "default",
        max_iterations: int = 10,
    ) -> Any:
        """
        Process input and return response, maintaining conversation history.

        Supports function calling - if the LLM requests a function call,
        executes it and continues the conversation.

        Args:
            input_text: The user's input message.
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
        
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": input_text})

        # Query LLM with full conversation history and tools
        # Tools are cached in __init__ to avoid repeated conversion
        iteration = 0
        accumulated_tool_results = []  # Accumulate results across iterations when return_raw_tool_result=True
        
        while iteration < max_iterations:
            iteration += 1
            
            if self.verbose:
                print_iteration(iteration=iteration, max_iterations=max_iterations)
                print_conversation_context(conversation_history=self.conversation_history)
            
            # Query LLM - use cached tools if available
            if self.tools is not None:
                response = run_llm.query(
                    messages=self.conversation_history,
                    tools=self.tools,
                )
            else:
                response = run_llm.query(messages=self.conversation_history)
            
            if self.verbose:
                print_llm_response(response=response)
            
            # Track usage
            if run_llm.last_usage:
                self.usage_tracker.add_record(
                    usage=run_llm.last_usage,
                    cost=run_llm.last_cost,
                    llm=llm_key,
                )

            # Check if response contains tool calls
            if isinstance(response, dict) and "tool_calls" in response:
                # Handle tool calling - can be multiple tool calls
                tool_calls = response["tool_calls"]
                
                if self.verbose:
                    print_tool_calls(tool_calls=tool_calls)
                
                # Add assistant message with tool_calls to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls,
                })
                
                # Execute each tool call and add results
                tool_results = []
                for tool_call in tool_calls:
                    raw_result = self._process_tool_call(tool_call=tool_call)
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
                self.conversation_history.append({"role": "assistant", "content": response})
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
                self.conversation_history.append({"role": "assistant", "content": response})
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
                self.conversation_history.append({"role": "assistant", "content": response_str})
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
    
    def _process_tool_call(
        self,
        tool_call: Dict[str, Any],
    ) -> Any:
        """
        Process a single tool call: extract, parse, convert types, execute.

        Args:
            tool_call: The tool call dictionary from the LLM response.

        Returns:
            Raw result from the tool execution.
        """
        import json
        
        function_name = tool_call["function"]["name"]
        arguments_json = tool_call["function"]["arguments"]
        
        # Parse JSON string to get arguments
        try:
            function_args = json.loads(arguments_json)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in tool arguments: {arguments_json}")
        
        # Convert types based on schema if available
        if function_name in self.tool_schemas:
            function_args = self._convert_arguments_to_types(
                function_args,
                self.tool_schemas[function_name]
            )
        
        # Execute the function - get raw result for tracking, string for conversation
        raw_result = self._execute_tool(function_name, function_args, return_raw=True)
        string_result = str(raw_result)
        
        if self.verbose:
            print_tool_result(tool_name=function_name, result=raw_result)
        
        # Add tool response with matching tool_call_id (as string for LLM)
        self.conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": string_result,
        })
        
        return raw_result
    
    def reset_conversation(self) -> None:
        """
        Reset conversation, clearing all messages except system prompt.
        """
        if self.system_prompt:
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
        else:
            self.conversation_history = []
    
    def get_total_usage(
        self,
        llm: Optional[str] = None,
    ) -> Dict[str, Optional[int]]:
        """
        Get total usage (tokens) optionally filtered by llm.
        
        Args:
            llm: Optional LLM identifier (key) to filter by. If None, includes all LLMs.
        
        Returns:
            Dictionary with "input_tokens", "output_tokens", and "total_tokens".
        """
        return self.usage_tracker.get_total_usage(llm=llm)
    
    def get_total_cost(
        self,
        llm: Optional[str] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Get total cost optionally filtered by llm.
        
        Args:
            llm: Optional LLM identifier (key) to filter by. If None, includes all LLMs.
        
        Returns:
            Dictionary with "input_cost", "output_cost", and "total_cost".
        """
        return self.usage_tracker.get_total_cost(llm=llm)

