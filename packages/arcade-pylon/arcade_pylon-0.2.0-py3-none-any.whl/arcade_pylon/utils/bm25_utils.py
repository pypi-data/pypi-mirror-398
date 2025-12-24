"""BM25 text search utilities for issue lookup.

BM25 (Best Match 25) is a ranking function for text retrieval. This module
provides utilities to search issues by title and description.

## Tips for LLM Query Optimization

When constructing BM25 search queries:
1. Use specific keywords from the problem domain (e.g., "authentication", "timeout")
2. Use word stems/roots for better matching:
   - "authenticate" matches "authentication", "authenticating"
   - Use roots like "auth" instead of "authentication"
   - "resolv" matches "resolve", "resolving", "resolved"
   - "config" matches "configure", "configuration", "configured"
3. Avoid very common words (a, the, is, are) - they add noise
4. Use multiple keywords for better precision (e.g., "login timeout" vs just "login")
5. Boolean operators: AND (both required), OR (either), NOT or - (exclude)
6. Shorter, focused queries work better than long sentences

Examples of good queries:
- "auth timeout" (word stems)
- "password reset email" (multiple related terms)
- "dashboard AND slow" (boolean AND)
- "error NOT test" (exclude test issues)
- "config fail" (short stems match more variations)

Examples of poor queries:
- "the issue with the login page" (too many common words)
- "can you find the problem" (no domain keywords)
- "authentication" (full word - use "auth" for broader match)
"""

import re
from typing import Any

from rank_bm25 import BM25Plus

from arcade_pylon.constants import (
    BM25_AUTO_ACCEPT_THRESHOLD,
    BM25_DEFAULT_TOP_K,
    BM25_MIN_SCORE_THRESHOLD,
)
from arcade_pylon.models.tool_outputs.search import BM25SearchResult


def tokenize_text(text: str) -> list[str]:
    """Tokenize text for BM25 indexing.

    Converts to lowercase and extracts alphanumeric tokens.
    No stopword removal - BM25Plus handles term frequency naturally.

    Args:
        text: Text to tokenize.

    Returns:
        List of lowercase tokens.
    """
    if not text:
        return []
    text = text.lower()
    return re.findall(r"\b[a-z0-9]+\b", text)


def parse_boolean_query(query: str) -> dict[str, list[str]]:
    """Parse a query string for boolean operators.

    Supports:
        - AND: terms that must be present (default behavior)
        - OR: terms where any can be present
        - NOT or -: terms that must not be present

    Args:
        query: Search query string.

    Returns:
        Dict with 'required', 'optional', 'excluded' term lists.
    """
    query = query.strip()

    excluded: list[str] = []
    optional: list[str] = []
    required: list[str] = []

    parts = re.split(r"\s+", query)
    i = 0
    while i < len(parts):
        part = parts[i]
        part_upper = part.upper()

        if part_upper == "NOT" and i + 1 < len(parts):
            excluded.extend(tokenize_text(parts[i + 1]))
            i += 2
            continue

        if part.startswith("-") and len(part) > 1:
            excluded.extend(tokenize_text(part[1:]))
            i += 1
            continue

        if part_upper == "OR" and i + 1 < len(parts):
            if required:
                optional.append(required.pop())
            optional.extend(tokenize_text(parts[i + 1]))
            i += 2
            continue

        if part_upper == "AND":
            i += 1
            continue

        tokens = tokenize_text(part)
        required.extend(tokens)
        i += 1

    return {
        "required": required,
        "optional": optional,
        "excluded": excluded,
    }


def _build_searchable_text(issue: dict[str, Any]) -> str:
    """Build searchable text from issue title and description."""
    title = issue.get("title", "") or ""
    body = issue.get("body_html", "") or ""
    body_text = re.sub(r"<[^>]+>", " ", body)
    return f"{title} {body_text}"


def _apply_boolean_filters(
    scores: list[float],
    corpus: list[list[str]],
    parsed: dict[str, list[str]],
) -> list[float]:
    """Apply boolean exclusion and required term penalties to scores."""
    for i, doc_tokens in enumerate(corpus):
        if parsed["excluded"] and any(excl in doc_tokens for excl in parsed["excluded"]):
            scores[i] = 0.0
        elif parsed["required"]:
            doc_set = set(doc_tokens)
            if not all(req in doc_set for req in parsed["required"]):
                scores[i] = scores[i] * 0.5
    return scores


def _format_result(issue: dict[str, Any], score: float) -> BM25SearchResult:
    """Format issue and score into BM25SearchResult."""
    return {
        "issue_id": issue.get("id", ""),
        "issue_number": issue.get("number", 0),
        "title": issue.get("title", ""),
        "score": round(float(score), 4),
        "link": issue.get("link", ""),
    }


def format_bm25_suggestions(results: list[BM25SearchResult]) -> str:
    """Format BM25 results as suggestion text for RetryableToolError."""
    return "\n".join(
        f"- #{r['issue_number']}: {r['title']} (ID: {r['issue_id']}, score: {r['score']:.2f})"
        for r in results
    )


def search_issues_bm25(
    issues: list[dict[str, Any]],
    query: str,
    top_k: int = BM25_DEFAULT_TOP_K,
    min_score: float = BM25_MIN_SCORE_THRESHOLD,
) -> list[BM25SearchResult]:
    """Search issues using BM25Plus algorithm."""
    if not issues or not query:
        return []

    corpus = [tokenize_text(_build_searchable_text(issue)) for issue in issues]
    non_empty_indices = [i for i, doc in enumerate(corpus) if doc]
    if not non_empty_indices:
        return []

    filtered_corpus = [corpus[i] for i in non_empty_indices]
    filtered_issues = [issues[i] for i in non_empty_indices]

    parsed = parse_boolean_query(query)
    query_tokens = parsed["required"] + parsed["optional"]
    if not query_tokens:
        return []

    bm25 = BM25Plus(filtered_corpus)
    scores = _apply_boolean_filters(list(bm25.get_scores(query_tokens)), filtered_corpus, parsed)

    scored_issues = sorted(
        [
            (filtered_issues[i], scores[i])
            for i in range(len(filtered_issues))
            if scores[i] > min_score
        ],
        key=lambda x: x[1],
        reverse=True,
    )

    return [_format_result(issue, score) for issue, score in scored_issues[:top_k]]


def try_bm25_search(
    issues: list[dict[str, Any]],
    query: str,
    auto_accept_matches: bool,
    top_k: int = BM25_DEFAULT_TOP_K,
) -> tuple[dict[str, Any] | None, list[BM25SearchResult] | None]:
    """Try to find an issue by BM25 search.

    Auto-accepts when auto_accept_matches=True AND:
    - Only one result found, OR
    - Best score is significantly higher than second best (85%+ gap)

    Returns:
        Tuple of (matched_issue, suggestions).
    """
    results = search_issues_bm25(issues, query, top_k=top_k)

    if not results:
        return None, None

    best = results[0]

    if auto_accept_matches:
        should_accept = len(results) == 1
        if not should_accept and len(results) > 1:
            second = results[1]
            gap = (best["score"] - second["score"]) / best["score"] if best["score"] > 0 else 0
            should_accept = gap >= BM25_AUTO_ACCEPT_THRESHOLD

        if should_accept:
            matched = next((i for i in issues if i.get("id") == best["issue_id"]), None)
            return matched, None

    return None, results
