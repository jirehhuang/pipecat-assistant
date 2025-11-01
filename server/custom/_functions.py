"""Function handlers for the Pipecat assistant bot."""

from jhutils.agent import AssistantFactory
from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams

_factory = AssistantFactory()


# Define function schema for task manager delegation
delegate_to_task_manager_function = FunctionSchema(
    name="delegate_to_task_manager",
    description=(
        "Delegate task-related instructions to the task manager to add to the "
        "tasks list."
    ),
    properties={
        "instructions": {
            "type": "string",
            "description": (
                "Clear instructions adding tasks, with all relevant details. "
                "For example: "
                "'Add tasks to: 1) buy groceries and 2) get an oil change for "
                "the Prius'."
            ),
        },
    },
    required=["instructions"],
)


# Define function schema for shopping list manager delegation
delegate_to_shopping_list_manager_function = FunctionSchema(
    name="delegate_to_shopping_list_manager",
    description=(
        "Delegate shopping-related instructions to the shopping list manager"
        "to add shopping items to the shopping list."
    ),
    properties={
        "instructions": {
            "type": "string",
            "description": (
                "Clear instructions to add shopping items, with all relevant "
                "details. For example: "
                "'Add milk and eggs from Costco and canned chipotles from "
                "Walmart'."
            ),
        },
    },
    required=["instructions"],
)


async def handle_delegate_to_task_manager(params: FunctionCallParams):
    """Handle delegation to the task manager."""
    try:
        instructions = params.arguments.get("instructions", "")
        result = _factory.assistant.run(instructions)
        await params.result_callback({"result": result})
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Error delegating to task manager: {e}")
        await params.result_callback({"error": str(e)})


async def handle_delegate_to_shopping_list_manager(params: FunctionCallParams):
    """Handle delegation to the shopping list manager."""
    try:
        instructions = params.arguments.get("instructions", "")
        result = _factory.assistant.run(instructions)
        await params.result_callback({"result": result})
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Error delegating to shopping list manager: {e}")
        await params.result_callback({"error": str(e)})
