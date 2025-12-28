"""
Web search tools for searching the internet.
"""

from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, quote_plus

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

from .fetch_url import fetch_url
from .constants import BROWSER_USER_AGENT


def search_web(
    query: str,
    max_results: Optional[int] = 10,
    search_engine: str = "duckduckgo",
    domain_filter: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Search the web using a specified search engine and return search results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return. Default: 10.
        search_engine: Search engine to use. Options: "duckduckgo" (default), "startpage".
        domain_filter: Optional domain filter(s) to restrict results to specific domains.
                      Can be a string (single domain) or list of strings (multiple domains).
                      Example: "openai.com" or ["openai.com", "anthropic.com"].

    Returns:
        Dictionary with:
            - success: Boolean indicating if search was successful
            - results: List of search results, each containing:
                - title: Result title
                - url: Result URL
                - snippet: Result description/snippet
            - count: Number of results returned
            - query: The original search query
            - search_engine: The search engine used
            - error: Error message if search failed (None if successful)
    """
    # Normalize domain_filter to a list
    if domain_filter is not None:
        if isinstance(domain_filter, str):
            domain_filter = [domain_filter]
    
    search_engine_lower = search_engine.lower()
    
    if search_engine_lower == "duckduckgo":
        return _search_duckduckgo(query=query, max_results=max_results, domain_filter=domain_filter)
    elif search_engine_lower == "startpage":
        return _search_startpage(query=query, max_results=max_results, domain_filter=domain_filter)
    else:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "query": query,
            "search_engine": search_engine,
            "error": f"Unknown search engine: {search_engine}. Supported: duckduckgo, startpage",
        }


def _search_duckduckgo(
    query: str,
    max_results: int,
    domain_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search using DuckDuckGo via the duckduckgo-search package.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
        domain_filter: Optional list of domain filters.

    Returns:
        Dictionary with search results.
    """
    if DDGS is None:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "query": query,
            "search_engine": "duckduckgo",
            "error": "ddgs package is required. Install it with: pip install ddgs",
        }
    
    try:
        # If domain filter is used, fetch more results initially to account for filtering
        fetch_count = max_results * 5 if domain_filter else max_results
        
        with DDGS() as ddgs:
            # Use text() method to get web search results
            search_results = ddgs.text(
                query=query,
                max_results=fetch_count,
            )
        
        # Convert to our format
        all_results = []
        for result in search_results:
            all_results.append({
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", ""),
            })
        
        # Apply domain filter if provided
        if domain_filter:
            filtered_results = []
            for result in all_results:
                url = result.get("url", "")
                if not url:
                    continue
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.lower()
                # Check if domain matches any filter (subdomain matching)
                if any(filter_domain in domain for filter_domain in domain_filter):
                    filtered_results.append(result)
                    # Stop if we have enough
                    if len(filtered_results) >= max_results:
                        break
            results = filtered_results
        else:
            results = all_results[:max_results]
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
            "search_engine": "duckduckgo",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "query": query,
            "search_engine": "duckduckgo",
            "error": f"Error performing search: {str(e)}",
        }


def _search_startpage(
    query: str,
    max_results: int,
    domain_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search using Startpage (privacy-focused search engine).

    Uses Startpage's search URL format to fetch and parse results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
        domain_filter: Optional list of domain filters.

    Returns:
        Dictionary with search results.
    """
    try:
        # Construct Startpage search URL
        encoded_query = quote_plus(query)
        search_url = f"https://www.startpage.com/sp/search?query={encoded_query}"
        
        # Fetch the search results page
        page_response = fetch_url(url=search_url, headers={"User-Agent": BROWSER_USER_AGENT})
        
        if not page_response["success"]:
            return {
                "success": False,
                "results": [],
                "count": 0,
                "query": query,
                "search_engine": "startpage",
                "error": f"Failed to fetch search page: {page_response.get('error')}",
            }
        
        # Parse HTML to extract search results
        html_content = page_response.get("content")
        if not html_content:
            return {
                "success": False,
                "results": [],
                "count": 0,
                "query": query,
                "search_engine": "startpage",
                "error": "No content returned from search page",
            }
        
        # Parse HTML using BeautifulSoup directly for more control
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract search results from parsed HTML
        # Startpage results are typically in specific HTML structures
        # This is a basic implementation - may need adjustment based on actual HTML structure
        all_results = []
        
        # Try to find result links and titles in the parsed HTML
        # Startpage typically uses specific classes/selectors for results
        # Common patterns: links with titles and snippets
        if soup:
            # Look for result containers - Startpage uses various selectors
            # Common patterns: divs with class containing "result" or "web-result"
            result_containers = soup.find_all(
                ["div", "article"],
                class_=lambda x: x and ("result" in x.lower() or "web-result" in x.lower())
            )
            
            # If no containers found, try alternative selectors
            if not result_containers:
                # Try finding links that look like search results
                result_links = soup.find_all("a", href=True)
                for link in result_links[:max_results * 3]:  # Get more to filter
                    href = link.get("href", "")
                    title = link.get_text(strip=True)
                    
                    # Skip if it's not a proper result link
                    if not href or not title or href.startswith("#") or href.startswith("javascript:"):
                        continue
                    
                    # Find snippet (description) - usually in nearby elements
                    snippet = ""
                    parent = link.parent
                    if parent:
                        # Look for description in sibling or parent elements
                        desc_elem = parent.find(["p", "span"], class_=lambda x: x and "desc" in x.lower() if x else False)
                        if desc_elem:
                            snippet = desc_elem.get_text(strip=True)
                    
                    all_results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet,
                    })
            else:
                # Extract from result containers
                for container in result_containers[:max_results * 3]:
                    link = container.find("a", href=True)
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    
                    # Find snippet
                    snippet_elem = container.find(["p", "span"], class_=lambda x: x and "desc" in x.lower() if x else False)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if title and href:
                        all_results.append({
                            "title": title,
                            "url": href,
                            "snippet": snippet,
                        })
        
        # Apply domain filter if provided
        if domain_filter:
            filtered_results = []
            for result in all_results:
                url = result.get("url", "")
                if not url:
                    continue
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.lower()
                # Check if domain matches any filter (subdomain matching)
                if any(filter_domain.lower() in domain for filter_domain in domain_filter):
                    filtered_results.append(result)
                    # Stop if we have enough
                    if len(filtered_results) >= max_results:
                        break
            results = filtered_results
        else:
            results = all_results[:max_results]
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
            "search_engine": "startpage",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "query": query,
            "search_engine": "startpage",
            "error": f"Error performing search: {str(e)}",
        }


def search_web_simple(
    query: str,
    search_engine: str = "duckduckgo",
) -> List[Dict[str, str]]:
    """
    Simple web search that returns just the results list.

    Args:
        query: The search query string.
        search_engine: Search engine to use. Options: "duckduckgo" (default), "startpage".

    Returns:
        List of search results, each containing:
            - title: Result title
            - url: Result URL
            - snippet: Result description/snippet
    """
    result = search_web(query=query, search_engine=search_engine)
    if result["success"]:
        return result["results"]
    else:
        return []

