"""Processor to handle sleep commands to set wake filter state to IDLE."""

import re

from loguru import logger
from pipecat.frames.frames import (
    TranscriptionFrame,
)
from pipecat.processors.filters.wake_check_filter import WakeCheckFilter
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

SLEEP_PHRASES = ["stop", "sleep", "pause", "give me a moment"]


class SleepCommandProcessor(FrameProcessor):
    """Detect sleep commands and resets the wake filter to idle."""

    def __init__(
        self,
        wake_filter: WakeCheckFilter,
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
                    # Ensure participant state exists in the wake filter
                    # pylint: disable=protected-access
                    participant_state = (
                        self._wake_filter._participant_states.get(
                            frame.user_id
                        )
                    )
                    if not participant_state:
                        # Create the participant state if it doesn't exist
                        participant_state = WakeCheckFilter.ParticipantState(
                            frame.user_id
                        )
                        self._wake_filter._participant_states[
                            frame.user_id
                        ] = participant_state

                    # Reset to IDLE state
                    participant_state.state = WakeCheckFilter.WakeState.IDLE
                    participant_state.wake_timer = 0.0
                    participant_state.accumulator = ""

                    logger.info(
                        "Wake filter state set to IDLE for user "
                        f"{frame.user_id}"
                    )
                    # Don't pass this frame through to prevent LLM response
                    return

        await self.push_frame(frame, direction)
