"""Gate processor to control TTS audio output."""

from pipecat.frames.frames import (
    TTSAudioRawFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class TTSGateProcessor(FrameProcessor):
    """Gate processor that can block or allow TTS audio output frames.

    This processor acts as a gate for TTS audio frames. When the gate
    is closed (not open), TTS audio frames are blocked from reaching the
    transport output, effectively muting the bot while still allowing
    text to appear in the conversation display.

    Parameters
    ----------
    gate_open
        Initial state of the gate. True means frames pass through.
    """

    def __init__(self, gate_open: bool = True):
        super().__init__()
        self._gate_open = gate_open

    @property
    def gate_open(self) -> bool:
        """Getter for whether the gate is open."""
        return self._gate_open

    @gate_open.setter
    def gate_open(self, gate_open: bool):
        """Setter for the gate state."""
        self._gate_open = gate_open

    async def process_frame(self, frame, direction: FrameDirection):
        """Process frames and block TTS audio frames when gate is closed.

        Blocks TTS audio output frames when muted, but allows text frames
        to flow through so they appear in the conversation display.
        """
        await super().process_frame(frame, direction)

        # Block TTS audio frames when gate is closed
        if not self._gate_open and isinstance(frame, TTSAudioRawFrame):
            # Don't push audio frames - effectively muting the bot
            return

        # Allow all other frames (including text) to pass through
        await self.push_frame(frame, direction)
