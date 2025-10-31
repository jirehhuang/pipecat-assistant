"""Utility functions for custom processors."""

import re


def compile_phrase_patterns(phrases: list[str]) -> list[re.Pattern]:
    """Compile regex patterns for phrase matching.

    Creates word-boundary-aware patterns that match phrases with flexible
    whitespace between words, case-insensitively.

    Parameters
    ----------
    phrases
        List of phrases to compile into regex patterns.

    Returns
    -------
    list[re.Pattern]
        Compiled regex patterns for each phrase.
    """
    patterns = []
    for phrase in phrases:
        # Build pattern that matches phrase with flexible whitespace
        words = phrase.split()
        escaped_words = [re.escape(word) for word in words]
        pattern_str = r"\b" + r"\s*".join(escaped_words) + r"\b"
        pattern = re.compile(pattern_str, re.IGNORECASE)
        patterns.append(pattern)
    return patterns
