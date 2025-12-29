"""Models for the Grader API endpoint."""

from typing import Literal, Optional

from pydantic import BaseModel

from .base import Selection


class GradedTeam(BaseModel):
    """A team with score in a graded event."""

    name: str
    score: int


class GradedTeams(BaseModel):
    """Away and home teams with scores."""

    away: GradedTeam
    home: GradedTeam


class GradedEvent(BaseModel):
    """Event information for bet grading."""

    id: str
    teams: GradedTeams
    status: str


class GradedPlayer(BaseModel):
    """Player information for bet grading."""

    id: str
    score: Optional[int] = None


class GraderResponse(BaseModel):
    """Response from the Grader API endpoint."""

    id: str
    event: GradedEvent
    market: str
    name: str
    selection: Optional[Selection] = None
    player: Optional[GradedPlayer] = None
    result: Literal["Win", "Lose", "Push"]
