"""Fuzzy matching helpers for PagerDuty toolkit."""

from collections.abc import Iterable
from difflib import SequenceMatcher

from arcade_pagerduty.constants import (
    DISABLE_AUTO_ACCEPT_THRESHOLD,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    FUZZY_MATCH_THRESHOLD,
    MAX_FUZZY_SUGGESTIONS,
)
from arcade_pagerduty.models.tool_outputs import (
    SearchUserMatchOutput,
    UserSummaryOutput,
)


def _compute_match_score(query: str, haystack: str) -> float:
    """Compute match score using best of substring match or fuzzy ratio.

    For short queries, substring matching works better than SequenceMatcher
    which penalizes length differences.
    """
    # Exact substring match gets high score
    if query in haystack:
        # Score based on how much of haystack the query covers
        return max(0.85, len(query) / len(haystack))

    # Check if all query words appear in haystack
    query_words = query.split()
    if query_words and all(word in haystack for word in query_words):
        return 0.80

    # Fall back to fuzzy ratio
    return SequenceMatcher(None, query, haystack).ratio()


def match_users(
    users: Iterable[UserSummaryOutput],
    query: str,
    auto_accept_matches: bool = False,
) -> tuple[list[SearchUserMatchOutput], bool]:
    """Fuzzy match users by name/email with configurable auto-accept.

    Only matches with confidence >= FUZZY_MATCH_THRESHOLD are returned.
    Uses a combination of substring matching and fuzzy ratio for better results.
    """
    q = query.lower().strip()
    if not q:
        return [], False

    matches: list[SearchUserMatchOutput] = []

    for user in users:
        haystack = f"{(user.get('name') or '')} {(user.get('email') or '')}".strip().lower()
        if not haystack:
            continue
        confidence = _compute_match_score(q, haystack)
        # Filter out low-confidence matches
        if confidence < FUZZY_MATCH_THRESHOLD:
            continue
        matches.append({
            "id": user.get("id", ""),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "confidence": confidence,
        })

    matches.sort(key=lambda m: m.get("confidence", 0.0), reverse=True)
    matches = matches[:MAX_FUZZY_SUGGESTIONS]

    threshold = (
        FUZZY_AUTO_ACCEPT_CONFIDENCE if auto_accept_matches else DISABLE_AUTO_ACCEPT_THRESHOLD
    )
    auto_accepted = bool(matches and (matches[0].get("confidence", 0.0) or 0.0) >= threshold)

    return matches, auto_accepted
