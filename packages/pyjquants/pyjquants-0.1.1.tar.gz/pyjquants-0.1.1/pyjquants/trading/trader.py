"""Trader class for paper trading simulation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pyjquants.models.enums import OrderSide, OrderType
from pyjquants.trading.order import Execution, Order
from pyjquants.trading.portfolio import Portfolio, Position

if TYPE_CHECKING:
    from pyjquants.entities.stock import Stock


class Trader:
    """
    Paper trading simulation interface.
    Separate from data access - Stock/Index handle data, Trader handles simulation.

    Usage:
        stock = Stock("7203")
        trader = Trader(initial_cash=10_000_000)
        trader.buy(stock, 100)
        trader.simulate_fills(date(2024, 6, 15))
        print(trader.portfolio.total_value)
    """

    def __init__(self, initial_cash: Decimal | int | float = 10_000_000) -> None:
        """
        Initialize paper trading with starting cash.

        Args:
            initial_cash: Starting cash (default 10M JPY)
        """
        if not isinstance(initial_cash, Decimal):
            initial_cash = Decimal(str(initial_cash))

        self._portfolio = Portfolio(_cash=initial_cash)
        self._pending_orders: list[Order] = []

    # === PROPERTIES ===

    @property
    def portfolio(self) -> Portfolio:
        """Get the portfolio."""
        return self._portfolio

    @property
    def cash(self) -> Decimal:
        """Current cash balance."""
        return self._portfolio.cash

    # === ORDER MANAGEMENT ===

    def buy(
        self, stock: Stock, quantity: int, price: Decimal | float | None = None
    ) -> Order:
        """
        Place buy order.

        Args:
            stock: Stock to buy
            quantity: Number of shares
            price: Limit price (None for market order)

        Returns:
            The created Order
        """
        if price is not None:
            if not isinstance(price, Decimal):
                price = Decimal(str(price))
            order = Order.limit_buy(stock, quantity, price)
        else:
            order = Order.market_buy(stock, quantity)

        self._pending_orders.append(order)
        return order

    def sell(
        self, stock: Stock, quantity: int, price: Decimal | float | None = None
    ) -> Order:
        """
        Place sell order.

        Args:
            stock: Stock to sell
            quantity: Number of shares
            price: Limit price (None for market order)

        Returns:
            The created Order
        """
        if price is not None:
            if not isinstance(price, Decimal):
                price = Decimal(str(price))
            order = Order.limit_sell(stock, quantity, price)
        else:
            order = Order.market_sell(stock, quantity)

        self._pending_orders.append(order)
        return order

    def make_order(self, order: Order) -> Order:
        """
        Submit a pre-built Order object.

        Args:
            order: The order to submit

        Returns:
            The submitted Order
        """
        self._pending_orders.append(order)
        return order

    def cancel_order(self, order: Order) -> bool:
        """
        Cancel a pending order.

        Args:
            order: The order to cancel

        Returns:
            True if successfully cancelled
        """
        if order in self._pending_orders:
            if order.cancel():
                self._pending_orders.remove(order)
                return True
        return False

    def pending_orders(self) -> list[Order]:
        """Get all unfilled orders."""
        return list(self._pending_orders)

    # === SIMULATION ===

    def simulate_fills(self, simulation_date: date) -> list[Execution]:
        """
        Simulate order execution for given date using historical prices.

        Args:
            simulation_date: Date to simulate fills for

        Returns:
            List of executions that occurred
        """
        executions: list[Execution] = []
        orders_to_remove: list[Order] = []

        for order in self._pending_orders:
            # Get price for the simulation date
            bars = order.stock.price_bars(simulation_date, simulation_date)
            if not bars:
                continue  # No price data for this date

            bar = bars[0]

            # Determine if order can be filled
            fill_price: Decimal | None = None

            if order.order_type == OrderType.MARKET:
                # Market orders fill at open
                fill_price = bar.open
            else:
                # Limit orders
                if order.side == OrderSide.BUY:
                    # Buy limit: fill if price drops to or below limit
                    if order.price is not None and bar.low <= order.price:
                        fill_price = min(order.price, bar.open)
                else:
                    # Sell limit: fill if price rises to or above limit
                    if order.price is not None and bar.high >= order.price:
                        fill_price = max(order.price, bar.open)

            if fill_price is not None:
                # Create execution
                execution = Execution(
                    order=order,
                    stock=order.stock,
                    side=order.side,
                    quantity=order.quantity,
                    price=fill_price,
                )

                # Update order status
                order.fill(fill_price)

                # Update portfolio
                self._portfolio.update_from_execution(execution)

                executions.append(execution)
                orders_to_remove.append(order)

        # Remove filled orders
        for order in orders_to_remove:
            self._pending_orders.remove(order)

        return executions

    # === PORTFOLIO SHORTCUTS ===

    def position(self, stock: Stock) -> Position | None:
        """Get position for a stock, or None if not held."""
        return self._portfolio.position(stock)

    def positions(self) -> list[Position]:
        """Get all current positions."""
        return self._portfolio.positions

    def __repr__(self) -> str:
        return f"Trader(cash={self.cash}, positions={len(self.positions())})"
