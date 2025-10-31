"""Pipecat assistant bot implementation."""

# pylint: disable=unused-argument

import os
import re

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    LLMRunFrame,
    TranscriptionFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.filters.wake_check_filter import WakeCheckFilter
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import (
    RTVIConfig,
    RTVIObserver,
    RTVIProcessor,
)
from pipecat.runner.run import main
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openrouter.llm import OpenRouterLLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

from custom import ActiveStartWakeFilter

load_dotenv(override=True)

SLEEP_PHRASES = ["stop", "sleep", "pause", "give me a moment"]


class SleepCommandProcessor(FrameProcessor):
    """Detect sleep commands and resets the wake filter to idle."""

    def __init__(self, wake_filter: WakeCheckFilter, sleep_phrases=None):
        """Initialize the sleep command processor.

        Args:
            wake_filter: Wake filter instance to control.
            sleep_phrases: List of phrases that trigger sleep mode.
        """
        super().__init__()
        self._wake_filter = wake_filter
        self._sleep_phrases = sleep_phrases or SLEEP_PHRASES
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


# We store functions so objects (e.g. SileroVADAnalyzer) don't get
# instantiated. The function will be called when the desired transport gets
# selected.
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
}


# pylint: disable=too-many-locals
async def create_bot_pipeline(
    session: aiohttp.ClientSession,
    transport: BaseTransport,
    runner_args: RunnerArguments,
):
    """Create and configure the bot pipeline with all necessary components."""
    logger.info("Starting bot")

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY", ""))

    tts = PiperTTSService(
        base_url=os.getenv("PIPER_BASE_URL", ""),
        aiohttp_session=session,
        sample_rate=24000,
    )

    llm = OpenRouterLLMService(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="openai/gpt-4o-mini",
    )

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    wake_filter = ActiveStartWakeFilter()

    # Resets wake filter to idle when commanded
    sleep_processor = SleepCommandProcessor(wake_filter)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Your output will be converted "
                "to audio so don't include special characters in your "
                "answers. Respond to what the user said in a creative and "
                "helpful way.",
            ),
        },
    ]

    context = OpenAILLMContext(messages)  # type: ignore
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            wake_filter,
            sleep_processor,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Kick off the conversation.
        messages.append(
            {
                "role": "system",
                "content": "Please introduce yourself to the user.",
            }
        )
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Run the bot with an HTTP session wrapper."""
    async with aiohttp.ClientSession() as session:
        await create_bot_pipeline(session, transport, runner_args)


async def bot(runner_args: RunnerArguments):
    """Run main bot entry point compatible with Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    main()
