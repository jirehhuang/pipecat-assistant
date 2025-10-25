"""Test functions in utils.py."""

import json

import pytest

from lambda_function.utils import _make_response


def test_invalid_status():
    """Test that invalid status raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid status: invalid"):
        _make_response(data={}, status="invalid")


def test_make_response_json_serializable():
    """Test that the output of `_make_response` is JSON serializable."""
    test_text = "This is test text"
    response = _make_response(data={"text": test_text})
    response_json = json.dumps(response)
    assert isinstance(response_json, str)

    response_dict = json.loads(response_json)
    assert isinstance(response_dict, dict)
    assert response_dict["data"]["text"] == test_text


def test_make_response_not_json_serializable():
    """Test that `_make_response` correctly throws an error if the provided
    data is not json serializable."""
    with pytest.raises(ValueError, match="Response is not JSON serializable"):
        _make_response(
            data={"text": {"A set is not JSON serializable"}},
        )
