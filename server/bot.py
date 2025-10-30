"""Pipecat assistant bot implementation."""

# pylint: disable=unused-argument

import os

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    LLMRunFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.filters.wake_check_filter import WakeCheckFilter
from pipecat.processors.frameworks.rtvi import (
    RTVIConfig,
    RTVIObserver,
    RTVIProcessor,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openrouter.llm import OpenRouterLLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

load_dotenv(override=True)

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

    wake_filter = WakeCheckFilter(
        wake_phrases=["wake up"],
        keepalive_timeout=5.0,
    )

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
            transport.input(),  # Transport user input
            rtvi,
            stt,
            wake_filter,
            context_aggregator.user(),  # User responses
            llm,  # LLM
            tts,  # TTS
            transport.output(),  # Transport bot output
            context_aggregator.assistant(),  # Assistant spoken responses
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
    from pipecat.runner.run import main

    main()
