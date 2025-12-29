"""Models for the Last Polled API endpoint."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _ms_to_datetime(v: int | datetime) -> datetime:
    """Convert millisecond timestamp to UTC datetime."""
    if isinstance(v, datetime):
        return v
    return datetime.fromtimestamp(v / 1000, tz=timezone.utc)


TimestampMs = Annotated[datetime, BeforeValidator(_ms_to_datetime)]


class PolledSportsbook(BaseModel):
    """A sportsbook's last polled status."""

    id: str
    name: str
    timestamp: TimestampMs
    last: int  # Seconds since last poll


class PolledLeague(BaseModel):
    """A league with polled sportsbooks."""

    id: str
    name: str
    sportsbooks: list[PolledSportsbook] = []


class PolledResponse(BaseModel):
    """Response from the Last Polled API endpoint."""

    updated: datetime
    leagues: list[PolledLeague] = []
