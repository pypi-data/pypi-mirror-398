"""
PyJQuants - Investor-friendly OOP Python library for J-Quants API.

Usage:
    import pyjquants as pjq

    # Env vars JQUANTS_MAIL_ADDRESS & JQUANTS_PASSWORD are auto-read
    stock = pjq.Stock("7203")
    stock.name              # "Toyota Motor Corporation"
    stock.prices            # Recent 30 days DataFrame

    # Trading simulation
    trader = pjq.Trader(initial_cash=10_000_000)
    trader.buy(stock, 100)
"""

# Collections
from pyjquants.collections.market import Market
from pyjquants.collections.universe import Universe
from pyjquants.core.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NotFoundError,
    PyJQuantsError,
    RateLimitError,
    TokenExpiredError,
    ValidationError,
)
from pyjquants.core.session import Session, set_global_session
from pyjquants.entities.index import Index

# Entities
from pyjquants.entities.stock import Stock
from pyjquants.models.company import Sector

# Models
from pyjquants.models.enums import (
    MarketSegment,
    OptionType,
    OrderSide,
    OrderStatus,
    OrderType,
)
from pyjquants.models.price import PriceBar

# Trading
from pyjquants.trading.order import Execution, Order
from pyjquants.trading.portfolio import Portfolio, Position
from pyjquants.trading.trader import Trader

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Session
    "Session",
    "set_global_session",
    # Exceptions
    "PyJQuantsError",
    "AuthenticationError",
    "TokenExpiredError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ConfigurationError",
    # Entities
    "Stock",
    "Index",
    # Collections
    "Market",
    "Universe",
    # Trading
    "Order",
    "Execution",
    "Portfolio",
    "Position",
    "Trader",
    # Models/Enums
    "MarketSegment",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "OptionType",
    "Sector",
    "PriceBar",
]
