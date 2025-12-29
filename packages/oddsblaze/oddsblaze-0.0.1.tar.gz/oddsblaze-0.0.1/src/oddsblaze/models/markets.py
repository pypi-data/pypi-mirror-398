"""Models for the Active Markets API endpoint."""

from datetime import datetime

from pydantic import BaseModel


class Market(BaseModel):
    """An active market."""

    id: str
    name: str
    sportsbooks: list[str] = []


class LeagueMarkets(BaseModel):
    """A league with its active markets."""

    id: str
    name: str
    sport: str
    markets: list[Market] = []


class ActiveMarketsResponse(BaseModel):
    """Response from the Active Markets API endpoint."""

    updated: datetime
    leagues: list[LeagueMarkets] = []
