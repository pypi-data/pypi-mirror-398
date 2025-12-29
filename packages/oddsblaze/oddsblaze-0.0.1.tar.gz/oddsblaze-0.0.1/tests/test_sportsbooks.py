"""Tests for get_sportsbooks endpoint."""

from oddsblaze import OddsblazeClient
from oddsblaze.models import Sportsbook


def test_get_sportsbooks_returns_list(client: OddsblazeClient) -> None:
    """Should return a list of Sportsbook objects."""
    sportsbooks = client.get_sportsbooks()

    assert isinstance(sportsbooks, list)
    assert len(sportsbooks) > 0
    assert all(isinstance(sb, Sportsbook) for sb in sportsbooks)


def test_get_sportsbooks_has_required_fields(client: OddsblazeClient) -> None:
    """Each sportsbook should have id, name, and sgp."""
    sportsbooks = client.get_sportsbooks()

    for sb in sportsbooks:
        assert sb.id is not None
        assert sb.name is not None
        assert sb.sgp is not None


def test_get_sportsbooks_contains_known_sportsbooks(client: OddsblazeClient) -> None:
    """Should contain well-known sportsbooks."""
    sportsbooks = client.get_sportsbooks()
    sportsbook_ids = {sb.id for sb in sportsbooks}

    known_sportsbooks = {"draftkings", "fanduel", "betmgm", "caesars"}
    found = known_sportsbooks & sportsbook_ids

    assert len(found) > 0, f"Expected at least one of {known_sportsbooks}"
