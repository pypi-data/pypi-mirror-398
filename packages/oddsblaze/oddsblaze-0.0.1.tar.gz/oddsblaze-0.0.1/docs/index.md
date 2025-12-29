# oddsblaze-python

Python SDK for the [OddsBlaze API](https://docs.oddsblaze.com/).

## Features

- **Pydantic models** for validated, typed API responses
- **Automatic timestamp conversion** - millisecond epochs become Python datetimes with timezone
- **Custom exceptions** for API errors (invalid market, event not found, etc.)
- **Flexible configuration** via env vars, `.env`, or `~/.oddsblaze`

## Quick Start

```bash
uv add oddsblaze
```

```python
from oddsblaze import OddsblazeClient

client = OddsblazeClient()

# Get NFL odds from DraftKings
odds = client.get_odds("draftkings", "nfl")
for event in odds.events:
    print(f"{event.teams.away.name} @ {event.teams.home.name}")
```

See [Getting Started](getting-started.md) for setup and configuration.