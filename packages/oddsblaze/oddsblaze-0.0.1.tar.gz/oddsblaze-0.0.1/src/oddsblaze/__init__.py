"""OddsBlaze Python SDK."""

from importlib.metadata import version

from .client import OddsblazeClient
from .exceptions import (
    AuthenticationError,
    EventNotFoundError,
    InvalidMarketError,
    OddsblazeError,
    PlayerNotFoundError,
)
from .settings import OddsblazeSettings, PriceFormat, get_settings

__version__ = version("oddsblaze")

__all__ = [
    # Client
    "OddsblazeClient",
    # Settings
    "OddsblazeSettings",
    "PriceFormat",
    "get_settings",
    # Exceptions
    "OddsblazeError",
    "AuthenticationError",
    "InvalidMarketError",
    "EventNotFoundError",
    "PlayerNotFoundError",
]
