"""Function handlers for bot audio control."""

from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams

# Define function schema for muting bot audio
set_bot_audio_mute_function = FunctionSchema(
    name="set_bot_audio_mute",
    description="Control whether the bot's audio output is muted or unmuted.",
    properties={
        "muted": {
            "type": "boolean",
            "description": "True to mute the bot's audio, False to unmute it.",
        },
    },
    required=["muted"],
)


def create_set_bot_audio_mute_handler(tts_gate):
    """Create a handler for controlling bot audio mute state.

    Parameters
    ----------
    tts_gate
        The TTSGateProcessor instance to control.

    Returns
    -------
    Callable
        Async function that handles bot audio mute/unmute.
    """

    async def handle_set_bot_audio_mute(params: FunctionCallParams):
        """Handle bot audio mute/unmute function call."""
        try:
            muted = params.arguments.get("muted", False)
            tts_gate.gate_open = not muted

            status = "muted" if muted else "unmuted"
            logger.info(f"Bot audio {status} via function call")

            await params.result_callback(
                {
                    "success": True,
                    "muted": muted,
                    "message": f"Bot audio {status}",
                }
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error setting bot audio mute: {e}")
            await params.result_callback({"error": str(e)})

    return handle_set_bot_audio_mute
