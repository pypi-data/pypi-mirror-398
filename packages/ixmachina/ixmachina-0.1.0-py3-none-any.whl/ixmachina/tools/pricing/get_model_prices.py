"""
Tools for fetching model pricing information from company websites.
"""

from typing import Dict, Any, Optional, List

from ..web.search_web import search_web
from ..web.extract_from_page import extract_from_page
from ..string.infer_type import infer_string_type


def get_model_prices(
    company: str,
    llm: Any,
    max_search_results: int = 5,
) -> Dict[str, Any]:
    """
    Get model pricing information from a company's website.

    Searches the web for pricing pages, filters to company domains,
    extracts pricing using LLM, and returns a dictionary of model names
    to prices per million tokens (in dollars as float).

    If pricing differs by type (input, output, cached_input, training, etc.),
    returns a dictionary with "input" and "output" keys for each model.

    Args:
        company: Company name (e.g., "openai", "anthropic", "google").
        llm: LLM instance to use for extraction (can be passed via special objects as "use:llm").
        max_search_results: Maximum number of search results to check. Default: 5.

    Returns:
        Dictionary with:
            - success: Boolean indicating if extraction was successful
            - prices: Dictionary mapping model names to prices per million tokens.
                     If pricing differs by type, each model maps to a dict with "input" and "output" keys (float, in dollars).
                     If pricing is the same, maps directly to a float.
            - company: The company name
            - url: The URL where pricing was extracted from (None if failed)
            - error: Error message if extraction failed (None if successful)
    """
    try:
        # Get two-part domain filters for the company
        company_lower = company.lower()
        domain_filter = _get_two_part_domains(company_lower)
        
        # Search for pricing pages with domain filters
        # Use more specific query to find official pricing pages
        search_query = f"{company} pricing models tokens official"
        search_result = search_web(
            query=search_query,
            max_results=max_search_results * 2,  # Get more results to filter
            search_engine="duckduckgo",
            domain_filter=domain_filter,
        )
        
        if not search_result["success"] or search_result["count"] == 0:
            return {
                "success": False,
                "prices": {},
                "company": company,
                "url": None,
                "error": f"Failed to find pricing pages: {search_result.get('error', 'No results')}",
            }
        
        # Try to extract pricing from the results (already filtered by search_web)
        # Filter out community/forum pages - they don't have official pricing
        # Prefer official pricing pages (platform.openai.com, docs, api/pricing)
        filtered_results = []
        preferred_results = []
        
        for r in search_result["results"]:
            url = r.get("url", "").lower()
            # Skip community/forum pages
            if "community" in url or "forum" in url:
                continue
            # Prefer official pricing pages
            if any(term in url for term in ["platform", "docs/pricing", "api/pricing", "pricing"]):
                preferred_results.append(r)
            else:
                filtered_results.append(r)
        
        # Use preferred results first, then others
        filtered_results = preferred_results + filtered_results
        
        # If no results after filtering, use all results (except community)
        if not filtered_results:
            filtered_results = [
                r for r in search_result["results"]
                if "community" not in r.get("url", "").lower()
                and "forum" not in r.get("url", "").lower()
            ]
        
        for result in filtered_results:
            url = result.get("url", "")
            
            # Extract pricing information using LLM
            extraction_result = extract_from_page(
                url=url,
                query=(
                    "Extract ALL model names and their pricing per million tokens in dollars. "
                    "Include every model mentioned on the page (GPT-4, GPT-4o, GPT-4o-mini, GPT-3.5-turbo, GPT-4-turbo, Ada, Babbage, Curie, Davinci, etc.). "
                    "Return as a JSON dictionary where keys are model names. "
                    "If pricing differs by type (input, output, cached_input, training, etc.), each model should map to a dictionary with 'input' and 'output' keys (as floats). "
                    "If pricing is the same for all types, map directly to a float. "
                    "Always include both input and output prices if they are different. "
                    "Extract ALL models, not just one."
                ),
                llm=llm,
                search_terms=[
                    "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5", "gpt-4-turbo",
                    "ada", "babbage", "curie", "davinci",
                    "pricing", "price", "token", "per million",
                ],
            )
            
            if not extraction_result["success"]:
                continue
            
            extracted_content = extraction_result["extracted"]
            
            # Use infer_string_type to convert to dictionary if needed
            type_result = infer_string_type(
                text=extracted_content,
                llm=llm,
                max_length=4000,
            )
            
            if not type_result["success"]:
                continue
            
            # If the result is a dictionary, extract it
            if type_result["type"] == "dict":
                prices_dict = type_result["value"]
                
                # Validate and clean the dictionary
                cleaned_prices = _clean_prices_dict(prices_dict)
                
                if cleaned_prices:
                    return {
                        "success": True,
                        "prices": cleaned_prices,
                        "company": company,
                        "url": url,
                        "error": None,
                    }
            
            # If it's a string, try to extract JSON from it
            elif type_result["type"] == "str":
                # Try to parse as JSON again with LLM
                json_extraction = extract_from_page(
                    url=url,
                    query=(
                        "Extract ALL model pricing as a JSON dictionary. "
                        "Include every model on the page (GPT-4, GPT-4o, GPT-4o-mini, GPT-3.5-turbo, GPT-4-turbo, Ada, Babbage, Curie, Davinci, etc.). "
                        "Keys are model names. "
                        "If pricing differs by type, each model maps to a dict with 'input' and 'output' keys (floats per million tokens). "
                        "If same, map directly to float per million tokens. "
                        "Return ONLY valid JSON, no other text. "
                        "Extract ALL models, not just one."
                    ),
                    llm=llm,
                    search_terms=[
                        "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5", "gpt-4-turbo",
                        "ada", "babbage", "curie", "davinci",
                        "pricing", "price", "token", "per million",
                    ],
                )
                
                if json_extraction["success"]:
                    json_type_result = infer_string_type(
                        text=json_extraction["extracted"],
                        llm=llm,
                        max_length=4000,
                    )
                    
                    if json_type_result["success"] and json_type_result["type"] == "dict":
                        cleaned_prices = _clean_prices_dict(json_type_result["value"])
                        if cleaned_prices:
                            return {
                                "success": True,
                                "prices": cleaned_prices,
                                "company": company,
                                "url": url,
                                "error": None,
                            }
        
        return {
            "success": False,
            "prices": {},
            "company": company,
            "url": None,
            "error": "Could not extract valid pricing information from any results",
        }
    
    except Exception as e:
        return {
            "success": False,
            "prices": {},
            "company": company,
            "url": None,
            "error": f"Error fetching pricing: {str(e)}",
        }


