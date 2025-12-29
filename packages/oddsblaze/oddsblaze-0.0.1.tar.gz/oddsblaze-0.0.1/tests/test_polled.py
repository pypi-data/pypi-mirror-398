"""Tests for get_last_polled endpoint."""

from oddsblaze import OddsblazeClient
from oddsblaze.models import PolledResponse


def test_get_last_polled_returns_response(
    authenticated_client: OddsblazeClient,
) -> None:
    """Should return a PolledResponse object."""
    response = authenticated_client.get_last_polled()

    assert isinstance(response, PolledResponse)
    assert response.updated is not None


def test_get_last_polled_has_leagues_with_sportsbooks(
    authenticated_client: OddsblazeClient,
) -> None:
    """Response should contain leagues with sportsbook timestamps."""
    response = authenticated_client.get_last_polled()

    assert isinstance(response.leagues, list)
    if len(response.leagues) > 0:
        league = response.leagues[0]
        assert league.id is not None
        assert isinstance(league.sportsbooks, list)


def test_get_last_polled_filter_by_league(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """Should filter by league."""
    response = authenticated_client.get_last_polled(league=active_league)

    league_ids = {league.id for league in response.leagues}
    assert active_league in league_ids or len(league_ids) == 0
