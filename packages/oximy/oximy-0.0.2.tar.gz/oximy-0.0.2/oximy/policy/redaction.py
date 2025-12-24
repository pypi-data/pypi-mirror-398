"""
Policy Redaction

Handles content redaction with position tracking.
"""

from typing import Any


class RedactionMatch:
    """A single redaction match with position and replacement."""

    def __init__(self, start: int, end: int, replacement: str, source: str):
        self.start = start
        self.end = end
        self.replacement = replacement
        self.source = source


def apply_redactions(content: str, matches: list[RedactionMatch]) -> str:
    """Applies multiple redactions to content, handling overlapping matches."""
    if not matches:
        return content

    # Sort matches by start position (descending) to apply from end to start
    # This prevents position shifts when applying redactions
    sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)

    result = content
    for match in sorted_matches:
        # Ensure we don't go out of bounds
        start = max(0, min(match.start, len(result)))
        end = max(start, min(match.end, len(result)))

        if start < end:
            result = result[:start] + match.replacement + result[end:]

    return result
