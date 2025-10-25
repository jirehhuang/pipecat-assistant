"""Lambda function handler module."""

import json
from typing import Any

from .alexa import _text_output, alexa_handler
from .responder import echo
from .utils import _make_response


def lambda_handler(event: Any, context: Any) -> Any:
    """Lambda handler."""
    try:
        # Check for Alexa request session
        if "session" in event:
            return alexa_handler(event, context)

        arn = str(getattr(context, "invoked_function_arn", ""))

        # Get body and convert str to dict if necessary
        body = event.get("body", event)
        if isinstance(body, str):
            try:
                body = json.loads(body)  # Convert if body is given as str
            except json.JSONDecodeError:
                body = None
        if not isinstance(body, dict):
            return _make_response(
                data={"fail": _text_output(group="api", key="invalid_body")},
                status="fail",
                arn=arn,
            )

        # Check for existing query in body
        query = body.get("query", "")
        if not query:
            return _make_response(
                data={"fail": _text_output(group="api", key="no_query")},
                status="fail",
                arn=arn,
            )

        result = {
            "text": echo(text=query),
        }
        return _make_response(
            data=result,
            status="success",
            arn=arn,
        )

    # pylint: disable=broad-exception-caught
    except Exception as e:  # pragma: no cover
        return _make_response(
            status="error",
            data={"error": "Error in lambda_handler(): " + str(e)},
            arn=arn,
        )
