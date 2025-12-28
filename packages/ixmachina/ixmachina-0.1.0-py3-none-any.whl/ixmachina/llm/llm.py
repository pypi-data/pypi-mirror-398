"""
LLM connection and querying functionality.
"""

from typing import List, Dict, Optional, Union, Any

from ..utils.addable_dictionary import AddableDictionary
from ..utils.normalize_keys import normalize_key, normalize_keys
from ..utils.usage_tracker import UsageTracker
from .env_var import EnvVar
from .query_openai import query_openai
from .query_anthropic import query_anthropic


class LLM:
    """
    General LLM class that can connect to any LLM provider.

    This class provides a unified interface for connecting to and
    querying various LLM providers without requiring separate classes
    for each provider.
    """

    def __init__(
        self,
        api_key: Union[str, EnvVar],
        model_name: str,
        provider: Optional[str] = None,
        pricing: Optional[Dict[str, Union[float, Dict[str, float]]]] = None,
        fetch_pricing: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize an LLM connection.

        Args:
            api_key: The API key for authentication. Can be a string or an EnvVar instance.
            model_name: The name of the model to use.
            provider: Optional provider name (auto-detected from model_name if not provided).
            pricing: Optional pricing information. Can be:
                - A float: single price per million tokens (same for input/output)
                - A dict with "input" and "output" keys: different prices per million tokens
                Example: {"input": 2.5, "output": 10.0} or 2.5
            fetch_pricing: If True, automatically fetch pricing from the web using get_model_prices.
                Pricing will be fetched lazily on first query if not already set.
            **kwargs: Additional provider-specific parameters.
        """
        # Resolve api_key from environment if EnvVar is provided
        if isinstance(api_key, EnvVar):
            self.api_key = api_key.get_value()
        else:
            self.api_key = api_key

        self.model_name = model_name
        self.extra_kwargs = kwargs

        # Auto-detect provider from model name if not provided
        if provider is None:
            provider = self._detect_provider(model_name)

        self.provider = provider.lower()
        self._initialize_client()
        
        # Usage tracking
        self.last_usage: Optional[Dict[str, int]] = None
        self.total_usage: AddableDictionary = AddableDictionary({
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        })
        
        # Usage tracker (without conversation_id)
        self.usage_tracker = UsageTracker(include_conversation_id=False)
        
        # Pricing and cost tracking
        self.pricing = pricing
        self.fetch_pricing = fetch_pricing
        self._pricing_fetched = False
        self.last_cost: Optional[Dict[str, float]] = None
        self.total_cost: AddableDictionary = AddableDictionary({
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
        })

    def _detect_provider(self, model_name: str) -> str:
        """
        Detect the provider from the model name.

        Args:
            model_name: The model name.

        Returns:
            The detected provider name.
        """
        model_lower = model_name.lower()
        if model_lower.startswith("gpt") or model_lower.startswith("o1"):
            return "openai"
        elif model_lower.startswith("claude"):
            return "anthropic"
        elif model_lower.startswith("gemini"):
            return "google"
        else:
            # Default to OpenAI for unknown models
            return "openai"

    def _initialize_client(self) -> None:
        """Initialize the appropriate client based on provider."""
        if self.provider == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package is required. Install it with: pip install openai"
                )
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "Anthropic package is required. Install it with: pip install anthropic"
                )
            self.client = Anthropic(api_key=self.api_key)
        else:
            raise ValueError(
                f"Unsupported provider: {self.provider}. "
                "Supported providers: openai, anthropic"
            )

    def query(
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Union[str, Dict[str, str], List[Dict[str, str]]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        """
        Query the LLM with a prompt or conversation.

        Either provide user_prompt (and optionally system_prompt) OR provide messages.
        If messages is provided, user_prompt and system_prompt are ignored.

        Args:
            user_prompt: The user's prompt or message (used if messages not provided).
            system_prompt: Optional system prompt for instructions (used if messages not provided).
            messages: Can be:
                - A string (treated as user prompt)
                - A single message dictionary with 'role' and 'content' keys
                - A list of message dictionaries
                Example: [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there"},
                    {"role": "user", "content": "How are you?"}
                ]
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The clean string output from the LLM.
        """
        # Merge extra_kwargs from initialization with query kwargs
        merged_kwargs = {**self.extra_kwargs, **kwargs}

        # Build messages list
        if messages is not None:
            # Normalize messages to a list
            if isinstance(messages, str):
                # String is treated as user prompt
                query_messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                # Single message dictionary
                if "role" not in messages or "content" not in messages:
                    raise ValueError(
                        "Message dictionary must contain 'role' and 'content' keys"
                    )
                query_messages = [messages]
            elif isinstance(messages, list):
                # List of message dictionaries
                query_messages = messages
            else:
                raise ValueError(
                    "messages must be a string, dictionary, or list of dictionaries"
                )
        else:
            if user_prompt is None:
                raise ValueError("Either user_prompt or messages must be provided")
            query_messages = []
            if system_prompt:
                query_messages.append({"role": "system", "content": system_prompt})
            query_messages.append({"role": "user", "content": user_prompt})

        # Fetch pricing if requested and not already fetched
        if self.fetch_pricing and not self._pricing_fetched and self.pricing is None:
            self._fetch_pricing_from_web()
        
        if self.provider == "openai":
            result = query_openai(
                client=self.client,
                model_name=self.model_name,
                messages=query_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **merged_kwargs,
            )
        elif self.provider == "anthropic":
            result = query_anthropic(
                client=self.client,
                model_name=self.model_name,
                messages=query_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **merged_kwargs,
            )
        else:
            raise ValueError(f"Query not implemented for provider: {self.provider}")
        
        # Extract usage and update tracking
        usage = None
        if isinstance(result, dict) and "usage" in result:
            usage = result["usage"]
            # Update last_usage
            self.last_usage = usage.copy()
            # Update total_usage by adding the new usage
            self.total_usage += usage
            
            # Calculate and track costs if pricing is available
            cost = None
            if self.pricing is not None:
                cost = self._calculate_cost(usage=usage)
            
            # Add to usage tracker
            self.usage_tracker.add_record(
                usage=usage,
                cost=cost,
                llm=self.model_name,
            )
        
        # Return content or result (which might be dict with tool_calls)
        if isinstance(result, dict) and "content" in result:
            return result["content"]
        elif isinstance(result, dict) and "tool_calls" in result:
            return result
        else:
            return result
    
    def _fetch_pricing_from_web(self) -> None:
        """
        Fetch pricing from the web using get_model_prices.
        
        This is called lazily on the first query if fetch_pricing=True.
        """
        try:
            from ..tools.pricing import get_model_prices
            
            # Use provider name directly as company name
            company = self.provider
            # Only support known providers
            if company not in ["openai", "anthropic", "google"]:
                return
            
            # Fetch pricing using self (the _pricing_fetched flag prevents recursion)
            result = get_model_prices(company=company, llm=self, max_search_results=5)
            
            if result.get("success") and result.get("prices"):
                prices = result["prices"]
                # Normalize model name for lookup
                normalized_model = normalize_key(self.model_name)
                
                # Normalize all keys in prices dictionary
                normalized_prices = normalize_keys(prices)
                
                # Try exact match first
                price_data = normalized_prices.get(normalized_model)
                if price_data:
                    self.pricing = price_data
                    self._pricing_fetched = True
                    return
                
                # Try partial match (check if normalized_model is contained in any key)
                for key, value in normalized_prices.items():
                    if normalized_model in key or key in normalized_model:
                        self.pricing = value
                        self._pricing_fetched = True
                        return
        except Exception:
            # Silently fail - pricing fetch is optional
            pass
        
        self._pricing_fetched = True
    
    def _calculate_cost(
        self,
        usage: Dict[str, int],
    ) -> Dict[str, float]:
        """
        Calculate cost from usage based on pricing and update tracking.
        
        Updates self.last_cost and self.total_cost.
        
        Args:
            usage: Dictionary with input_tokens, output_tokens, and total_tokens.
        
        Returns:
            Dictionary with "input_cost", "output_cost", and "total_cost" in dollars.
        """
        if self.pricing is None:
            # No pricing available, return None, do not return 0
            return None
        
        # If input_tokens or output_tokens are None, return None, do not return 0
        input_tokens = usage.get("input_tokens", None)
        output_tokens = usage.get("output_tokens", None)
        
        # Handle different pricing formats
        if isinstance(self.pricing, (int, float)):
            # Single price per million tokens (same for input/output)
            price_per_million = float(self.pricing)
            input_cost = (input_tokens / 1_000_000) * price_per_million
            output_cost = (output_tokens / 1_000_000) * price_per_million
        elif isinstance(self.pricing, dict):
            # Different prices for input/output
            input_price = self.pricing.get("input", None)
            output_price = self.pricing.get("output", None)
            
            # If input_price or output_price are None, return None, do not return 0
            if input_price is None or output_price is None:
                return None
            
            input_cost = (input_tokens / 1_000_000) * float(input_price)
            output_cost = (output_tokens / 1_000_000) * float(output_price)
        else:
            return None
        
        total_cost = input_cost + output_cost
        
        cost = {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }
        
        # Update tracking
        self.last_cost = cost
        self.total_cost += cost
        
        return cost
    
    def calculate_cost_from_usage(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> Optional[Dict[str, float]]:
        """
        Calculate cost from input and output tokens.
        
        This is a pure calculator method that does NOT update last_cost or total_cost.
        It only calculates the cost based on the provided tokens and current pricing.
        
        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
        
        Returns:
            Dictionary with "input_cost", "output_cost", and "total_cost" in dollars.
            Returns None if pricing is not set.
        """
        if self.pricing is None:
            return None
        
        # Calculate cost without updating tracking
        if isinstance(self.pricing, (int, float)):
            # Single price per million tokens (same for input/output)
            price_per_million = float(self.pricing)
            input_cost = (input_tokens / 1_000_000) * price_per_million
            output_cost = (output_tokens / 1_000_000) * price_per_million
        elif isinstance(self.pricing, dict):
            # Different prices for input/output
            input_price = self.pricing.get("input")
            output_price = self.pricing.get("output")
            
            if input_price is None or output_price is None:
                return None
            
            input_cost = (input_tokens / 1_000_000) * float(input_price)
            output_cost = (output_tokens / 1_000_000) * float(output_price)
        else:
            return None
        
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }
    
    def get_total_usage(self) -> Dict[str, Optional[int]]:
        """
        Get total usage (tokens) for this LLM.
        
        Returns:
            Dictionary with "input_tokens", "output_tokens", and "total_tokens".
        """
        return self.usage_tracker.get_total_usage(llm=self.model_name)
    
    def get_total_cost(self) -> Dict[str, Optional[float]]:
        """
        Get total cost for this LLM.
        
        Returns:
            Dictionary with "input_cost", "output_cost", and "total_cost".
        """
        return self.usage_tracker.get_total_cost(llm=self.model_name)
