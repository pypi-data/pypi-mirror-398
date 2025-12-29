"""Models for the Historical Odds API endpoint."""

from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator

from .base import Selection


def _ms_to_datetime(v: int | datetime) -> datetime:
    """Convert millisecond timestamp to UTC datetime."""
    if isinstance(v, datetime):
        return v
    return datetime.fromtimestamp(v / 1000, tz=timezone.utc)


# Type alias for millisecond timestamps that become datetimes
TimestampMs = Annotated[datetime, BeforeValidator(_ms_to_datetime)]


class PricePoint(BaseModel):
    """A price at a specific timestamp (CLV/OLV)."""

    price: str
    timestamp: TimestampMs


class TimeSeriesEntry(BaseModel):
    """An entry in the line movement history."""

    price: Optional[str] = None
    locked: bool
    timestamp: TimestampMs


class HistoricalResponse(BaseModel):
    """Response from the Historical Odds API endpoint."""

    updated: datetime
    id: str
    market: str
    name: str
    selection: Optional[Selection] = None
    olv: Optional[PricePoint] = None
    clv: Optional[PricePoint] = None
    entries: list[TimeSeriesEntry] = []
