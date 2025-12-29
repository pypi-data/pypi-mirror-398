"""Order and Execution classes for paper trading."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pyjquants.models.enums import OrderSide, OrderStatus, OrderType

if TYPE_CHECKING:
    from pyjquants.entities.stock import Stock


@dataclass
class Order:
    """Simulated order representation."""

    stock: Stock
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    price: Decimal | None = None  # For limit orders
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: datetime | None = None
    filled_price: Decimal | None = None
    filled_quantity: int = 0

    @classmethod
    def market_buy(cls, stock: Stock, quantity: int) -> Order:
        """Create market buy order."""
        return cls(
            stock=stock,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )

    @classmethod
    def market_sell(cls, stock: Stock, quantity: int) -> Order:
        """Create market sell order."""
        return cls(
            stock=stock,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )

    @classmethod
    def limit_buy(cls, stock: Stock, quantity: int, price: Decimal) -> Order:
        """Create limit buy order."""
        return cls(
            stock=stock,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
        )

    @classmethod
    def limit_sell(cls, stock: Stock, quantity: int, price: Decimal) -> Order:
        """Create limit sell order."""
        return cls(
            stock=stock,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
        )

    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED)

    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity

    def cancel(self) -> bool:
        """
        Cancel the order.

        Returns:
            True if successfully cancelled
        """
        if self.is_active:
            self.status = OrderStatus.CANCELLED
            return True
        return False

    def fill(self, price: Decimal, quantity: int | None = None) -> None:
        """
        Fill the order (or partially fill).

        Args:
            price: Execution price
            quantity: Quantity filled (default: remaining quantity)
        """
        if quantity is None:
            quantity = self.remaining_quantity

        self.filled_quantity += quantity
        self.filled_price = price
        self.filled_at = datetime.now()

        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def __repr__(self) -> str:
        return (
            f"Order({self.id}: {self.side.value} {self.quantity} "
            f"{self.stock.code} @ {self.price or 'market'}, {self.status.value})"
        )


@dataclass
class Execution:
    """Record of a filled order."""

    order: Order
    stock: Stock
    side: OrderSide
    quantity: int
    price: Decimal
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def value(self) -> Decimal:
        """Total value of execution."""
        return self.price * self.quantity

    def __repr__(self) -> str:
        return (
            f"Execution({self.side.value} {self.quantity} "
            f"{self.stock.code} @ {self.price})"
        )
