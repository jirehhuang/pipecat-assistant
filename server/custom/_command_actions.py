"""Action handlers for CustomFrameProcessor commands."""

# pylint: disable=unused-argument

from loguru import logger
from pipecat.frames.frames import TranscriptionFrame

from ._active_start_wake_filter import ActiveStartWakeFilter

SLEEP_PHRASES = ["go idle", "take a break", "let me think"]

MUTE_BOT_PHRASES = ["mute yourself", "be quiet"]

UNMUTE_BOT_PHRASES = ["unmute yourself", "speak out loud"]


def create_sleep_action(wake_filter: ActiveStartWakeFilter):
    """Create a sleep command action.

    Parameters
    ----------
    wake_filter
        Wake filter instance to control.

    Returns
    -------
    Callable
        Async function that handles sleep commands.
    """

    async def sleep_action(frame: TranscriptionFrame):
        """Set the wake filter to idle state."""
        logger.info(f"Executing sleep action for user: {frame.user_id}")
        wake_filter.set_participant_idle(frame.user_id)

    return sleep_action


def create_mute_bot_action(tts_gate):
    """Create a mute bot action.

    Parameters
    ----------
    tts_gate
        TTS gate processor to control TTS output.

    Returns
    -------
    Callable
        Async function that mutes the bot's TTS.
    """

    async def mute_bot_action(frame: TranscriptionFrame):
        """Disable TTS output."""
        logger.info("Executing mute bot action - disabling TTS")
        tts_gate.gate_open = False

    return mute_bot_action


def create_unmute_bot_action(tts_gate):
    """Create an unmute bot action.

    Parameters
    ----------
    tts_gate
        TTS gate processor to control TTS output.

    Returns
    -------
    Callable
        Async function that unmutes the bot's TTS.
    """

    async def unmute_bot_action(frame: TranscriptionFrame):
        """Enable TTS output."""
        logger.info("Executing unmute bot action - enabling TTS")
        tts_gate.gate_open = True

    return unmute_bot_action
