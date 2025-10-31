"""Processor to handle sleep commands to set wake filter state to IDLE."""

import re

from loguru import logger
from pipecat.frames.frames import (
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from ._active_start_wake_filter import ActiveStartWakeFilter

SLEEP_PHRASES = ["stop", "sleep", "pause", "give me a moment"]


class SleepCommandProcessor(FrameProcessor):
    """Detect sleep commands and resets the wake filter to idle."""

    def __init__(
        self,
        wake_filter: ActiveStartWakeFilter,
        sleep_phrases: list[str] | None = None,
    ):
        """Initialize the sleep command processor.

        Args:
            wake_filter: Wake filter instance to control.
            sleep_phrases: List of phrases that trigger sleep mode.
        """
        super().__init__()
        if sleep_phrases is None:
            sleep_phrases = SLEEP_PHRASES

        self._wake_filter = wake_filter
        self._sleep_phrases = sleep_phrases

        # Compile regex patterns for sleep phrases
        self._sleep_patterns = []
        for phrase in self._sleep_phrases:
            # pylint: disable=duplicate-code
            pattern = re.compile(
                r"\b"
                + r"\s*".join(re.escape(word) for word in phrase.split())
                + r"\b",
                re.IGNORECASE,
            )
            self._sleep_patterns.append(pattern)

    async def process_frame(self, frame, direction: FrameDirection):
        """Process frames and check for sleep commands."""
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            # Check if the transcription contains a sleep phrase
            for pattern in self._sleep_patterns:
                if pattern.search(frame.text):
                    logger.info(
                        f"Sleep command detected: '{frame.text}' - going idle"
                    )
                    # Set participant to IDLE state using public method
                    self._wake_filter.set_participant_idle(frame.user_id)
                    # Don't pass this frame through to prevent LLM response
                    return

        await self.push_frame(frame, direction)
