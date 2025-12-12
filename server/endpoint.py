"""Minimal API endpoint for Pipecat assistant bot pipeline."""

import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from loguru import logger
from pipecat.frames.frames import (
    LLMMessagesUpdateFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantAggregatorParams,
)
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pydantic import BaseModel

from custom import make_assistant_llm

load_dotenv(override=True)

API_KEY = os.getenv("API_KEY")
API_RESPONSE_TIMEOUT = float(os.getenv("API_RESPONSE_TIMEOUT", "30.0"))
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "20"))


# Global pipeline state
class PipelineState:
    """Manages the persistent pipeline instance."""

    def __init__(self):
        """Initialize pipeline state."""
        self.assistant_llm = None
        self.pipeline = None
        self.task = None
        self.runner = None
        self.task_handle = None
        self.response_queue = asyncio.Queue()

    async def start(self) -> None:
        """Start the persistent pipeline."""
        logger.info("Starting persistent pipeline")

        self.assistant_llm = make_assistant_llm(
            context_aggregator_params={
                "assistant_params": LLMAssistantAggregatorParams(
                    expect_stripped_words=False
                )
            }
        )

        processors = [
            self.assistant_llm.context_aggregator.user(),
            self.assistant_llm.llm,
            self.assistant_llm.context_aggregator.assistant(),
        ]

        self.pipeline = Pipeline(processors)
        self.task = PipelineTask(
            self.pipeline,
            params=PipelineParams(
                enable_metrics=False,
                enable_usage_metrics=False,
            ),
            idle_timeout_secs=None,
        )

        self.runner = PipelineRunner()
        self.task_handle = asyncio.create_task(self.runner.run(self.task))

        logger.info("Persistent pipeline started")

    async def stop(self) -> None:
        """Stop the persistent pipeline."""
        logger.info("Stopping persistent pipeline")
        if self.task:
            await self.task.cancel()
        if self.task_handle:
            try:
                await asyncio.wait_for(self.task_handle, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Pipeline shutdown timed out")
        logger.info("Persistent pipeline stopped")

    def _trim_context(
        self, context: OpenAILLMContext, max_messages: int
    ) -> None:
        """Trim the context to ensure it does not exceed the maximum length.

        Parameters
        ----------
        context
            The assistant's context containing messages.
        max_messages
            The maximum allowed length of the context messages.
        """
        if len(context.messages) > max_messages:
            # Keep only the first message and last (max_messages - 1) messages
            keep_from = -1 * (max_messages - 1)
            context.set_messages(
                context.messages[:1] + context.messages[keep_from:]
            )

    async def _wait_for_response(
        self,
        context: OpenAILLMContext,
        timeout: float = 30.0,
        interval: float = 0.1,
    ) -> str:
        """Wait for the assistant's response within the given timeout.

        Parameters
        ----------
        context
            The assistant's context containing messages.
        timeout
            Maximum time to wait for response in seconds.

        Returns
        -------
            The assistant's response text or a timeout message.
        """
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if (
                "role" in context.messages[-1]
                and "content" in context.messages[-1]
                and context.messages[-1]["role"] == "assistant"
            ):
                return str(context.messages[-1]["content"])
            await asyncio.sleep(interval)
        logger.error("Pipeline processing timed out")
        return (
            f"Sorry, the assistant took more than {timeout} "
            "seconds to respond."
        )

    async def process_query(self, query: str, timeout: float) -> str:
        """Process a query through the pipeline.

        Parameters
        ----------
        query
            The user query to process.
        timeout
            Maximum time to wait for response in seconds.

        Returns
        -------
            The assistant's response text.
        """
        logger.info(f"Processing query: {query}")

        context = self.assistant_llm.context
        self._trim_context(context, max_messages=MAX_MESSAGES)

        context.add_message({"role": "user", "content": query})
        await self.task.queue_frame(
            LLMMessagesUpdateFrame(messages=context.messages, run_llm=True)
        )
        response = await self._wait_for_response(context, timeout=timeout)
        return response


# Initialize pipeline state
pipeline_state = PipelineState()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    await pipeline_state.start()
    yield
    # Shutdown
    await pipeline_state.stop()


app = FastAPI(lifespan=lifespan)


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify the API key from the request header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str


@app.post(
    "/query",
    dependencies=[Depends(verify_api_key)],
)
async def process_query(request: QueryRequest):
    """Process a query through the persistent pipeline.

    Parameters
    ----------
    request
        The query request containing the user's question.

    Returns
    -------
        JSON response with the assistant's answer.
    """
    try:
        response_text = await pipeline_state.process_query(
            request.query, timeout=API_RESPONSE_TIMEOUT
        )
        return {"response": response_text}
    except Exception as exc:
        logger.error(f"Error processing query: {exc}")
        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred while processing your request. "
                "Please try again later."
            ),
        ) from exc


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "5476"))
    uvicorn.run("endpoint:app", host="0.0.0.0", port=port, reload=False)
