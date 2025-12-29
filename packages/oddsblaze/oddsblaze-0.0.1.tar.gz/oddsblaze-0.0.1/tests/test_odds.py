"""Tests for get_odds endpoint."""

from oddsblaze import OddsblazeClient
from oddsblaze.models import OddsResponse


def test_get_odds_returns_response(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """Should return an OddsResponse object."""
    response = authenticated_client.get_odds("draftkings", active_league)

    assert isinstance(response, OddsResponse)
    assert response.updated is not None
    assert response.league.id == active_league
    assert response.sportsbook.id == "draftkings"


def test_get_odds_has_events_with_teams(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """Events should have teams and dates."""
    response = authenticated_client.get_odds("draftkings", active_league)

    assert isinstance(response.events, list)
    for event in response.events:
        assert event.id is not None
        assert event.teams.away is not None
        assert event.teams.home is not None
        assert event.date is not None
        assert isinstance(event.live, bool)


def test_get_odds_filter_by_market(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """Should filter odds by market."""
    response = authenticated_client.get_odds(
        "draftkings", active_league, market="moneyline"
    )

    assert isinstance(response, OddsResponse)
    for event in response.events:
        for odd in event.odds:
            assert "moneyline" in odd.market.lower()


def test_get_odds_filter_live_only(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """live=True should only return live events."""
    response = authenticated_client.get_odds("draftkings", active_league, live=True)

    for event in response.events:
        assert event.live is True


def test_get_odds_filter_prematch_only(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """live=False should only return pre-match events."""
    response = authenticated_client.get_odds("draftkings", active_league, live=False)

    for event in response.events:
        assert event.live is False
