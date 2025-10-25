"""Alexa skill backend and utility functions."""

# pylint: disable=wrong-import-order, unused-import
import lambda_function.suppress_warnings  # isort:skip  # noqa: F401

import logging
import random

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
)
from ask_sdk_core.handler_input import HandlerInput  # noqa: F401
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model import IntentRequest, Response  # noqa: F401

from .responder import echo

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


SPEAK_OUTPUT = {
    "launch": [
        "How can I help?",
    ],
    "help": [
        "Say anything!",
    ],
    "cancel": [
        "Goodbye!",
    ],
    "catch": [
        "Sorry, I had trouble doing what you asked. Please try again.",
    ],
}

API_OUTPUT = {
    "invalid_body": [
        "Invalid body.",
    ],
    "no_query": [
        "No query provided.",
    ],
}

TEXT_OUTPUT = {
    "speak": SPEAK_OUTPUT,
    "api": API_OUTPUT,
}


def _text_output(group: str, key: str):
    """Return a random text response from the specified group and key."""
    text_choices = TEXT_OUTPUT.get(group, {}).get(
        key, "Invalid text group or key."
    )
    return random.choice(text_choices)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = _text_output(group="speak", key="launch")

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


class GeneralIntentHandler(AbstractRequestHandler):
    """Handler for General Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GeneralIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            request = handler_input.request_envelope.request

            speak_output = None
            if (
                isinstance(request, IntentRequest)
                and request.intent is not None
                and isinstance(request.intent.slots, dict)
                and "query" in request.intent.slots
            ):
                query = request.intent.slots["query"].value
                if isinstance(query, str):
                    speak_output = echo(text=query)
            if not speak_output:
                raise ValueError("No valid query provided.")

        # pylint: disable=broad-exception-caught
        except Exception as e:  # pragma: no cover
            speak_output = f"Error in GeneralIntentHandler.handle(): {e!s}"

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = _text_output(group="speak", key="help")

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(
            handler_input
        ) or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = _text_output(group="speak", key="cancel")

        return handler_input.response_builder.speak(speak_output).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = _text_output(group="speak", key="catch")

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GeneralIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

alexa_handler = sb.lambda_handler()
