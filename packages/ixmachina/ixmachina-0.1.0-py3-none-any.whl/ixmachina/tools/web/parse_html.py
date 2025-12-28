"""
HTML parsing tools using BeautifulSoup.
"""

from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup


def parse_html(
    html_content: str,
    selector: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Parse HTML content and optionally extract elements by CSS selector.

    Args:
        html_content: The HTML content to parse.
        selector: Optional CSS selector to find specific elements. If None, returns document structure.

    Returns:
        Dictionary with:
            - success: Boolean indicating if parsing was successful
            - elements: List of extracted elements (if selector provided) or None
            - text: Full text content of the document (if no selector)
            - title: Page title if available
            - error: Error message if parsing failed (None if successful)
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        result = {
            "success": True,
            "error": None,
        }
        
        # Extract title if available
        title_tag = soup.find("title")
        result["title"] = title_tag.get_text(strip=True) if title_tag else None
        
        if selector:
            # Find elements by CSS selector
            elements = soup.select(selector)
            result["elements"] = [
                {
                    "text": elem.get_text(strip=True),
                    "html": str(elem),
                    "tag": elem.name,
                    "attributes": dict(elem.attrs) if elem.attrs else {},
                }
                for elem in elements
            ]
            result["count"] = len(elements)
        else:
            # Return full text content
            result["text"] = soup.get_text(separator=" ", strip=True)
            result["elements"] = None
        
        return result
    except Exception as e:
        return {
            "success": False,
            "elements": None,
            "text": None,
            "title": None,
            "error": f"Error parsing HTML: {str(e)}",
        }


def extract_text(html_content: str) -> str:
    """
    Extract all text content from HTML, removing HTML tags.

    Args:
        html_content: The HTML content to extract text from.

    Returns:
        Plain text content with HTML tags removed.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def find_elements(
    html_content: str,
    selector: str,
) -> List[Dict[str, Any]]:
    """
    Find HTML elements by CSS selector and return their content.

    Args:
        html_content: The HTML content to search.
        selector: CSS selector to find elements.

    Returns:
        List of dictionaries, each containing:
            - text: Text content of the element
            - html: HTML representation of the element
            - tag: HTML tag name
            - attributes: Dictionary of element attributes
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        elements = soup.select(selector)
        return [
            {
                "text": elem.get_text(strip=True),
                "html": str(elem),
                "tag": elem.name,
                "attributes": dict(elem.attrs) if elem.attrs else {},
            }
            for elem in elements
        ]
    except Exception as e:
        return [{"error": f"Error finding elements: {str(e)}"}]

