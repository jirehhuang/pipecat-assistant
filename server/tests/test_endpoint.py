"""Test the API endpoint."""

import os

import pytest
import requests

API_KEY = os.getenv("API_KEY", "")
API_URL = (
    os.getenv(
        "API_BASE_URL", f"http://localhost:{os.getenv('API_PORT', '8000')}"
    )
    + "/query"
)


@pytest.mark.parametrize(
    "query, expected",
    [
        ("What is the capital of France?", "Paris"),
    ],
)
def test_query_endpoint(query, expected):
    """Test the /query endpoint."""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"query": query}
    response = requests.post(API_URL, json=payload, headers=headers, timeout=9)
    assert response.status_code == 200  # noqa: PLR2004
    data = response.json()
    assert "response" in data
    assert expected in data["response"]
