"""Custom wake filter that starts in AWAKE state."""

import time

from loguru import logger
from pipecat.frames.frames import TranscriptionFrame
from pipecat.processors.filters.wake_check_filter import WakeCheckFilter
from pipecat.processors.frame_processor import FrameProcessor

WAKE_PHRASES = ["pipecat", "pipe cat", "wake up", "listen up", "I'm back"]


class ActiveStartWakeFilter(WakeCheckFilter):
    """Wake filter that starts in AWAKE state instead of IDLE.

    Overrides the default WakeCheckFilter to have new participants start
    in the AWAKE state, allowing immediate response without needing to hear
    a wake phrase first.

    Additionally, by default, the keepalive timeout is set to infinity,
    meaning once awake, the filter remains awake indefinitely until a sleep
    command is received.
    """

    def __init__(
        self,
        wake_phrases: list[str] | None = None,
        keepalive_timeout: float = float("inf"),
    ):
        """Initialize with wake phrases and keepalive timeout.

        Parameters
        ----------
        wake_phrases
            Phrases that will wake the filter.
        keepalive_timeout
            Time in seconds to stay awake without hearing a wake phrase.
        """
        if wake_phrases is None or wake_phrases == []:
            wake_phrases = WAKE_PHRASES

        super().__init__(wake_phrases, keepalive_timeout)
        self._start_awake = True

    async def process_frame(self, frame, direction):
        """Process frames, starting in AWAKE state for new participants."""
        await FrameProcessor.process_frame(self, frame, direction)

        try:
            if isinstance(frame, TranscriptionFrame):
                p = self._participant_states.get(frame.user_id)
                if p is None:
                    p = WakeCheckFilter.ParticipantState(frame.user_id)
                    # Start in AWAKE state
                    if self._start_awake:
                        p.state = WakeCheckFilter.WakeState.AWAKE
                        p.wake_timer = float("inf")  # Stay awake indefinitely
                    self._participant_states[frame.user_id] = p

                # If AWAKE, pass frames through and reset timeout
                if p.state == WakeCheckFilter.WakeState.AWAKE:
                    if p.wake_timer == float("inf") or (
                        self._keepalive_timeout > 0
                        and self._get_time() - p.wake_timer
                        < self._keepalive_timeout
                    ):
                        logger.info(f"Wake filter is awake. Pushing {frame}")
                        if p.wake_timer != float("inf"):
                            p.wake_timer = self._get_time()
                        await self.push_frame(frame)
                        return
                    p.state = WakeCheckFilter.WakeState.IDLE

                # Check for wake phrase
                p.accumulator += frame.text
                for pattern in self._wake_patterns:
                    match = pattern.search(p.accumulator)
                    if match:
                        logger.info(f"Wake phrase triggered: {match.group()}")
                        p.state = WakeCheckFilter.WakeState.AWAKE
                        p.wake_timer = self._get_time()
                        match_start = match.start()
                        frame.text = p.accumulator[match_start:]
                        p.accumulator = ""
                        await self.push_frame(frame)
                        return
                # If IDLE and no wake phrase found, don't pass frame through
                logger.info(
                    "Wake filter is IDLE - "
                    f"dropping transcription: {frame.text}"
                )
                return
            # Pass through non-transcription frames
            await self.push_frame(frame, direction)
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_msg = f"Error in wake filter: {e}"
            logger.exception(error_msg)

    def _get_time(self):
        """Get current time for wake timer tracking."""
        return time.time()
