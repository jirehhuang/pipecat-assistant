"""Test Alexa skill backend and utility functions."""

import numpy as np
import pytest

from lambda_function import lambda_handler
from lambda_function.alexa import _text_output


# pylint: disable=too-many-arguments,too-many-positional-arguments
# ruff: noqa: PLR0913, RUF013
def make_request_payload(
    request_type: str,
    new: bool = False,
    request_id: str = "amzn1.echo-api.request.1234",
    timestamp: str = "2016-10-27T18:21:44Z",
    locale: str = "en-US",
    reason: str | None = None,
    intent_name: str | None = None,
    slots: dict | None = None,
    player_activity: str | None = "IDLE",
    session_id: str = "amzn1.echo-api.session.123456789012",
    application_id: str = "amzn1.ask.skill.987654321",
    user_id: str = "amzn1.ask.account.testUser",
    attributes: dict | None = None,
) -> dict:
    """Create Alexa request payload for testing."""
    payload = {
        "version": "1.0",
        "session": {
            "new": new,
            "sessionId": session_id,
            "application": {"applicationId": application_id},
            "attributes": attributes or {},
            "user": {"userId": user_id},
        },
        "context": {
            "System": {
                "application": {"applicationId": application_id},
                "user": {"userId": user_id},
                "device": {"supportedInterfaces": {"AudioPlayer": {}}},
            },
        },
        "request": {
            "type": request_type,
            "requestId": request_id,
            "timestamp": timestamp,
            "locale": locale,
        },
    }
    if player_activity is not None and isinstance(payload["context"], dict):
        payload["context"]["AudioPlayer"] = {"playerActivity": player_activity}
    if (
        request_type == "SessionEndedRequest"
        and isinstance(payload["request"], dict)
        and reason is not None
    ):
        payload["request"]["reason"] = reason
    if (
        request_type == "IntentRequest"
        and isinstance(payload["request"], dict)
        and intent_name is not None
    ):
        payload["request"]["intent"] = {"name": intent_name, "slots": {}}
        if slots is not None:
            payload["request"]["intent"]["slots"] = slots
    return payload


def make_general_intent_payload(query):
    """Create GeneralIntent payload from query."""
    return make_request_payload(
        request_type="IntentRequest",
        intent_name="GeneralIntent",
        slots={"query": {"name": "query", "value": query}},
    )


@pytest.fixture(name="launch_intent_payload", scope="module")
def fixture_launch_intent_payload():
    """Return Alexa Start Session test event JSON."""
    return make_request_payload(
        request_type="LaunchRequest",
        new=True,
    )


@pytest.fixture(name="session_ended_payload", scope="module")
def fixture_session_ended_payload():
    """Return Alexa End Session test event JSON."""
    return make_request_payload(
        request_type="SessionEndedRequest",
        reason="USER_INITIATED",
        player_activity=None,
    )


def test_launch_intent(launch_intent_payload):
    """Test that invoking LaunchRequest returns the expected response."""
    response = lambda_handler(launch_intent_payload, None)
    assert np.any(
        _text_output(group="speak", key="launch")
        in response["response"]["outputSpeech"]["ssml"]
    )


@pytest.mark.parametrize("query", ["Example text", ""])
def test_general_intent(query):
    """Test that invoking GeneralIntent returns the expected response."""
    response = lambda_handler(make_general_intent_payload(query), None)
    assert query in response["response"]["outputSpeech"]["ssml"]


def test_help_intent():
    """Test that invoking HelpIntent returns the expected response."""
    response = lambda_handler(
        make_request_payload(
            request_type="IntentRequest",
            intent_name="AMAZON.HelpIntent",
        ),
        None,
    )
    assert np.any(
        _text_output(group="speak", key="help")
        in response["response"]["outputSpeech"]["ssml"]
    )


@pytest.mark.parametrize(
    "intent", ["AMAZON.CancelIntent", "AMAZON.StopIntent"]
)
def test_cancel_stop_intent(intent):
    """Test that invoking CancelOrStopIntent returns the expected response."""
    response = lambda_handler(
        make_request_payload(
            request_type="IntentRequest",
            intent_name=intent,
        ),
        None,
    )
    assert np.any(
        _text_output(group="speak", key="cancel")
        in response["response"]["outputSpeech"]["ssml"]
    )


def test_session_ended(session_ended_payload):
    """Test that invoking SessionEndedRequest returns the expected response."""
    response = lambda_handler(session_ended_payload, None)
    assert response["response"] == {}


def test_catch_all_exception():
    """Test that invoking HelpIntent returns the expected response."""
    response = lambda_handler(
        make_request_payload(
            request_type="IntentRequest",
            intent_name="InvalidIntent",
        ),
        None,
    )
    assert np.any(
        _text_output(group="speak", key="catch")
        in response["response"]["outputSpeech"]["ssml"]
    )