def _get_two_part_domains(company: str) -> List[str]:
    """
    Get list of two-part domain filters for a company.

    Only returns two-part domains (e.g., "openai.com", not "azure.microsoft.com").
    This is used for domain filtering in search_web.

    Args:
        company: Company name in lowercase.

    Returns:
        List of two-part domain filters (e.g., ["openai.com", "claude.com"]).
    """
    company_domain_map = {
        "openai": ["openai.com"],
        "anthropic": ["anthropic.com", "claude.com"],
        "google": ["google.com", "deepmind.com"],
        "meta": ["meta.com", "facebook.com"],
        "microsoft": ["microsoft.com"],
        "amazon": ["amazon.com", "aws.amazon.com"],
        "cohere": ["cohere.com"],
        "mistral": ["mistral.ai"],
    }
    
    return company_domain_map.get(company, [f"{company}.com", f"{company}.ai"])

def _clean_prices_dict(prices_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and validate a prices dictionary.

    Converts all values to floats (per million tokens) and filters out invalid entries.
    Handles both simple pricing (float) and type-based pricing (dict with input/output).

    Args:
        prices_dict: Dictionary that may contain pricing information.

    Returns:
        Cleaned dictionary with model names as keys and prices as values.
        Values are either floats (per million tokens) or dicts with "input" and "output" keys.
    """
    cleaned = {}
    
    for key, value in prices_dict.items():
        # Skip non-string keys
        if not isinstance(key, str):
            continue
        
        # Replace spaces with underscores in keys
        cleaned_key = key.replace(" ", "_")
        
        # Handle dictionary values (input/output pricing)
        if isinstance(value, dict):
            input_price = None
            output_price = None
            
            # Look for input price
            for input_key in ["input", "input_price", "input_tokens", "prompt", "prompt_tokens"]:
                if input_key in value:
                    input_price = _convert_to_float_per_million(value[input_key])
                    break
            
            # Look for output price
            for output_key in ["output", "output_price", "output_tokens", "completion", "completion_tokens"]:
                if output_key in value:
                    output_price = _convert_to_float_per_million(value[output_key])
                    break
            
            # If we found both, create a dict with input/output
            if input_price is not None and output_price is not None:
                cleaned[cleaned_key] = {
                    "input": input_price,
                    "output": output_price,
                }
            # If only one found, use it for both
            elif input_price is not None:
                cleaned[cleaned_key] = {
                    "input": input_price,
                    "output": input_price,
                }
            elif output_price is not None:
                cleaned[cleaned_key] = {
                    "input": output_price,
                    "output": output_price,
                }
        
        # Handle simple float/int/string values
        else:
            price = _convert_to_float_per_million(value)
            if price is not None and price > 0:
                cleaned[cleaned_key] = price
    
    return cleaned


def _convert_to_float_per_million(value: Any) -> Optional[float]:
    """
    Convert a value to float representing price per million tokens.

    Handles values that might be per token, per 1K tokens, per 10K tokens, etc.
    Converts them all to per million tokens.

    Args:
        value: Value to convert (int, float, or string).

    Returns:
        Float representing price per million tokens, or None if conversion fails.
    """
    try:
        if isinstance(value, (int, float)):
            price = float(value)
        elif isinstance(value, str):
            # Remove currency symbols, whitespace, and common units
            cleaned_value = value.replace("$", "").replace(",", "").strip().lower()
            
            # Check for unit indicators and convert accordingly
            if "per million" in cleaned_value or "/million" in cleaned_value or "/m" in cleaned_value:
                # Already per million, extract number
                cleaned_value = cleaned_value.replace("per million", "").replace("/million", "").replace("/m", "").strip()
                price = float(cleaned_value)
            elif "per 1k" in cleaned_value or "/1k" in cleaned_value or "/k" in cleaned_value:
                # Per 1K tokens, multiply by 1000
                cleaned_value = cleaned_value.replace("per 1k", "").replace("/1k", "").replace("/k", "").strip()
                price = float(cleaned_value) * 1000
            elif "per 10k" in cleaned_value or "/10k" in cleaned_value:
                # Per 10K tokens, multiply by 100
                cleaned_value = cleaned_value.replace("per 10k", "").replace("/10k", "").strip()
                price = float(cleaned_value) * 100
            elif "per token" in cleaned_value or "/token" in cleaned_value:
                # Per token, multiply by 1,000,000
                cleaned_value = cleaned_value.replace("per token", "").replace("/token", "").strip()
                price = float(cleaned_value) * 1000000
            else:
                # Assume it's already per million or try to parse as-is
                price = float(cleaned_value)
        else:
            return None
        
        # Only return positive prices
        if price > 0:
            return price
        return None
    
    except (ValueError, TypeError):
        return None

