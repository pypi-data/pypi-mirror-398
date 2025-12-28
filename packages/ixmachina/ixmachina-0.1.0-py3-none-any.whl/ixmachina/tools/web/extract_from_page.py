"""
Tools for extracting specific information from web pages using LLM.
"""

from typing import Dict, Optional, Any, List, Union

from .fetch_url import fetch_url
from .parse_html import extract_text
from .constants import BROWSER_USER_AGENT
from ..string.smart_truncate import smart_truncate_text


def extract_from_page(
    url: str,
    query: str,
    llm: Any,
    search_terms: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Extract specific information from a web page using an LLM.

    Fetches the page, extracts text content, and uses the LLM to find
    the specific information requested in the query.

    Args:
        url: The URL of the web page to extract from.
        query: What to find/extract from the page (e.g., "price", "contact email", "product name").
        llm: LLM instance to use for extraction (can be passed via special objects as "use:llm").

    Returns:
        Dictionary with:
            - success: Boolean indicating if extraction was successful
            - extracted: The extracted information as a string
            - url: The URL that was queried
            - query: The original query
            - error: Error message if extraction failed (None if successful)
    """
    try:
        # Fetch the page with browser headers to avoid 403 errors
        headers = {"User-Agent": BROWSER_USER_AGENT}
        page_response = fetch_url(url=url, headers=headers)
        
        if not page_response["success"]:
            return {
                "success": False,
                "extracted": None,
                "url": url,
                "query": query,
                "error": f"Failed to fetch page: {page_response['error']}",
            }
        
        # Extract text from HTML
        html_content = page_response["content"]
        page_text = extract_text(html_content)
        
        # Use LLM to extract the specific information
        # Smart truncation: find relevant sections based on search terms
        limited_text = smart_truncate_text(
            text=page_text,
            search_terms=search_terms,
            max_length=8000,
        )
        prompt = (
            f"Extract the following information from the web page content below:\n\n"
            f"Query: {query}\n\n"
            f"Web page content:\n"
            f"{limited_text}\n\n"
            f"Return only the extracted information, nothing else. If the information is not found, say \"Information not found\"."
        )

        llm_response = llm.query(user_prompt=prompt)
        
        # LLM.query can return string or dict (with "content" key when usage tracking is enabled)
        if isinstance(llm_response, dict):
            # If it's a dict, extract the content (or convert to string if no content key)
            extracted = llm_response.get("content", str(llm_response))
        else:
            # Normal case: string response
            extracted = str(llm_response)
        
        return {
            "success": True,
            "extracted": extracted.strip(),
            "url": url,
            "query": query,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "extracted": None,
            "url": url,
            "query": query,
            "error": f"Error extracting information: {str(e)}",
        }



