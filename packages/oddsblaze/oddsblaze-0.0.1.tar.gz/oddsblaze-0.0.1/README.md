# oddsblaze-python

Python SDK for the [OddsBlaze API](https://oddsblaze.com/). 

## Installation

```bash
uv add oddsblaze
```

Or with pip:

```bash
pip install oddsblaze
```

## Quick Start

1. Get an API key at [oddsblaze.com](https://www.oddsblaze.com/)

2. Set your API key:

```bash
# Option 1: Environment variable
export ODDSBLAZE_API_KEY=your_key

# Option 2: .env file in project root
echo "ODDSBLAZE_API_KEY=your_key" >> .env

# Option 3: Global config file
echo "ODDSBLAZE_API_KEY=your_key" >> ~/.oddsblaze
```

3. Start using the SDK:

```python
from oddsblaze import OddsblazeClient

client = OddsblazeClient()

# Get NFL odds from DraftKings
odds = client.get_odds("draftkings", "nfl")
for event in odds.events:
    print(f"{event.teams.away.name} @ {event.teams.home.name}")
```

## Documentation

Full documentation at [reecetec.github.io/oddsblaze-python](https://reecetec.github.io/oddsblaze-python/)