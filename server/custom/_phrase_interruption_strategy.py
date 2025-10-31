"""Custom interruption strategy for immediate phrase-based interruptions."""

import re

from pipecat.audio.interruptions.base_interruption_strategy import (
    BaseInterruptionStrategy,
)

from ._sleep_command_processor import SLEEP_PHRASES

INTERRUPT_PHRASES = [
    "hold on",
    "okay",
    "wait",
    *SLEEP_PHRASES,
]


class PhraseInterruptionStrategy(BaseInterruptionStrategy):
    """Interrupt immediately if specific phrases are detected."""

    def __init__(self, phrases: list[str] | None = None):
        """Initialize the phrase interruption strategy.

        Args:
            phrases: List of phrases that trigger immediate interruption.
        """
        super().__init__()
        if phrases is None:
            phrases = INTERRUPT_PHRASES

        self._phrases = phrases
        self._accumulated_text = ""

        # Compile regex patterns for each phrase
        self._patterns = []
        for phrase in self._phrases:
            # pylint: disable=duplicate-code
            pattern = re.compile(
                r"\b"
                + r"\s*".join(re.escape(word) for word in phrase.split())
                + r"\b",
                re.IGNORECASE,
            )
            self._patterns.append(pattern)

    async def append_text(self, text: str):
        """Accumulate transcribed text for analysis.

        Args:
            text: Transcribed text to add.
        """
        self._accumulated_text += f" {text}"

    async def should_interrupt(self) -> bool:
        """Check if any interrupt phrase was detected.

        Returns
        -------
        bool
            True if any interrupt phrase is found in accumulated text.
        """
        for pattern in self._patterns:
            if pattern.search(self._accumulated_text):
                return True
        return False

    async def reset(self):
        """Reset accumulated text."""
        self._accumulated_text = ""
