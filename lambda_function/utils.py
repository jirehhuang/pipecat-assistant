"""Utility functions for the Lambda function."""

import json
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid6


# pylint: disable=too-many-arguments, too-many-positional-arguments
def _make_response(
    data: dict,
    status: str = "success",
    arn: str = "",
) -> dict[str, Any]:
    """
    Assemble an API response in OpenAI/OpenRouter style.

    Parameters
    ----------
    data
        The payload data to include.
    status
        The status of the response, one of "success", "fail", or "error".
    arn
        The Lambda function ARN, from which to parse the identified execution
        environment.

    Returns
    -------
    dict
        A full response dict (not JSON serialized).
    """
    # Map status -> HTTP code
    status_map = {
        "success": 200,  # OK
        "fail": 400,  # Bad Request
        "error": 500,  # Internal Server Error
    }
    if status not in status_map:
        raise ValueError(f"Invalid status: {status}")

    # Detect invoked environment from ARN
    env = arn if arn is None else arn.split(":")[-1]
    env = (
        env
        if env in {"staging", "prod"}
        else (
            "local"
            if env is None
            else "version" if env.isdigit() else "latest"
        )
    )

    # https://github.com/omniti-labs/jsend
    response = {
        "data": data,
        "status": status,
        "env": env,
        "id": str(uuid6()),
        "created": datetime.now(UTC).isoformat(),
    }

    # Ensure response is JSON-serializable
    try:
        json.dumps(response)
    except (TypeError, ValueError) as e:
        raise ValueError("Response is not JSON serializable") from e

    return response
