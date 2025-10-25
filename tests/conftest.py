"""Configure API URL and key for E2E tests."""

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv


def pytest_addoption(parser):
    """Add command line option(s) for pytest."""
    parser.addoption(
        "--url",
        action="store",
        default=None,
        help="Base API URL required for E2E tests.",
    )


@pytest.fixture(name="api_env", scope="session")
def fixture_api_env(pytestconfig):
    """Return detected API environment."""
    url = pytestconfig.getoption("--url")
    return url if url in ["latest", "staging", "prod"] else None


@pytest.fixture(name="api_url", scope="session")
def fixture_api_url(api_env, pytestconfig):
    """Return retrieved API URL, from alias if applicable."""
    url = pytestconfig.getoption("--url")

    env_file = Path(__file__).resolve().parents[1] / ".env"
    if api_env and env_file.exists():
        load_dotenv(env_file)
        if api_env in ["latest"]:
            url = os.getenv("LATEST_API_URL")
        if api_env in ["staging"]:
            url = os.getenv("STAGING_API_URL")
        if api_env in ["prod"]:
            url = os.getenv("PROD_API_URL")

    return url


class SecretStr(str):
    """Ensure a sensitive str is not exposed in logs."""

    def __repr__(self):
        """Redact string representation."""
        return "<redacted>"

    def __str__(self):
        """Redact string representation."""
        return "<redacted>"


@pytest.fixture(name="api_key", scope="session")
def fixture_api_key(api_url):
    """Return retrieved API key based on API URL, redacted for test output."""
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    if not api_url:
        return None

    parsed = urlparse(api_url)
    key = None
    if parsed.path.endswith("/staging") or parsed.path.endswith("/latest"):
        key = os.getenv("STAGING_API_KEY")
    elif parsed.path.endswith("/prod"):
        key = os.getenv("PROD_API_KEY")
    if key is not None:
        return SecretStr(key)
    return key


def pytest_collection_modifyitems(config, items):
    """Skip all e2e tests if --url not provided."""
    url = config.getoption("--url")
    if not url:
        skip_e2e = pytest.mark.skip(
            reason="No --url provided; skipping E2E tests"
        )
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
