"""Pipecat assistant bot implementation."""

# pylint: disable=unused-argument

import os

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.interruptions.min_words_interruption_strategy import (
    MinWordsInterruptionStrategy,
)
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import (
    LocalSmartTurnAnalyzerV3,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import (
    LLMRunFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
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

from custom import (
    ActiveStartWakeFilter,
    PhraseInterruptionStrategy,
)
from custom._command_actions import (
    MUTE_BOT_PHRASES,
    SLEEP_PHRASES,
    UNMUTE_BOT_PHRASES,
    create_mute_bot_action,
    create_sleep_action,
    create_unmute_bot_action,
)
from custom._custom_frame_processor import (
    CommandAction,
    CustomFrameProcessor,
    MatchType,
)
from custom._functions import (
    delegate_to_shopping_list_manager_function,
    delegate_to_task_manager_function,
    handle_delegate_to_shopping_list_manager,
    handle_delegate_to_task_manager,
)
from custom._tts_gate_processor import TTSGateProcessor

load_dotenv(override=True)


# We store functions so objects (e.g. SileroVADAnalyzer) don't get
# instantiated. The function will be called when the desired transport gets
# selected.
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        turn_analyzer=LocalSmartTurnAnalyzerV3(),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        turn_analyzer=LocalSmartTurnAnalyzerV3(),
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

    # Register function handlers
    llm.register_function(
        "delegate_to_task_manager", handle_delegate_to_task_manager
    )
    llm.register_function(
        "delegate_to_shopping_list_manager",
        handle_delegate_to_shopping_list_manager,
    )

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    wake_filter = ActiveStartWakeFilter()

    # Gate to control TTS output (for mute/unmute) - start muted
    tts_gate = TTSGateProcessor(gate_open=False)

    # Create command actions
    sleep_action = CommandAction(
        phrases=SLEEP_PHRASES,
        action=create_sleep_action(wake_filter),
        match_type=MatchType.CONTAINS,
        name="sleep",
    )

    mute_bot_action = CommandAction(
        phrases=MUTE_BOT_PHRASES,
        action=create_mute_bot_action(tts_gate),
        match_type=MatchType.CONTAINS,
        name="mute",
    )

    unmute_bot_action = CommandAction(
        phrases=UNMUTE_BOT_PHRASES,
        action=create_unmute_bot_action(tts_gate),
        match_type=MatchType.CONTAINS,
        name="unmute",
    )

    # Custom frame processor with all command actions
    command_processor = CustomFrameProcessor(
        actions=[sleep_action, mute_bot_action, unmute_bot_action],
        block_on_match=True,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful and efficient assistant. "
                "Respond as concisely and completely as possible. "
                "Your output will be converted to audio, so do not include "
                "any special characters or formatting."
            ),
        },
    ]

    # Create tools schema with both delegation functions
    tools = ToolsSchema(
        standard_tools=[
            delegate_to_task_manager_function,
            delegate_to_shopping_list_manager_function,
        ]
    )

    context = OpenAILLMContext(messages, tools=tools)  # type: ignore
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            wake_filter,
            command_processor,
            context_aggregator.user(),
            llm,
            tts,
            tts_gate,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            allow_interruptions=True,
            interruption_strategies=[
                PhraseInterruptionStrategy(),
                MinWordsInterruptionStrategy(min_words=3),
            ],
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
    # pylint: disable="ungrouped-imports"
    from pipecat.runner.run import main

    main()
