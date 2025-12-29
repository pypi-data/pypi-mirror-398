"""Shared pytest fixtures."""

import pytest

from oddsblaze import OddsblazeClient
from oddsblaze.settings import OddsblazeSettings


@pytest.fixture
def client() -> OddsblazeClient:
    """Create a client with default settings (uses env/file config)."""
    return OddsblazeClient()


@pytest.fixture
def authenticated_client() -> OddsblazeClient:
    """Create a client that requires valid API key from env/file config.

    Tests using this fixture will be skipped if no API key is configured
    or if the key is invalid/expired.
    """
    from oddsblaze import AuthenticationError

    client = OddsblazeClient()
    if not client.settings.api_key:
        pytest.skip("ODDSBLAZE_API_KEY not configured")

    # Validate the key works by making a simple authenticated request
    try:
        client.get_schedule("nfl")
    except AuthenticationError:
        pytest.skip("ODDSBLAZE_API_KEY is invalid or expired")

    return client


@pytest.fixture
def unauthenticated_client() -> OddsblazeClient:
    """Create a client with no API key for testing auth errors."""
    # Use model_construct to bypass env file loading and validation
    settings = OddsblazeSettings.model_construct(
        api_key=None,
        price_format=OddsblazeSettings.model_fields["price_format"].default,
    )
    return OddsblazeClient(settings=settings)


@pytest.fixture
def active_league(client: OddsblazeClient) -> str:
    """Get a league that currently has active markets.

    This ensures tests work year-round regardless of which sports are in season.
    """
    response = client.get_active_markets()

    if not response.leagues:
        pytest.skip("No active leagues available")

    # Return the first league with active markets
    return response.leagues[0].id
