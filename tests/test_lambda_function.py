"""Test Lambda function handler module (non-Alexa)."""

import pytest

from lambda_function import lambda_handler
from lambda_function.alexa import _text_output


def test_no_query():
    """Test that if no query is provided, the lambda_handler correctly returns
    a fail message."""
    response = lambda_handler({}, None)
    assert response["status"] == "fail" and "fail" in response["data"]
    assert (
        _text_output(group="api", key="no_query") in response["data"]["fail"]
    )


@pytest.mark.parametrize("body", [None, [], "str"])
def test_invalid_body(body):
    """Test that if an invalid body is provided, the lambda_handler correctly
    returns a fail message."""
    response = lambda_handler({"body": body}, None)
    assert response["status"] == "fail" and "fail" in response["data"]
    assert (
        _text_output(group="api", key="invalid_body")
        in response["data"]["fail"]
    )


def test_success_text():
    """Test that if a valid body with query is provided, the lambda_handler
    correctly returns a success message."""
    query = "Hello, world!"
    response = lambda_handler({"body": {"query": query}}, None)
    assert response["status"] == "success"
    assert response["data"]["text"] == query
