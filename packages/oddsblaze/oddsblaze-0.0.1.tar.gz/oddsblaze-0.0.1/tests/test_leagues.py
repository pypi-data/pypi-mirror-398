"""Tests for get_leagues endpoint."""

from oddsblaze import OddsblazeClient
from oddsblaze.models import League


def test_get_leagues_returns_list(client: OddsblazeClient) -> None:
    """Should return a list of League objects."""
    leagues = client.get_leagues()

    assert isinstance(leagues, list)
    assert len(leagues) > 0
    assert all(isinstance(league, League) for league in leagues)


def test_get_leagues_has_required_fields(client: OddsblazeClient) -> None:
    """Each league should have id, name, and sport."""
    leagues = client.get_leagues()

    for league in leagues:
        assert league.id is not None
        assert league.name is not None
        assert league.sport is not None


def test_get_leagues_contains_known_leagues(client: OddsblazeClient) -> None:
    """Should contain well-known leagues like NFL, NBA, MLB."""
    leagues = client.get_leagues()
    league_ids = {league.id for league in leagues}

    known_leagues = {"nfl", "nba", "mlb", "nhl"}
    found = known_leagues & league_ids

    assert len(found) > 0, f"Expected at least one of {known_leagues}"
