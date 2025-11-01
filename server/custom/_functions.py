"""Function handlers for the Pipecat assistant bot."""

from jhutils.agent import AssistantFactory
from loguru import logger
from pipecat.services.llm_service import FunctionCallParams

_factory = AssistantFactory()


async def handle_delegate_to_assistant(params: FunctionCallParams):
    """Handle delegation to the assistant."""
    try:
        instructions = params.arguments.get("instructions", "")
        result = _factory.assistant.run(instructions)
        await params.result_callback({"result": result})
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Error delegating to assistant: {e}")
        await params.result_callback({"error": str(e)})
