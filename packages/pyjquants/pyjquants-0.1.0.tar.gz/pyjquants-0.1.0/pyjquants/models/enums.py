"""Enumerations for pyjquants."""

from __future__ import annotations

from enum import Enum


class MarketSegment(str, Enum):
    """Market segment classification."""

    TSE_PRIME = "Prime"
    TSE_STANDARD = "Standard"
    TSE_GROWTH = "Growth"
    TOKYO_PRO = "Tokyo Pro Market"
    OTHER = "Other"

    @classmethod
    def from_code(cls, code: str) -> MarketSegment:
        """Convert market code to MarketSegment."""
        code_map = {
            "0111": cls.TSE_PRIME,
            "0112": cls.TSE_STANDARD,
            "0113": cls.TSE_GROWTH,
            "0105": cls.TOKYO_PRO,
            "0109": cls.OTHER,
        }
        return code_map.get(code, cls.OTHER)


class OrderSide(str, Enum):
    """Order side (buy or sell)."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OptionType(str, Enum):
    """Option type (call or put)."""

    CALL = "call"
    PUT = "put"
