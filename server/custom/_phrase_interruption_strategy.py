"""Custom interruption strategy for immediate phrase-based interruptions."""

from pipecat.audio.interruptions.base_interruption_strategy import (
    BaseInterruptionStrategy,
)

from ._command_actions import SLEEP_PHRASES
from ._utils import compile_phrase_patterns

INTERRUPT_PHRASES = [
    "hold on",
    "okay",
    "wait",
    *SLEEP_PHRASES,
]


class PhraseInterruptionStrategy(BaseInterruptionStrategy):
    """Interrupt immediately if specific phrases are detected.

    Parameters
    ----------
    phrases
        List of phrases that trigger immediate interruption.
    """

    def __init__(self, phrases: list[str] | None = None):
        super().__init__()
        if phrases is None:
            phrases = INTERRUPT_PHRASES

        self._phrases = phrases
        self._accumulated_text = ""
        self._patterns = compile_phrase_patterns(self._phrases)

    async def append_text(self, text: str):
        """Accumulate transcribed text for analysis.

        Parameters
        ----------
        text
            Transcribed text to add.
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
