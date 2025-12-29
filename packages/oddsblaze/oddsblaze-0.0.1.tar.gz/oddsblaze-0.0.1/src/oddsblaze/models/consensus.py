"""Models for the Consensus Odds API endpoint."""

from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator

from .base import League, Player, Selection, Sportsbook, Teams


def _ms_to_datetime(v: int | datetime) -> datetime:
    """Convert millisecond timestamp to UTC datetime."""
    if isinstance(v, datetime):
        return v
    return datetime.fromtimestamp(v / 1000, tz=timezone.utc)


TimestampMs = Annotated[datetime, BeforeValidator(_ms_to_datetime)]


class SportsbookPrice(BaseModel):
    """A sportsbook's price for consensus odds."""

    name: str
    price: str
    timestamp: TimestampMs


class ConsensusOdd(BaseModel):
    """Individual consensus odds line with sportsbook breakdown."""

    id: str
    market: str
    name: str
    price: str
    selection: Optional[Selection] = None
    player: Optional[Player] = None
    sportsbooks: list[SportsbookPrice] = []


class ConsensusEvent(BaseModel):
    """A sporting event with consensus odds."""

    id: str
    teams: Teams
    date: datetime
    live: bool
    odds: list[ConsensusOdd] = []


class ConsensusResponse(BaseModel):
    """Response from the Consensus Odds API endpoint."""

    updated: datetime
    league: League
    sportsbook: Sportsbook
    events: list[ConsensusEvent] = []
