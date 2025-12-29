"""Portfolio and Position classes for paper trading."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.models.enums import OrderSide
from pyjquants.trading.order import Execution

if TYPE_CHECKING:
    from pyjquants.entities.stock import Stock


@dataclass
class Position:
    """Represents a holding in the portfolio."""

    stock: Stock
    quantity: int
    average_cost: Decimal

    @property
    def cost_basis(self) -> Decimal:
        """Total cost basis."""
        return self.average_cost * self.quantity

    @property
    def market_value(self) -> Decimal:
        """Current market value."""
        latest = self.stock.latest_price
        if latest is None:
            return self.cost_basis
        return Decimal(str(latest.close)) * self.quantity

    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit/loss."""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized P&L as percentage."""
        if self.cost_basis == 0:
            return 0.0
        return float(self.unrealized_pnl / self.cost_basis * 100)

    def update(self, quantity_delta: int, price: Decimal) -> None:
        """
        Update position with new trade.

        Args:
            quantity_delta: Positive for buy, negative for sell
            price: Trade price
        """
        if quantity_delta > 0:
            # Buying: update average cost
            new_cost = self.average_cost * self.quantity + price * quantity_delta
            new_quantity = self.quantity + quantity_delta
            self.average_cost = new_cost / new_quantity
            self.quantity = new_quantity
        else:
            # Selling: just reduce quantity (keep average cost for remaining)
            self.quantity += quantity_delta

    def __repr__(self) -> str:
        return f"Position({self.stock.code}: {self.quantity} @ {self.average_cost})"


@dataclass
class Portfolio:
    """Simulated portfolio for paper trading."""

    _positions: dict[str, Position] = field(default_factory=dict)
    _cash: Decimal = field(default_factory=lambda: Decimal("10000000"))
    _executions: list[Execution] = field(default_factory=list)
    _realized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))

    @property
    def positions(self) -> list[Position]:
        """Get all current positions (with quantity > 0)."""
        return [p for p in self._positions.values() if p.quantity > 0]

    @property
    def cash(self) -> Decimal:
        """Current cash balance."""
        return self._cash

    @property
    def total_value(self) -> Decimal:
        """Total portfolio value (cash + positions)."""
        positions_value = sum(p.market_value for p in self.positions)
        return self._cash + positions_value

    @property
    def realized_pnl(self) -> Decimal:
        """Total realized P&L."""
        return self._realized_pnl

    @property
    def unrealized_pnl(self) -> Decimal:
        """Total unrealized P&L."""
        return sum((p.unrealized_pnl for p in self.positions), Decimal("0"))

    def position(self, stock: Stock) -> Position | None:
        """Get position for a stock."""
        pos = self._positions.get(stock.code)
        if pos and pos.quantity > 0:
            return pos
        return None

    def add_position(self, stock: Stock, quantity: int, price: Decimal) -> Position:
        """Add a new position or update existing."""
        if stock.code in self._positions:
            pos = self._positions[stock.code]
            pos.update(quantity, price)
        else:
            pos = Position(stock=stock, quantity=quantity, average_cost=price)
            self._positions[stock.code] = pos
        return pos

    def update_from_execution(self, execution: Execution) -> None:
        """
        Update portfolio from an execution.

        Args:
            execution: The execution to process
        """
        stock = execution.stock
        price = execution.price
        quantity = execution.quantity

        if execution.side == OrderSide.BUY:
            # Deduct cash and add position
            self._cash -= price * quantity
            self.add_position(stock, quantity, price)
        else:
            # Selling: add cash and reduce position
            self._cash += price * quantity

            if stock.code in self._positions:
                pos = self._positions[stock.code]
                # Calculate realized P&L
                realized = (price - pos.average_cost) * quantity
                self._realized_pnl += realized
                pos.update(-quantity, price)

        self._executions.append(execution)

    def summary(self) -> pd.DataFrame:
        """Get portfolio summary as DataFrame."""
        if not self.positions:
            return pd.DataFrame(
                columns=[
                    "code",
                    "name",
                    "quantity",
                    "avg_cost",
                    "market_value",
                    "unrealized_pnl",
                    "weight",
                ]
            )

        data = []
        total = self.total_value
        for pos in self.positions:
            data.append(
                {
                    "code": pos.stock.code,
                    "name": pos.stock.name,
                    "quantity": pos.quantity,
                    "avg_cost": float(pos.average_cost),
                    "market_value": float(pos.market_value),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "weight": float(pos.market_value / total) if total > 0 else 0,
                }
            )

        return pd.DataFrame(data)

    def history(self) -> pd.DataFrame:
        """Get execution history as DataFrame."""
        if not self._executions:
            return pd.DataFrame(
                columns=["timestamp", "code", "side", "quantity", "price", "value"]
            )

        data = []
        for ex in self._executions:
            data.append(
                {
                    "timestamp": ex.timestamp,
                    "code": ex.stock.code,
                    "side": ex.side.value,
                    "quantity": ex.quantity,
                    "price": float(ex.price),
                    "value": float(ex.value),
                }
            )

        return pd.DataFrame(data)

    def weights(self) -> dict[str, float]:
        """Get portfolio weights by stock."""
        total = self.total_value
        if total == 0:
            return {}
        return {
            pos.stock.code: float(pos.market_value / total) for pos in self.positions
        }

    def __repr__(self) -> str:
        return f"Portfolio(cash={self._cash}, positions={len(self.positions)})"
