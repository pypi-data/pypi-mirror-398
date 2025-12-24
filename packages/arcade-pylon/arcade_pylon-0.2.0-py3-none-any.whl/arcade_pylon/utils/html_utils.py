"""HTML utilities for Pylon toolkit."""

import html
import re
from html.parser import HTMLParser


def escape_html_if_needed(body: str, as_html: bool) -> str:
    """Escape HTML if body is plain text.

    Args:
        body: The message body content.
        as_html: If True, body is already HTML; if False, escape special chars.

    Returns:
        HTML-safe string.
    """
    if not body:
        return ""

    normalized = body.replace("\r\n", "\n").replace("\r", "\n")

    if as_html and (_contains_html_tags(normalized) or _contains_html_entities(normalized)):
        return normalized

    escaped = html.escape(normalized)
    return escaped.replace("\n", "<br>")


def _contains_html_tags(text: str) -> bool:
    parser = _TagDetectingHTMLParser()
    parser.feed(text)
    return parser.seen_tag


def _contains_html_entities(text: str) -> bool:
    return bool(re.search(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]+);", text))


class _TagDetectingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.seen_tag = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.seen_tag = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.seen_tag = True

    def handle_endtag(self, tag: str) -> None:
        self.seen_tag = True
