# Getting Started

## Installation

Install oddsblaze using uv:

```bash
uv add oddsblaze
```

Or with pip:

```bash
pip install oddsblaze
```

## Configuration

You need an API key from [oddsblaze.com](https://www.oddsblaze.com/).

=== "Environment Variable"

    ```bash
    export ODDSBLAZE_API_KEY=your_key
    export ODDSBLAZE_PRICE_FORMAT=decimal  # optional
    ```

=== ".env File"

    Create a `.env` file in your project root:

    ```
    ODDSBLAZE_API_KEY=your_key
    ODDSBLAZE_PRICE_FORMAT=decimal
    ```

=== "Global Config (~/.oddsblaze)"

    ```
    ODDSBLAZE_API_KEY=your_key
    ODDSBLAZE_PRICE_FORMAT=decimal
    ```

**Price formats:** `american` (default), `decimal`, `fractional`, `probability`, `malaysian`, `indonesian`, `hong_kong`

You can also override price format per-request:

```python
from oddsblaze import OddsblazeClient, PriceFormat

client = OddsblazeClient()
odds = client.get_odds("draftkings", "nfl", price=PriceFormat.DECIMAL)
```

## Basic Usage

```python
from oddsblaze import OddsblazeClient

client = OddsblazeClient()

# Get NFL odds from DraftKings
odds = client.get_odds("draftkings", "nfl")

for event in odds.events:
    print(f"{event.teams.away.name} @ {event.teams.home.name}")
    for odd in event.odds:
        print(f"  {odd.name}: {odd.price}")
```

## Error Handling

The SDK raises specific exceptions for API errors:

```python
from oddsblaze import (
    OddsblazeClient,
    OddsblazeError,
    AuthenticationError,
    InvalidMarketError,
    EventNotFoundError,
    PlayerNotFoundError,
)

client = OddsblazeClient()

try:
    result = client.grade_bet("invalid-id")
except EventNotFoundError:
    print("Event not found")
except OddsblazeError as e:
    print(f"API error: {e.message}")
```
