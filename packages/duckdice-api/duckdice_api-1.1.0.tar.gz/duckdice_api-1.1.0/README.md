# DuckDice API Python Wrapper

A modern, type-safe Python client for the [DuckDice Bot API](https://duckdice.io/bot-api). Place bets, manage balances, and retrieve user statistics programmatically.

## Features

- **Simple & Intuitive**: Easy-to-use API client with clear method signatures
- **Type Hints**: Full type annotations for IDE support and better code safety
- **Error Handling**: Comprehensive exception handling with `DuckDiceAPIException`
- **Well Tested**: 13 unit tests covering all methods and edge cases
- **Production Ready**: Used by DuckDice bot operators worldwide

## Installation

```bash
pip install duckdice-api
```

## Quick Start

```python
from duckdice_api import DuckDiceAPI, DuckDiceConfig

# Initialize client
cfg = DuckDiceConfig(api_key="YOUR_BOT_API_KEY")
client = DuckDiceAPI(cfg)

# Get user info
user = client.get_user_info()
print(f"Username: {user['username']}, Level: {user['level']}")

# Get currency stats
stats = client.get_currency_stats("XLM")
print(f"Bets: {stats['bets']}, Wins: {stats['wins']}")

# Place Original Dice bet
result = client.play_dice(
    symbol="XLM",
    amount="0.1",
    chance="77.77",
    is_high=True
)
print(f"Bet result: {result['bet']['result']}")

# Place Range Dice bet
result = client.play_range_dice(
    symbol="XLM",
    amount="0.1",
    range_vals=[0, 5000],
    is_in=True
)
```

## API Methods

### Read Methods

- `get_user_info()` — Retrieve bot user profile, balances, wagering bonuses, and TLE info
- `get_currency_stats(symbol)` — Get statistics for a specific currency (bets, wins, profit, volume)

### Betting Methods

- `play_dice(symbol, amount, chance, is_high, ...)` — Place Original Dice bet (high/low prediction)
- `play_range_dice(symbol, amount, range_vals, is_in, ...)` — Place Range Dice bet (range prediction)

All methods return parsed JSON responses from the DuckDice API.

## Configuration

```python
from duckdice_api import DuckDiceConfig

cfg = DuckDiceConfig(
    api_key="your_api_key",                      # Required
    base_url="https://duckdice.io/api",         # Default
    timeout=30                                    # Seconds
)
```

## Error Handling

```python
from duckdice_api import DuckDiceAPIException

try:
    user = client.get_user_info()
except DuckDiceAPIException as e:
    print(f"API Error: {e}")
```

## Full Documentation

See [docs/USAGE.md](docs/USAGE.md) for more examples and [https://duckdice.io/bot-api](https://duckdice.io/bot-api) for official API documentation.

## Requirements

- Python 3.8+
- `requests>=2.25.0`

## Testing

Run the test suite:

```bash
pytest tests/
```

## License

MIT License — Copyright (c) 2025 duckdice.casino
