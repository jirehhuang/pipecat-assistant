"""Gate processor to control TTS audio output."""

from pipecat.frames.frames import (
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class TTSGateProcessor(FrameProcessor):
    """Processor that can block or allow TTS frames.

    This processor acts as a gate for TTS-related frames. When the gate is
    closed (not open), TTS frames are blocked from passing through the
    pipeline.

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
        """Process frames and block TTS frames when gate is closed."""
        await super().process_frame(frame, direction)

        # Block TTS frames when gate is closed
        if not self._gate_open and isinstance(
            frame, (TTSAudioRawFrame, TTSStartedFrame, TTSStoppedFrame)
        ):
            # Don't push the frame - effectively blocking it
            return

        # Allow all other frames or when gate is open
        await self.push_frame(frame, direction)
