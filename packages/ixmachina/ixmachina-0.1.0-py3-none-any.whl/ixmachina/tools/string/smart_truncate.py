"""
Smart text truncation tools.
"""

import re
from typing import List, Optional, Union


def smart_truncate_text(
    text: str,
    search_terms: Optional[Union[str, List[str]]] = None,
    max_length: int = 8000,
) -> str:
    """
    Intelligently truncate text by finding relevant sections based on search terms.
    
    Searches for search terms in the text, finds their min/max indices,
    and truncates around those sections with a 5% buffer on each side.
    
    Args:
        text: The full text to truncate.
        search_terms: Optional search term(s) to find in the text. Can be a string (single term)
            or a list of strings (multiple terms).
        max_length: Maximum length of truncated text. Default: 8000.
    
    Returns:
        Truncated text focused on relevant sections.
    """
    if len(text) <= max_length:
        return text
    
    if not search_terms:
        # Fallback to simple truncation if no terms provided
        return text[:max_length]
    
    # Normalize to list: convert single string to list
    if isinstance(search_terms, str):
        search_terms = [search_terms]
    
    # Find all occurrences of search terms (case-insensitive)
    text_lower = text.lower()
    all_indices = []
    
    # Use regex for multiple terms (more efficient), simple find() for single term
    if len(search_terms) == 1:
        # Single term: use simple find() approach (no regex overhead)
        term = search_terms[0].lower()
        start = 0
        while True:
            idx = text_lower.find(term, start)
            if idx == -1:
                break
            all_indices.append(idx)
            start = idx + 1
    else:
        # Multiple terms: use regex for single-pass search (more efficient)
        # Escape special regex characters and create pattern
        escaped_terms = [re.escape(term.lower()) for term in search_terms]
        pattern = "|".join(escaped_terms)
        regex = re.compile(pattern, re.IGNORECASE)
        
        # Find all matches in a single pass
        for match in regex.finditer(text_lower):
            all_indices.append(match.start())
    
    if not all_indices:
        # No terms found, use simple truncation
        return text[:max_length]
    
    # Find overall min and max indices across all terms
    min_idx = min(all_indices)
    max_idx = max(all_indices)
    
    # Add 5% buffer on each side
    text_length = len(text)
    buffer = int(text_length * 0.05)
    
    # Find the longest term to ensure we capture it fully
    max_term_length = max(len(term) for term in search_terms) if search_terms else 0
    
    start_idx = max(0, min_idx - buffer)
    end_idx = min(text_length, max_idx + buffer + max_term_length)
    
    # Extract the relevant section
    truncated = text[start_idx:end_idx]
    
    # If still too long, truncate from the end
    if len(truncated) > max_length:
        truncated = truncated[:max_length]
    
    return truncated

