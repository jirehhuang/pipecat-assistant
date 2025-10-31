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
        pattern = re.compile(
            r"\b"
            + r"\s*".join(re.escape(word) for word in phrase.split())
            + r"\b",
            re.IGNORECASE,
        )
        patterns.append(pattern)
    return patterns
