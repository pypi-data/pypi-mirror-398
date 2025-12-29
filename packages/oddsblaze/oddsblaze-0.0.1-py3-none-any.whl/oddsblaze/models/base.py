"""Base Pydantic models shared across multiple endpoints."""

from typing import Optional

from pydantic import BaseModel


class League(BaseModel):
    """A sports league."""

    id: str
    name: str
    sport: str


class Sportsbook(BaseModel):
    """A sportsbook."""

    id: str
    name: str
    sgp: Optional[bool] = None


class Team(BaseModel):
    """A team."""

    id: str
    name: str
    abbreviation: Optional[str] = None


class Teams(BaseModel):
    """Away and home teams for an event."""

    away: Team
    home: Team


class Player(BaseModel):
    """A player with team information."""

    id: str
    name: str
    position: Optional[str] = None
    number: Optional[str] = None
    team: Optional[Team] = None


class Selection(BaseModel):
    """Betting selection details."""

    name: Optional[str] = None
    side: Optional[str] = None
    line: Optional[float] = None


class Links(BaseModel):
    """Deep links to sportsbook betting slip."""

    desktop: Optional[str] = None
    mobile: Optional[str] = None
