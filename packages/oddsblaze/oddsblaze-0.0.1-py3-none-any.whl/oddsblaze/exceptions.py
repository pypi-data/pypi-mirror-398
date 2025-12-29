"""Custom exceptions for the OddsBlaze SDK."""


class OddsblazeError(Exception):
    """Base exception for all OddsBlaze errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AuthenticationError(OddsblazeError):
    """Raised when API key is invalid or missing for an authenticated endpoint."""


class InvalidMarketError(OddsblazeError):
    """Raised when the requested market is invalid."""


class EventNotFoundError(OddsblazeError):
    """Raised when the requested event is not found."""


class PlayerNotFoundError(OddsblazeError):
    """Raised when the requested player is not found."""


# Mapping from API error messages to exception classes
ERROR_MESSAGE_MAP: dict[str, type[OddsblazeError]] = {
    "Invalid market": InvalidMarketError,
    "Event not found": EventNotFoundError,
    "Player not found": PlayerNotFoundError,
}


def raise_for_error_message(message: str) -> None:
    """Raise the appropriate exception for an API error message."""
    exception_class = ERROR_MESSAGE_MAP.get(message, OddsblazeError)
    raise exception_class(message)
