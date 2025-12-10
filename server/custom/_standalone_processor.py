"""Standalone query processor for direct API access."""

import asyncio

from loguru import logger

from custom._assistant_llm import make_assistant_llm


class StandaloneQueryProcessor:  # pylint: disable=too-few-public-methods
    """Process queries independently without transport layer."""

    def __init__(self):
        """Initialize the standalone processor with LLM components."""
        self.assistant_llm = make_assistant_llm()

    async def process_query(self, query: str) -> str:
        """Process a single query and return the response.

        Parameters
        ----------
        query
            The user query to process.

        Returns
        -------
            The assistant's response as a string.
        """
        logger.info(f"Processing standalone query: {query}")

        # Use the assistant directly for synchronous processing
        try:
            response = await asyncio.to_thread(
                self.assistant_llm.assistant.run,
                query=query,
            )
            logger.info(f"Generated response: {response}")
            return response
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_msg = f"Error processing query: {e!s}"
            logger.error(error_msg)
            return error_msg


# pylint: disable=too-few-public-methods
class StandaloneQueryProcessorFactory:
    """Factory class for initializing and retrieving the processor."""

    def __init__(self):
        """Initialize the factory."""
        self._standalone_processor: StandaloneQueryProcessor | None = None

    @property
    def standalone_processor(self) -> StandaloneQueryProcessor:
        """Get or create the standalone processor instance."""
        if self._standalone_processor is None:
            self._standalone_processor = StandaloneQueryProcessor()
        return self._standalone_processor


_standalone_processor_factory = StandaloneQueryProcessorFactory()
