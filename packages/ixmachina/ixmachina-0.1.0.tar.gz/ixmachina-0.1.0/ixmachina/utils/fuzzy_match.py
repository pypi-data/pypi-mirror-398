"""
Fuzzy string matching utilities.

Uses efficient algorithms including difflib.SequenceMatcher and optionally RapidFuzz
for high-performance fuzzy string matching.
"""

from difflib import SequenceMatcher
from typing import List, Optional

# Try to import RapidFuzz for better performance (optional dependency)
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


def fuzzy_match(
    query: str,
    candidates: List[str],
    threshold: float = 0.6,
    max_results: Optional[int] = None,
) -> List[str]:
    """
    Find candidates that fuzzy match a query string.
    
    Uses efficient algorithms (RapidFuzz if available, otherwise difflib.SequenceMatcher)
    and returns candidates sorted by best match. Optimized for performance.
    
    Args:
        query: The query string to match against.
        candidates: List of candidate strings to search.
        threshold: Minimum similarity score (0.0 to 1.0) to include a candidate.
                  Default: 0.6
        max_results: Maximum number of results to return. If None, returns all matches.
                    Default: None
    
    Returns:
        List of matching candidate strings, sorted by similarity (best first).
    """
    if not query or not candidates:
        return []
    
    query_stripped = query.strip()
    if not query_stripped:
        return []
    
    # Use RapidFuzz if available (much faster)
    if RAPIDFUZZ_AVAILABLE:
        return _fuzzy_match_rapidfuzz(
            query=query_stripped,
            candidates=candidates,
            threshold=threshold,
            max_results=max_results,
        )
    else:
        return _fuzzy_match_difflib(
            query=query_stripped,
            candidates=candidates,
            threshold=threshold,
            max_results=max_results,
        )


def _fuzzy_match_rapidfuzz(
    query: str,
    candidates: List[str],
    threshold: float,
    max_results: Optional[int],
) -> List[str]:
    """
    Fast fuzzy matching using RapidFuzz library.
    
    Uses RapidFuzz's optimized algorithms for high-performance matching.
    """
    # RapidFuzz's process.extract is highly optimized
    # It uses multiple algorithms and returns best matches
    results = process.extract(
        query=query,
        choices=candidates,
        limit=max_results if max_results is not None else len(candidates),
        score_cutoff=int(threshold * 100),  # RapidFuzz uses 0-100 scale
    )
    
    # Extract just the candidate strings, sorted by score (already sorted by process.extract)
    return [candidate for candidate, score, _ in results]


def _fuzzy_match_difflib(
    query: str,
    candidates: List[str],
    threshold: float,
    max_results: Optional[int],
) -> List[str]:
    """
    Fuzzy matching using Python's built-in difflib.SequenceMatcher.
    
    Efficient fallback when RapidFuzz is not available.
    """
    query_lower = query.lower()
    query_len = len(query_lower)
    
    if query_len == 0:
        return []
    
    scored_candidates = []
    matcher = SequenceMatcher()
    matcher.set_seq1(query_lower)
    
    # Fast path: exact matches
    exact_matches = []
    other_candidates = []
    
    for candidate in candidates:
        candidate_stripped = candidate.strip()
        if not candidate_stripped:
            continue
        
        candidate_lower = candidate_stripped.lower()
        
        # Exact match (case-insensitive) - highest priority
        if query_lower == candidate_lower:
            exact_matches.append(candidate_stripped)
        else:
            other_candidates.append((candidate_stripped, candidate_lower))
    
    # Add exact matches first
    for candidate in exact_matches:
        scored_candidates.append((1.0, candidate))
    
    # Process other candidates with SequenceMatcher
    for candidate, candidate_lower in other_candidates:
        matcher.set_seq2(candidate_lower)
        ratio = matcher.ratio()
        
        if ratio >= threshold:
            scored_candidates.append((ratio, candidate))
    
    # Sort by score (descending)
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    # Apply max_results limit
    if max_results is not None and max_results > 0:
        scored_candidates = scored_candidates[:max_results]
    
    return [candidate for _, candidate in scored_candidates]



