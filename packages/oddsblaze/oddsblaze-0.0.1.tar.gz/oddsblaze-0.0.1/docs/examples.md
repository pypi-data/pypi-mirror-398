# Examples

## Get Odds

### Basic Usage

```python
from oddsblaze import OddsblazeClient

client = OddsblazeClient()

# Get all NFL odds from DraftKings
odds = client.get_odds("draftkings", "nfl")

print(f"Updated: {odds.updated}")
print(f"League: {odds.league.name}")
print(f"Sportsbook: {odds.sportsbook.name}")

for event in odds.events:
    print(f"\n{event.teams.away.name} @ {event.teams.home.name}")
    print(f"  Date: {event.date}")
    print(f"  Live: {event.live}")
```

### Filter by Market

```python
# Single market
odds = client.get_odds("draftkings", "nfl", market="moneyline")

# Multiple markets
odds = client.get_odds("draftkings", "nfl", market=["moneyline", "point-spread"])

# Markets containing a string
odds = client.get_odds("draftkings", "nfl", market_contains="Player")
```

### Filter by Event Type

```python
# Only live events
odds = client.get_odds("draftkings", "nfl", live=True)

# Only pre-match events
odds = client.get_odds("draftkings", "nfl", live=False)

# Only main lines (no alternates)
odds = client.get_odds("draftkings", "nfl", main=True)
```

---

## Get Consensus Odds

```python
# Get consensus point spreads for NFL
consensus = client.get_consensus("nfl", "point-spread")

for event in consensus.events:
    print(f"\n{event.teams.away.name} @ {event.teams.home.name}")
    for odd in event.odds:
        print(f"  {odd.name}: {odd.price}")
        print(f"    Sportsbooks: {len(odd.sportsbooks)}")
        for sb in odd.sportsbooks:
            print(f"      {sb.name}: {sb.price}")
```

### Custom Weights

```python
# Weight Circa higher
consensus = client.get_consensus(
    "nfl",
    "point-spread",
    sportsbooks=["draftkings", "circa", "caesars"],
    weights={"circa": 1.5, "draftkings": 1.0}
)
```

---

## Get Schedule

```python
# Get NFL schedule
schedule = client.get_schedule("nfl")

for event in schedule.events:
    print(f"{event.teams.away.name} @ {event.teams.home.name} - {event.date}")
```

### Filter by Date

```python
# Single date
schedule = client.get_schedule("nfl", date="2025-01-05")

# Date range
schedule = client.get_schedule("nfl", date="2025-01-01-2025-01-31")
```

### Filter by Team

```python
schedule = client.get_schedule("nfl", team="Kansas City Chiefs")
# or by abbreviation
schedule = client.get_schedule("nfl", team="KC")
```

---

## Grade a Bet

```python
# Get the odds ID from a previous odds call
odds_id = "DraftKings#543e2c71-dd0a-53b6-b6a8-07395ca23ed0#Moneyline#Green Bay Packers"

result = client.grade_bet(odds_id)

print(f"Result: {result.result}")  # Win, Lose, or Push
print(f"Event: {result.event.teams.away.name} @ {result.event.teams.home.name}")
print(f"Status: {result.event.status}")
```

### Grade Live Bet

```python
result = client.grade_bet(odds_id, live=True)
```

---

## Get Historical Odds

```python
# Get CLV and OLV
historical = client.get_historical(odds_id)

print(f"OLV (Opening): {historical.olv.price}")
print(f"CLV (Closing): {historical.clv.price}")
```

### With Line Movement

```python
historical = client.get_historical(odds_id, time_series=True)

for entry in historical.entries:
    if entry.locked:
        print(f"  LOCKED at {entry.timestamp}")
    else:
        print(f"  {entry.price} at {entry.timestamp}")
```

---

## Metadata Endpoints

### Get Leagues

```python
leagues = client.get_leagues()

for league in leagues:
    print(f"{league.name} ({league.sport})")
```

### Get Sportsbooks

```python
sportsbooks = client.get_sportsbooks()

for sb in sportsbooks:
    print(f"{sb.name} - SGP: {sb.sgp}")
```

### Get Active Markets

```python
markets = client.get_active_markets()

for league in markets.leagues:
    print(f"\n{league.name}:")
    for market in league.markets:
        print(f"  {market.name}: {len(market.sportsbooks)} sportsbooks")
```

### Get Last Polled

```python
polled = client.get_last_polled(league=["nfl", "nba"])

for league in polled.leagues:
    print(f"\n{league.name}:")
    for sb in league.sportsbooks:
        print(f"  {sb.name}: {sb.last}s ago")
```
