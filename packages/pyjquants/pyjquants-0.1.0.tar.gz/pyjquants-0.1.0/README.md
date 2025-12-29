# PyJQuants

[![CI](https://github.com/obichan117/pyjquants/actions/workflows/ci.yml/badge.svg)](https://github.com/obichan117/pyjquants/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Investor-friendly OOP Python library for [J-Quants API](https://jpx.gitbook.io/j-quants-en).

## Features

- **Intuitive OOP design**: `Stock("7203")` just works
- **Lazy-loaded attributes**: `stock.name`, `stock.prices`, `stock.financials`
- **Auto-authentication**: Reads credentials from environment variables
- **Paper trading simulation**: `Trader`, `Order`, `Portfolio`, `Position`
- **Type hints**: Full type annotations with Pydantic models
- **DataFrame integration**: Price data returned as pandas DataFrames

## Installation

```bash
pip install pyjquants
```

For development:
```bash
pip install pyjquants[dev]
```

## Quick Start

### Setup

Set your J-Quants credentials as environment variables:

```bash
export JQUANTS_MAIL_ADDRESS="your_email@example.com"
export JQUANTS_PASSWORD="your_password"
```

### Basic Usage

```python
import pyjquants as pjq

# Create a stock - data is lazy-loaded from API
stock = pjq.Stock("7203")  # Toyota

# Access attributes (fetched on first access, then cached)
stock.code              # "7203"
stock.name              # "トヨタ自動車"
stock.name_english      # "Toyota Motor Corporation"
stock.sector_33.name    # "輸送用機器"
stock.market_segment    # MarketSegment.TSE_PRIME

# Get price data as DataFrame
stock.prices            # Recent 30 trading days
stock.adjusted_prices   # Adjusted for splits/dividends

# Custom date range
from datetime import date
stock.prices_between(date(2024, 1, 1), date(2024, 6, 30))

# Financial data
stock.financials        # Latest financial statements
stock.dividends         # Dividend history
```

### Paper Trading

```python
import pyjquants as pjq
from datetime import date
from decimal import Decimal

# Initialize trader with starting cash
trader = pjq.Trader(initial_cash=10_000_000)

# Get stock
toyota = pjq.Stock("7203")

# Place orders
order = trader.buy(toyota, 100)                    # Market buy 100 shares
order = trader.buy(toyota, 100, price=2500)        # Limit buy at 2500
order = trader.sell(toyota, 50)                    # Market sell

# Simulate fills using historical prices
executions = trader.simulate_fills(date(2024, 6, 15))

# Check portfolio
trader.cash                     # Current cash balance
trader.portfolio.total_value    # Total portfolio value
trader.portfolio.positions      # List of positions
trader.portfolio.realized_pnl   # Realized P&L
trader.portfolio.unrealized_pnl # Unrealized P&L

# Get position for a specific stock
position = trader.position(toyota)
if position:
    print(f"Holding {position.quantity} shares")
    print(f"Average cost: {position.average_cost}")
    print(f"Unrealized P&L: {position.unrealized_pnl}")
```

### Market Data

```python
import pyjquants as pjq
from datetime import date

# Market utilities
market = pjq.Market()
market.is_trading_day(date(2024, 12, 25))  # False
market.trading_days(date(2024, 1, 1), date(2024, 1, 31))
market.next_trading_day(date(2024, 1, 1))

# Sector information
market.sectors_17  # 17-sector classification
market.sectors_33  # 33-sector classification
```

### Index Data

```python
import pyjquants as pjq

# Get TOPIX index
topix = pjq.Index.topix()
topix.name      # "TOPIX"
topix.prices    # Recent 30 days

# All available indices
indices = pjq.Index.all()
```

### Universe Filtering

```python
import pyjquants as pjq

# Get all stocks and filter
universe = pjq.Universe.all()
prime_stocks = (universe
    .filter_by_market(pjq.MarketSegment.TSE_PRIME)
    .head(50))

# Get prices for filtered universe
prime_stocks.prices  # Multi-stock DataFrame
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JQUANTS_MAIL_ADDRESS` | Your J-Quants email |
| `JQUANTS_PASSWORD` | Your J-Quants password |
| `JQUANTS_REFRESH_TOKEN` | (Optional) Refresh token |
| `JQUANTS_CACHE_ENABLED` | Enable caching (default: `true`) |
| `JQUANTS_CACHE_TTL` | Cache TTL in seconds (default: `3600`) |
| `JQUANTS_RATE_LIMIT` | Requests per minute (default: `60`) |

### TOML Configuration

Create `~/.jquants/config.toml`:

```toml
[credentials]
mail_address = "your_email@example.com"
password = "your_password"

[cache]
enabled = true
ttl_seconds = 3600

[rate_limit]
requests_per_minute = 60
```

## Data Models

### PriceBar

```python
from pyjquants import PriceBar

bar = stock.latest_price
bar.date            # datetime.date
bar.open            # Decimal
bar.high            # Decimal
bar.low             # Decimal
bar.close           # Decimal
bar.volume          # int
bar.adjustment_factor  # Decimal
bar.adjusted_close  # Decimal (adjusted for splits)
```

### Order

```python
from pyjquants import Order, OrderSide, OrderType, OrderStatus

order = Order.market_buy(stock, 100)
order = Order.limit_sell(stock, 100, Decimal("2600"))

order.id            # Unique order ID
order.side          # OrderSide.BUY or OrderSide.SELL
order.order_type    # OrderType.MARKET or OrderType.LIMIT
order.status        # OrderStatus.PENDING, FILLED, CANCELLED, etc.
order.is_active     # True if pending/partially filled
order.is_filled     # True if fully filled
```

## API Reference

### Entities

| Class | Description |
|-------|-------------|
| `Stock(code)` | Japanese stock with lazy-loaded data |
| `Index` | Market index (TOPIX, etc.) |
| `Market` | Market utilities (calendar, sectors) |
| `Universe` | Filterable collection of stocks |

### Trading

| Class | Description |
|-------|-------------|
| `Trader` | Paper trading interface |
| `Order` | Buy/sell order |
| `Portfolio` | Holdings and cash |
| `Position` | Single stock holding |
| `Execution` | Filled order record |

### Enums

| Enum | Values |
|------|--------|
| `MarketSegment` | `TSE_PRIME`, `TSE_STANDARD`, `TSE_GROWTH`, `OTHER` |
| `OrderSide` | `BUY`, `SELL` |
| `OrderType` | `MARKET`, `LIMIT` |
| `OrderStatus` | `PENDING`, `FILLED`, `PARTIALLY_FILLED`, `CANCELLED`, `REJECTED` |

## Development

```bash
# Clone repository
git clone https://github.com/obichan117/pyjquants.git
cd pyjquants

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=pyjquants --cov-report=term-missing

# Type checking
mypy pyjquants/

# Linting
ruff check pyjquants/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [J-Quants API Documentation](https://jpx.gitbook.io/j-quants-en)
- [GitHub Repository](https://github.com/obichan117/pyjquants)
