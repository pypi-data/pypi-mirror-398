"""Tests for get_schedule endpoint."""

from oddsblaze import OddsblazeClient
from oddsblaze.models import ScheduleResponse


def test_get_schedule_returns_response(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """Should return a ScheduleResponse object."""
    response = authenticated_client.get_schedule(active_league)

    assert isinstance(response, ScheduleResponse)
    assert response.updated is not None
    assert response.league.id == active_league


def test_get_schedule_has_events(
    authenticated_client: OddsblazeClient, active_league: str
) -> None:
    """Response should contain events."""
    response = authenticated_client.get_schedule(active_league)

    assert isinstance(response.events, list)
    for event in response.events:
        assert event.id is not None
        assert event.teams.away is not None
        assert event.teams.home is not None
        assert event.date is not None
