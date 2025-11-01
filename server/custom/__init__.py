"""Custom server functionality for Pipecat Assistant."""

from ._active_start_wake_filter import ActiveStartWakeFilter
from ._bot_audio_control_processor import (
    create_set_bot_audio_mute_handler,
    set_bot_audio_mute_function,
)
from ._command_actions import (
    create_mute_bot_action,
    create_sleep_action,
    create_unmute_bot_action,
)
from ._custom_frame_processor import (
    CommandAction,
    CustomFrameProcessor,
    MatchType,
)
from ._phrase_interruption_strategy import PhraseInterruptionStrategy
from ._tts_gate_processor import TTSGateProcessor
