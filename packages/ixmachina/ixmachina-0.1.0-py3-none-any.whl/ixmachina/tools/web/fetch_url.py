"""
Web fetching tools for HTTP requests.
"""

from typing import Dict, Optional, Any
import requests

from .constants import BROWSER_USER_AGENT


def fetch_url(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 30,
) -> Dict[str, Any]:
    """
    Fetch content from a URL using HTTP GET request.

    Args:
        url: The URL to fetch.
        headers: Optional HTTP headers to include in the request.
        timeout: Request timeout in seconds. Default: 30.

    Returns:
        Dictionary with:
            - status_code: HTTP status code
            - content: Response content as string
            - headers: Response headers as dictionary
            - content_type: Content type from headers
            - url: Final URL after redirects
            - success: Boolean indicating if request was successful
            - error: Error message if request failed (None if successful)
    """
    try:
        response = requests.get(url=url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "content": response.text,
            "headers": dict(response.headers),
            "content_type": response.headers.get("Content-Type", ""),
            "url": response.url,
            "success": True,
            "error": None,
        }
    except requests.RequestException as e:
        return {
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
            "content": None,
            "headers": dict(e.response.headers) if hasattr(e, "response") and e.response else {},
            "content_type": None,
            "url": url,
            "success": False,
            "error": str(e),
        }


def fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 30,
) -> Dict[str, Any]:
    """
    Fetch a URL and parse the response as JSON.

    Uses fetch_url internally and then parses the content as JSON.

    Args:
        url: The URL to fetch.
        headers: Optional HTTP headers to include in the request.
        timeout: Request timeout in seconds. Default: 30.

    Returns:
        Dictionary with:
            - status_code: HTTP status code
            - data: Parsed JSON data (dict or list) if successful
            - headers: Response headers as dictionary
            - url: Final URL after redirects
            - success: Boolean indicating if request and parsing were successful
            - error: Error message if request or parsing failed (None if successful)
    """
    # Use fetch_url to get the response
    response = fetch_url(url=url, headers=headers, timeout=timeout)
    
    # If the HTTP request failed, return the error
    if not response["success"]:
        return {
            "status_code": response["status_code"],
            "data": None,
            "headers": response["headers"],
            "url": response["url"],
            "success": False,
            "error": response["error"],
        }
    
    # Try to parse the content as JSON
    try:
        import json
        json_data = json.loads(response["content"])
        return {
            "status_code": response["status_code"],
            "data": json_data,
            "headers": response["headers"],
            "url": response["url"],
            "success": True,
            "error": None,
        }
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "status_code": response["status_code"],
            "data": None,
            "headers": response["headers"],
            "url": response["url"],
            "success": False,
            "error": f"Error parsing JSON: {str(e)}",
        }


def post_request(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = 30,
) -> Dict[str, Any]:
    """
    Send an HTTP POST request to a URL.

    Args:
        url: The URL to post to.
        data: Data to send (will be JSON encoded). Default: None.
        headers: Optional HTTP headers to include in the request.
        timeout: Request timeout in seconds. Default: 30.

    Returns:
        Dictionary with:
            - status_code: HTTP status code
            - content: Response content as string
            - headers: Response headers as dictionary
            - content_type: Content type from headers
            - url: Final URL after redirects
            - success: Boolean indicating if request was successful
            - error: Error message if request failed (None if successful)
    """
    try:
        json_data = data if data else None
        response = requests.post(
            url=url,
            json=json_data,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "content": response.text,
            "headers": dict(response.headers),
            "content_type": response.headers.get("Content-Type", ""),
            "url": response.url,
            "success": True,
            "error": None,
        }
    except requests.RequestException as e:
        return {
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
            "content": None,
            "headers": dict(e.response.headers) if hasattr(e, "response") and e.response else {},
            "content_type": None,
            "url": url,
            "success": False,
            "error": str(e),
        }

