"""Fuzzy match a school name across apartments.com / Niche / TEA naming."""
from typing import Optional

from rapidfuzz import fuzz


def best_match(query: str, candidates: list[str], min_score: int = 80) -> Optional[str]:
    """Return the best-matching candidate if it scores >= min_score, else None.

    Uses token_set_ratio so word order and extra tokens (e.g. "School")
    don't hurt the match.
    """
    if not candidates:
        return None
    scored = [(c, fuzz.token_set_ratio(query, c)) for c in candidates]
    best = max(scored, key=lambda x: x[1])
    return best[0] if best[1] >= min_score else None
