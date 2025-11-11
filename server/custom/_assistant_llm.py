"""Function handlers for the Pipecat assistant bot."""

import asyncio
import os
from typing import Callable

from jhutils.agent import AssistantAgent, AssistantFactory
from jhutils.agent.tools._tools import AVAILABLE_MODES
from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAIContextAggregatorPair
from pipecat.services.openrouter.llm import OpenRouterLLMService

assistant_factory = AssistantFactory()

EXCLUDE_TOOLS: set[str] = {"RespondTool"}


class AssistantLLM:
    """Class for integrating the assistant with the LLM."""

    def __init__(self, assistant_agent: AssistantAgent):
        self._assistant = assistant_agent
        self._initialize_llm()

    @property
    def assistant(self) -> AssistantAgent:
        """Get the assistant agent."""
        return self._assistant

    @property
    def llm(self) -> OpenRouterLLMService:
        """Get the LLM service."""
        return self._llm

    @property
    def context(self) -> OpenAILLMContext:
        """Get the LLM context."""
        return self._context

    @property
    def context_aggregator(self) -> OpenAIContextAggregatorPair:
        """Get the LLM context aggregator."""
        return self._context_aggregator

    def _initialize_llm(self):
        """Initialize the LLM along with context and context aggregator."""
        # pylint: disable=attribute-defined-outside-init
        self._llm = OpenRouterLLMService(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )
        self._context = OpenAILLMContext(messages=[], tools=[])
        self._context_aggregator = self._llm.create_context_aggregator(
            self._context
        )
        self._functions: dict[str, FunctionSchema] = {}
        self._handlers: dict[str, Callable] = {}
        self._update_llm_config()

    def change_mode(self, mode: str):
        """Change the assistant mode and update the LLM configuration."""
        # .match_mode() fuzzy matches and updates the mode to the matched mode
        matched_mode = self.assistant.toolset.match_mode(query=mode)
        if matched_mode is None:
            msg = f"Could not find mode: {mode}"
            logger.warning(msg)
            return msg

        logger.info(f"Changing assistant mode to: {matched_mode}")
        self._update_llm_config()
        return f"Changed to mode: '{matched_mode}'"

    def _update_llm_config(self):
        """Update the existing LLM instance configuration.

        This method updates the system prompt and tools in the existing context
        without creating new processor instances.
        """
        self._unregister_tools()
        self._register_tools_as_functions()
        self._register_change_mode()
        self._update_context()

    def _update_context(self):
        """Update messages and tools in context object.

        The context instance must be updated in place in order for updates to
        be reflected in the executing pipeline. This method resets the messages
        to the system prompt and adds the available tools for the current mode.
        """
        messages = [
            {
                "role": "system",
                "content": self.assistant.toolset.system_prompt,
            },
        ]
        # Add most recent user query in case there are applicable instructions
        if len(self._context.messages) > 1:
            last_message = self._context.messages[-1]
            if last_message["role"] == "user":
                messages.append(last_message)  # type: ignore

        self._context.set_messages(messages)  # type: ignore

        standard_tools = list(self._functions.values())
        tools = self._llm.adapter_class().from_standard_tools(
            tools=ToolsSchema(standard_tools=standard_tools)  # type: ignore
        )
        self._context.set_tools(tools)

        logger.info(
            f"Reset messages and added {len(standard_tools)} tools to context"
        )

    def _unregister_tools(self):
        """Unregister tools currently registered as functions from the LLM."""
        logger.info("Unregistering tools")

        for function_name in list(self._handlers.keys()):
            if function_name == "change_mode":
                continue
            try:
                self._llm.unregister_function(function_name)
            except Exception as e:  # pylint: disable=broad-exception-caught
                if self._llm.has_function(function_name):
                    logger.warning(
                        f"Failed to unregister function {function_name}: {e}"
                    )
            if not self._llm.has_function(function_name):
                logger.info(f"Unregistered function: {function_name}")

        self._functions.clear()
        self._handlers.clear()
        logger.info("Unregistered tools and cleared internal state")

    def _register_change_mode(self):
        """Register the change_mode function with the LLM."""
        tool_name = "change_mode"
        available_modes = ", ".join(
            repr(key) for key, _ in AVAILABLE_MODES.items()
        )
        self._functions[tool_name] = FunctionSchema(
            name="change_mode",
            description=("Change the assistant's mode to the specified mode."),
            properties={
                "mode": {
                    "type": "string",
                    "description": (
                        f"The mode to change to. One of: {available_modes}"
                    ),
                },
            },
            required=["mode"],
        )

        async def handle_change_mode(params: FunctionCallParams):
            mode = params.arguments.get("mode", "")
            result = self.change_mode(mode)
            await params.result_callback({"result": result})

        self._handlers[tool_name] = handle_change_mode
        self._llm.register_function(tool_name, self._handlers[tool_name])

    async def _handle_tool_execution(
        self, params: FunctionCallParams, tool_name: str
    ):
        """Handle execution of any tool by delegating to the assistant."""
        try:
            instructions = params.arguments.get("instructions", "")
            result = await asyncio.to_thread(self.assistant.run, instructions)
            await params.result_callback({"result": result})
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error executing {tool_name}: {e}")
            await params.result_callback({"error": str(e)})

    def _create_tool_handler(self, tool_name: str) -> Callable:
        """Create a tool handler for the given tool name."""

        async def handle_tool_execution_(params: FunctionCallParams):
            await self._handle_tool_execution(params, tool_name)

        handle_tool_execution_.__name__ = tool_name
        handle_tool_execution_.__doc__ = f"Handle execution of {tool_name}."

        return handle_tool_execution_

    def _register_tools_as_functions(self):
        """Register available tools in the assistant toolset as LLM functions.

        The FunctionSchema for each tool is provided via ToolsSchema to inform
        the LLM what functions are available. The actual function handlers are
        registered to enable the LLM to execute them.
        """
        for tool_name in self.assistant.toolset.available_tool_names:
            if tool_name in EXCLUDE_TOOLS:
                continue

            function_schema_data = self.assistant.toolset.get_function_schema(
                tool_name
            )
            self._functions[tool_name] = FunctionSchema(
                **function_schema_data  # type: ignore
            )

            self._handlers[tool_name] = self._create_tool_handler(tool_name)
            self._llm.register_function(tool_name, self._handlers[tool_name])


def make_assistant_llm() -> AssistantLLM:
    """Create an AssistantLLM instance."""
    return AssistantLLM(assistant_agent=assistant_factory.assistant)
