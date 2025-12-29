"""Models for the Odds API endpoint."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .base import League, Links, Player, Selection, Sportsbook, Teams


class Odd(BaseModel):
    """Individual odds line."""

    id: str
    market: str
    name: str
    price: str
    main: Optional[bool] = None
    links: Optional[Links] = None
    sgp: Optional[str] = None
    selection: Optional[Selection] = None
    player: Optional[Player] = None


class Event(BaseModel):
    """A sporting event with associated odds."""

    id: str
    teams: Teams
    date: datetime
    live: bool
    odds: list[Odd] = []


class OddsResponse(BaseModel):
    """Response from the Odds API endpoint."""

    updated: datetime
    league: League
    sportsbook: Sportsbook
    events: list[Event] = []
