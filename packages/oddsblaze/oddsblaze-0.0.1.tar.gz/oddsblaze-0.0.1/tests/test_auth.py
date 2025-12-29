"""Tests for authentication error handling."""

import pytest

from oddsblaze import AuthenticationError, OddsblazeClient


def test_raises_auth_error_without_key(unauthenticated_client: OddsblazeClient) -> None:
    """Should raise AuthenticationError when API key is missing."""
    with pytest.raises(AuthenticationError):
        unauthenticated_client.get_odds("draftkings", "nfl")


def test_unauthenticated_can_access_public_endpoints(
    unauthenticated_client: OddsblazeClient,
) -> None:
    """Public endpoints should work without auth."""
    leagues = unauthenticated_client.get_leagues()
    assert len(leagues) > 0

    sportsbooks = unauthenticated_client.get_sportsbooks()
    assert len(sportsbooks) > 0
