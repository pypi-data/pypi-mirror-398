"""Pytest configuration and fixtures for gurufocus-api tests."""

import pytest


@pytest.fixture
def api_token() -> str:
    """Provide a test API token."""
    return "test-api-token-12345"


@pytest.fixture
def base_url() -> str:
    """Provide a test base URL."""
    return "https://api.gurufocus.com/public/user"
