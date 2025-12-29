"""Models for the Schedule API endpoint."""

from datetime import datetime

from pydantic import BaseModel

from .base import League, Teams


class ScheduleEvent(BaseModel):
    """A scheduled sporting event."""

    id: str
    teams: Teams
    date: datetime
    live: bool


class ScheduleResponse(BaseModel):
    """Response from the Schedule API endpoint."""

    updated: datetime
    league: League
    events: list[ScheduleEvent] = []
