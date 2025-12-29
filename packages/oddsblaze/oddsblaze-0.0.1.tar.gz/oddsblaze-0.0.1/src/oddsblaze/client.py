"""OddsBlaze API client."""

from typing import Any, Optional

import httpx

from .exceptions import AuthenticationError, raise_for_error_message
from .models import (
    ActiveMarketsResponse,
    ConsensusResponse,
    GraderResponse,
    HistoricalResponse,
    League,
    OddsResponse,
    PolledResponse,
    ScheduleResponse,
    Sportsbook,
)
from .settings import OddsblazeSettings, PriceFormat, get_settings


class OddsblazeClient:
    """Synchronous client for the OddsBlaze API."""

    BASE_URL = "https://api.oddsblaze.com/v2"
    ODDS_URL = "https://odds.oddsblaze.com"
    HISTORICAL_URL = "https://historical.oddsblaze.com"
    GRADER_URL = "https://grader.oddsblaze.com"
    POLLED_URL = "https://polled.oddsblaze.com"

    def __init__(
        self,
        settings: Optional[OddsblazeSettings] = None,
        timeout: float = 30.0,
    ):
        self.settings = settings or get_settings()
        self._client = httpx.Client(timeout=timeout)

    def _require_api_key(self) -> str:
        """Get API key or raise AuthenticationError."""
        if self.settings.api_key:
            return self.settings.api_key
        raise AuthenticationError(
            "ODDSBLAZE_API_KEY is required; set it in env, .env, or ~/.oddsblaze"
        )

    def _get_price_format(self, price: Optional[PriceFormat] = None) -> str:
        """Get price format, defaulting to settings."""
        fmt = price or self.settings.price_format
        return fmt.value if isinstance(fmt, PriceFormat) else fmt

    def _build_params(self, require_auth: bool = True, **kwargs: Any) -> dict[str, str]:
        """Build query parameters, handling auth and filtering None values."""
        params: dict[str, str] = {}

        if require_auth:
            params["key"] = self._require_api_key()
        elif self.settings.api_key:
            params["key"] = self.settings.api_key

        for key, value in kwargs.items():
            if value is None:
                continue
            if isinstance(value, bool):
                params[key] = "true" if value else "false"
            elif isinstance(value, list):
                params[key] = ",".join(str(v) for v in value)
            elif isinstance(value, PriceFormat):
                params[key] = value.value
            else:
                params[key] = str(value)

        return params

    def _request(self, url: str, params: dict[str, str]) -> Any:
        """Make GET request and handle errors."""
        response = self._client.get(url, params=params)

        # Handle 401 as AuthenticationError
        if response.status_code == 401:
            raise AuthenticationError(
                "Invalid or expired API key. Get a new key at oddsblaze.com"
            )

        response.raise_for_status()
        data = response.json()

        # Check for API error messages
        if isinstance(data, dict) and "message" in data and len(data) == 1:
            raise_for_error_message(data["message"])

        return data

    # -------------------------------------------------------------------------
    # Odds API
    # -------------------------------------------------------------------------
    def get_odds(
        self,
        sportsbook: str,
        league: str,
        *,
        market: Optional[str | list[str]] = None,
        market_contains: Optional[str | list[str]] = None,
        price: Optional[PriceFormat] = None,
        event: Optional[str | list[str]] = None,
        main: Optional[bool] = None,
        live: Optional[bool] = None,
    ) -> OddsResponse:
        """
        Get real-time odds for a sportsbook and league.

        Args:
            sportsbook: Sportsbook ID (e.g., "draftkings")
            league: League ID (e.g., "nfl")
            market: Market ID(s) or name(s) to filter
            market_contains: Filter markets containing these strings
            price: Price format (defaults to settings)
            event: Event ID(s) to filter
            main: True for main lines only, False for alternates only
            live: True for live events only, False for pre-match only
        """
        params = self._build_params(
            require_auth=True,
            sportsbook=sportsbook,
            league=league,
            market=market,
            market_contains=market_contains,
            price=price or self.settings.price_format,
            event=event,
            main=main,
            live=live,
        )
        data = self._request(self.ODDS_URL, params)
        return OddsResponse.model_validate(data)

    # -------------------------------------------------------------------------
    # Historical Odds API
    # -------------------------------------------------------------------------
    def get_historical(
        self,
        odds_id: str,
        *,
        price: Optional[PriceFormat] = None,
        time_series: bool = False,
        locked: bool = False,
    ) -> HistoricalResponse:
        """
        Get historical odds with CLV, OLV, and line movement.

        Args:
            odds_id: The odds ID from a previous odds response
            price: Price format (defaults to settings)
            time_series: Include line movement history
            locked: Include locked odds in time series
        """
        params = self._build_params(
            require_auth=True,
            id=odds_id,
            price=price or self.settings.price_format,
        )
        if time_series:
            params["time_series"] = ""
        if locked:
            params["locked"] = ""

        data = self._request(self.HISTORICAL_URL, params)
        return HistoricalResponse.model_validate(data)

    # -------------------------------------------------------------------------
    # Consensus Odds API
    # -------------------------------------------------------------------------
    def get_consensus(
        self,
        league: str,
        market: str,
        *,
        price: Optional[PriceFormat] = None,
        dedupe: Optional[bool] = None,
        sportsbooks: Optional[list[str]] = None,
        required_sportsbooks: Optional[list[str]] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> ConsensusResponse:
        """
        Get consensus odds across sportsbooks.

        Args:
            league: League ID (e.g., "nfl")
            market: Market ID (e.g., "point-spread")
            price: Price format (defaults to settings)
            dedupe: Remove duplicate prices (default True)
            sportsbooks: Sportsbooks to include (at least one must have odds)
            required_sportsbooks: Sportsbooks that must all be present
            weights: Custom weights by sportsbook ID (e.g., {"draftkings": 1.5})
        """
        params = self._build_params(
            require_auth=True,
            price=price or self.settings.price_format,
            dedupe=dedupe,
            sportsbooks=sportsbooks,
        )

        if required_sportsbooks:
            params["required-sportsbooks"] = ",".join(required_sportsbooks)

        if weights:
            for book_id, weight in weights.items():
                params[f"weight-{book_id}"] = str(weight)

        url = f"{self.BASE_URL}/consensus/{league}/{market}.json"
        data = self._request(url, params)
        return ConsensusResponse.model_validate(data)

    # -------------------------------------------------------------------------
    # Grader API
    # -------------------------------------------------------------------------
    def grade_bet(
        self,
        odds_id: str,
        *,
        live: bool = False,
    ) -> GraderResponse:
        """
        Grade a bet (Win, Lose, or Push).

        Args:
            odds_id: The odds ID to grade
            live: Grade while event is still in progress
        """
        params = self._build_params(require_auth=True, id=odds_id)
        if live:
            params["live"] = ""

        data = self._request(self.GRADER_URL, params)
        return GraderResponse.model_validate(data)

    # -------------------------------------------------------------------------
    # Schedule API
    # -------------------------------------------------------------------------
    def get_schedule(
        self,
        league: str,
        *,
        event_id: Optional[str | list[str]] = None,
        team: Optional[str | list[str]] = None,
        date: Optional[str | list[str]] = None,
        live: Optional[bool] = None,
    ) -> ScheduleResponse:
        """
        Get upcoming and live events.

        Args:
            league: League ID (e.g., "nfl")
            event_id: Event ID(s) to filter
            team: Team ID(s), name(s), or abbreviation(s) to filter
            date: Date(s) in YYYY-MM-DD format, or range YYYY-MM-DD-YYYY-MM-DD
            live: True for live only, False for pre-match only
        """
        params = self._build_params(
            require_auth=True,
            id=event_id,
            team=team,
            date=date,
            live=live,
        )
        url = f"{self.BASE_URL}/schedule/{league}.json"
        data = self._request(url, params)
        return ScheduleResponse.model_validate(data)

    # -------------------------------------------------------------------------
    # Leagues API (no auth required)
    # -------------------------------------------------------------------------
    def get_leagues(self) -> list[League]:
        """Get all available leagues."""
        params = self._build_params(require_auth=False)
        url = f"{self.BASE_URL}/leagues.json"
        data = self._request(url, params)
        return [League.model_validate(item) for item in data]

    # -------------------------------------------------------------------------
    # Sportsbooks API (no auth required)
    # -------------------------------------------------------------------------
    def get_sportsbooks(self) -> list[Sportsbook]:
        """Get all available sportsbooks."""
        params = self._build_params(require_auth=False)
        url = f"{self.BASE_URL}/sportsbooks.json"
        data = self._request(url, params)
        return [Sportsbook.model_validate(item) for item in data]

    # -------------------------------------------------------------------------
    # Active Markets API (no auth required)
    # -------------------------------------------------------------------------
    def get_active_markets(self) -> ActiveMarketsResponse:
        """Get active markets across all leagues."""
        params = self._build_params(require_auth=False)
        url = f"{self.BASE_URL}/markets/active.json"
        data = self._request(url, params)
        return ActiveMarketsResponse.model_validate(data)

    # -------------------------------------------------------------------------
    # Last Polled API
    # -------------------------------------------------------------------------
    def get_last_polled(
        self,
        *,
        league: Optional[str | list[str]] = None,
        sportsbook: Optional[str | list[str]] = None,
        group: bool = False,
    ) -> PolledResponse:
        """
        Get last polled timestamps for odds.

        Args:
            league: League ID(s) to filter
            sportsbook: Sportsbook ID(s) to filter
            group: Group results by sportsbook
        """
        params = self._build_params(
            require_auth=True,
            league=league,
            sportsbook=sportsbook,
        )
        if group:
            params["group"] = ""

        data = self._request(self.POLLED_URL, params)
        return PolledResponse.model_validate(data)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "OddsblazeClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
