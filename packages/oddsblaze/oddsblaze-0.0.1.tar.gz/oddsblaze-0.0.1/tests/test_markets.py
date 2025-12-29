"""Tests for get_active_markets endpoint."""

from oddsblaze import OddsblazeClient
from oddsblaze.models import ActiveMarketsResponse


def test_get_active_markets_returns_response(client: OddsblazeClient) -> None:
    """Should return an ActiveMarketsResponse object."""
    response = client.get_active_markets()

    assert isinstance(response, ActiveMarketsResponse)
    assert response.updated is not None


def test_get_active_markets_has_leagues_with_markets(client: OddsblazeClient) -> None:
    """Response should contain leagues with markets."""
    response = client.get_active_markets()

    assert isinstance(response.leagues, list)
    if len(response.leagues) > 0:
        league = response.leagues[0]
        assert league.id is not None
        assert league.name is not None
        assert league.sport is not None
        assert isinstance(league.markets, list)


def test_get_active_markets_markets_have_sportsbooks(client: OddsblazeClient) -> None:
    """Each market should list supporting sportsbooks."""
    response = client.get_active_markets()

    for league in response.leagues:
        for market in league.markets:
            assert market.id is not None
            assert market.name is not None
            assert isinstance(market.sportsbooks, list)
