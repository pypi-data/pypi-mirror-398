from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PriceFormat(str, Enum):
    """Supported price formats for odds display."""

    AMERICAN = "american"
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"
    PROBABILITY = "probability"
    MALAYSIAN = "malaysian"
    INDONESIAN = "indonesian"
    HONG_KONG = "hong_kong"


class OddsblazeSettings(BaseSettings):
    api_key: Optional[str] = Field(None, alias="ODDSBLAZE_API_KEY")
    price_format: PriceFormat = Field(
        PriceFormat.AMERICAN, alias="ODDSBLAZE_PRICE_FORMAT"
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=(".env", Path.home() / ".oddsblaze"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> OddsblazeSettings:
    return OddsblazeSettings()
