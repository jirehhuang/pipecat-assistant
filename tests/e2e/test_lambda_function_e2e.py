"""Test Lambda function end-to-end (E2E) via API."""

import pytest
import requests

from lambda_function.alexa import _text_output


def query2response(api_url: str, api_key: str, query: str) -> dict:
    """Retrieve API response based on query."""
    headers = {"x-api-key": api_key}
    body = {"query": query}
    response = requests.post(api_url, headers=headers, json=body, timeout=10)
    return response.json()


@pytest.mark.parametrize("query", [None, [], ""])
def test_no_query(api_url, api_key, query):
    """Test that if an invalid body is provided, the API response correctly
    returns a fail message."""
    response = query2response(api_url, api_key, query)
    assert "status" in response
    assert response["status"] == "fail" and "fail" in response["data"]
    assert (
        _text_output(group="api", key="no_query") in response["data"]["fail"]
    )


@pytest.mark.parametrize("query, expected", [("query", "query")])
def test_query(api_url, api_key, query, expected):
    """Test that if an invalid body is provided, the API response correctly
    returns a fail message."""
    response = query2response(api_url, api_key, query)
    assert "status" in response
    assert response["status"] == "success"
    assert response["data"]["text"] == expected
