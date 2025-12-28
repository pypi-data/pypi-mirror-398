"""
Web-related tools for fetching URLs, scraping, etc.
"""

from .fetch_url import fetch_url, fetch_json, post_request
from .parse_html import parse_html, extract_text, find_elements
from .search_web import search_web, search_web_simple
from .extract_from_page import extract_from_page

__all__ = [
    "fetch_url",
    "fetch_json",
    "post_request",
    "parse_html",
    "extract_text",
    "find_elements",
    "search_web",
    "search_web_simple",
    "extract_from_page",
]
