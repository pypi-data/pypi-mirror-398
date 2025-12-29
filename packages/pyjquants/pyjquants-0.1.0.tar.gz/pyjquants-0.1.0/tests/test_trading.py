"""Tests for pyjquants trading module."""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock

import pytest

from pyjquants.models.enums import OrderSide, OrderStatus, OrderType
from pyjquants.trading.order import Order, Execution
from pyjquants.trading.portfolio import Portfolio, Position
from pyjquants.trading.trader import Trader


@pytest.fixture
def mock_stock() -> MagicMock:
    """Create a mock Stock for testing."""
    stock = MagicMock()
    stock.code = "7203"
    stock.name = "Toyota Motor Corporation"
    return stock


@pytest.fixture
def mock_stock_with_price(mock_stock: MagicMock) -> MagicMock:
    """Mock stock with latest_price property."""
    price_bar = MagicMock()
    price_bar.close = Decimal("2500")
    price_bar.open = Decimal("2480")
    price_bar.high = Decimal("2550")
    price_bar.low = Decimal("2450")
    type(mock_stock).latest_price = PropertyMock(return_value=price_bar)
    return mock_stock


class TestOrder:
    """Tests for Order class."""

    def test_market_buy(self, mock_stock: MagicMock) -> None:
        """Test creating a market buy order."""
        order = Order.market_buy(mock_stock, 100)

        assert order.stock == mock_stock
        assert order.side == OrderSide.BUY
        assert order.quantity == 100
        assert order.order_type == OrderType.MARKET
        assert order.price is None
        assert order.status == OrderStatus.PENDING

    def test_market_sell(self, mock_stock: MagicMock) -> None:
        """Test creating a market sell order."""
        order = Order.market_sell(mock_stock, 50)

        assert order.side == OrderSide.SELL
        assert order.order_type == OrderType.MARKET

    def test_limit_buy(self, mock_stock: MagicMock) -> None:
        """Test creating a limit buy order."""
        order = Order.limit_buy(mock_stock, 100, Decimal("2500"))

        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("2500")
        assert order.side == OrderSide.BUY

    def test_limit_sell(self, mock_stock: MagicMock) -> None:
        """Test creating a limit sell order."""
        order = Order.limit_sell(mock_stock, 100, Decimal("2600"))

        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("2600")
        assert order.side == OrderSide.SELL

    def test_order_has_unique_id(self, mock_stock: MagicMock) -> None:
        """Test that each order gets a unique ID."""
        order1 = Order.market_buy(mock_stock, 100)
        order2 = Order.market_buy(mock_stock, 100)

        assert order1.id != order2.id

    def test_is_active(self, mock_stock: MagicMock) -> None:
        """Test is_active property."""
        order = Order.market_buy(mock_stock, 100)

        assert order.is_active is True
        order.status = OrderStatus.FILLED
        assert order.is_active is False

    def test_is_filled(self, mock_stock: MagicMock) -> None:
        """Test is_filled property."""
        order = Order.market_buy(mock_stock, 100)

        assert order.is_filled is False
        order.status = OrderStatus.FILLED
        assert order.is_filled is True

    def test_remaining_quantity(self, mock_stock: MagicMock) -> None:
        """Test remaining quantity calculation."""
        order = Order.market_buy(mock_stock, 100)

        assert order.remaining_quantity == 100
        order.filled_quantity = 30
        assert order.remaining_quantity == 70

    def test_cancel_active_order(self, mock_stock: MagicMock) -> None:
        """Test cancelling an active order."""
        order = Order.market_buy(mock_stock, 100)

        result = order.cancel()

        assert result is True
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_filled_order(self, mock_stock: MagicMock) -> None:
        """Test cancelling a filled order fails."""
        order = Order.market_buy(mock_stock, 100)
        order.status = OrderStatus.FILLED

        result = order.cancel()

        assert result is False
        assert order.status == OrderStatus.FILLED

    def test_fill_order(self, mock_stock: MagicMock) -> None:
        """Test filling an order."""
        order = Order.market_buy(mock_stock, 100)

        order.fill(Decimal("2500"))

        assert order.filled_quantity == 100
        assert order.filled_price == Decimal("2500")
        assert order.status == OrderStatus.FILLED
        assert order.filled_at is not None

    def test_partial_fill(self, mock_stock: MagicMock) -> None:
        """Test partially filling an order."""
        order = Order.market_buy(mock_stock, 100)

        order.fill(Decimal("2500"), quantity=50)

        assert order.filled_quantity == 50
        assert order.status == OrderStatus.PARTIALLY_FILLED
        assert order.remaining_quantity == 50


class TestExecution:
    """Tests for Execution class."""

    def test_execution_value(self, mock_stock: MagicMock) -> None:
        """Test execution value calculation."""
        order = Order.market_buy(mock_stock, 100)
        execution = Execution(
            order=order,
            stock=mock_stock,
            side=OrderSide.BUY,
            quantity=100,
            price=Decimal("2500"),
        )

        assert execution.value == Decimal("250000")


class TestPosition:
    """Tests for Position class."""

    def test_cost_basis(self, mock_stock_with_price: MagicMock) -> None:
        """Test cost basis calculation."""
        position = Position(
            stock=mock_stock_with_price,
            quantity=100,
            average_cost=Decimal("2400"),
        )

        assert position.cost_basis == Decimal("240000")

    def test_market_value(self, mock_stock_with_price: MagicMock) -> None:
        """Test market value calculation."""
        position = Position(
            stock=mock_stock_with_price,
            quantity=100,
            average_cost=Decimal("2400"),
        )

        assert position.market_value == Decimal("250000")

    def test_unrealized_pnl(self, mock_stock_with_price: MagicMock) -> None:
        """Test unrealized P&L calculation."""
        position = Position(
            stock=mock_stock_with_price,
            quantity=100,
            average_cost=Decimal("2400"),
        )

        # Market value 250000 - Cost 240000 = 10000
        assert position.unrealized_pnl == Decimal("10000")

    def test_unrealized_pnl_percent(self, mock_stock_with_price: MagicMock) -> None:
        """Test unrealized P&L percentage."""
        position = Position(
            stock=mock_stock_with_price,
            quantity=100,
            average_cost=Decimal("2400"),
        )

        # 10000 / 240000 * 100 = 4.166...
        assert abs(position.unrealized_pnl_percent - 4.1666) < 0.01

    def test_update_buy(self, mock_stock_with_price: MagicMock) -> None:
        """Test updating position with a buy."""
        position = Position(
            stock=mock_stock_with_price,
            quantity=100,
            average_cost=Decimal("2400"),
        )

        # Buy 100 more at 2600
        position.update(100, Decimal("2600"))

        assert position.quantity == 200
        # New avg = (2400*100 + 2600*100) / 200 = 2500
        assert position.average_cost == Decimal("2500")

    def test_update_sell(self, mock_stock_with_price: MagicMock) -> None:
        """Test updating position with a sell."""
        position = Position(
            stock=mock_stock_with_price,
            quantity=100,
            average_cost=Decimal("2400"),
        )

        # Sell 50 shares
        position.update(-50, Decimal("2600"))

        assert position.quantity == 50
        assert position.average_cost == Decimal("2400")  # Average cost unchanged


class TestPortfolio:
    """Tests for Portfolio class."""

    def test_initial_state(self) -> None:
        """Test initial portfolio state."""
        portfolio = Portfolio()

        assert portfolio.cash == Decimal("10000000")
        assert len(portfolio.positions) == 0
        assert portfolio.realized_pnl == Decimal("0")

    def test_custom_initial_cash(self) -> None:
        """Test portfolio with custom initial cash."""
        portfolio = Portfolio(_cash=Decimal("5000000"))

        assert portfolio.cash == Decimal("5000000")

    def test_add_position(self, mock_stock_with_price: MagicMock) -> None:
        """Test adding a position."""
        portfolio = Portfolio()

        pos = portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        assert pos.quantity == 100
        assert pos.average_cost == Decimal("2400")
        assert len(portfolio.positions) == 1

    def test_add_to_existing_position(self, mock_stock_with_price: MagicMock) -> None:
        """Test adding to an existing position."""
        portfolio = Portfolio()
        portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        portfolio.add_position(mock_stock_with_price, 100, Decimal("2600"))

        positions = portfolio.positions
        assert len(positions) == 1
        assert positions[0].quantity == 200
        assert positions[0].average_cost == Decimal("2500")

    def test_position_lookup(self, mock_stock_with_price: MagicMock) -> None:
        """Test looking up a position."""
        portfolio = Portfolio()
        portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        pos = portfolio.position(mock_stock_with_price)

        assert pos is not None
        assert pos.quantity == 100

    def test_position_lookup_not_found(self, mock_stock: MagicMock) -> None:
        """Test looking up a non-existent position."""
        portfolio = Portfolio()

        pos = portfolio.position(mock_stock)

        assert pos is None

    def test_total_value(self, mock_stock_with_price: MagicMock) -> None:
        """Test total portfolio value."""
        portfolio = Portfolio(_cash=Decimal("1000000"))
        portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        # Cash 1000000 + Market value (2500 * 100 = 250000) = 1250000
        assert portfolio.total_value == Decimal("1250000")

    def test_update_from_buy_execution(self, mock_stock_with_price: MagicMock) -> None:
        """Test updating portfolio from a buy execution."""
        portfolio = Portfolio(_cash=Decimal("1000000"))
        order = Order.market_buy(mock_stock_with_price, 100)
        execution = Execution(
            order=order,
            stock=mock_stock_with_price,
            side=OrderSide.BUY,
            quantity=100,
            price=Decimal("2500"),
        )

        portfolio.update_from_execution(execution)

        assert portfolio.cash == Decimal("750000")  # 1000000 - 250000
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].quantity == 100

    def test_update_from_sell_execution(self, mock_stock_with_price: MagicMock) -> None:
        """Test updating portfolio from a sell execution."""
        portfolio = Portfolio(_cash=Decimal("750000"))
        portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        order = Order.market_sell(mock_stock_with_price, 50)
        execution = Execution(
            order=order,
            stock=mock_stock_with_price,
            side=OrderSide.SELL,
            quantity=50,
            price=Decimal("2600"),
        )

        portfolio.update_from_execution(execution)

        assert portfolio.cash == Decimal("880000")  # 750000 + 130000
        # Realized P&L: (2600 - 2400) * 50 = 10000
        assert portfolio.realized_pnl == Decimal("10000")
        assert portfolio.positions[0].quantity == 50

    def test_weights(self, mock_stock_with_price: MagicMock) -> None:
        """Test portfolio weights calculation."""
        portfolio = Portfolio(_cash=Decimal("750000"))
        portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        weights = portfolio.weights()

        # Position value: 250000, Total: 1000000
        assert "7203" in weights
        assert weights["7203"] == pytest.approx(0.25, rel=0.01)


class TestTrader:
    """Tests for Trader class."""

    def test_init_default_cash(self) -> None:
        """Test trader initialization with default cash."""
        trader = Trader()

        assert trader.cash == Decimal("10000000")

    def test_init_custom_cash(self) -> None:
        """Test trader initialization with custom cash."""
        trader = Trader(initial_cash=5000000)

        assert trader.cash == Decimal("5000000")

    def test_init_decimal_cash(self) -> None:
        """Test trader initialization with Decimal cash."""
        trader = Trader(initial_cash=Decimal("5000000.50"))

        assert trader.cash == Decimal("5000000.50")

    def test_buy_market_order(self, mock_stock: MagicMock) -> None:
        """Test placing a market buy order."""
        trader = Trader()

        order = trader.buy(mock_stock, 100)

        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 100
        assert order in trader.pending_orders()

    def test_buy_limit_order(self, mock_stock: MagicMock) -> None:
        """Test placing a limit buy order."""
        trader = Trader()

        order = trader.buy(mock_stock, 100, price=2500.0)

        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("2500")

    def test_sell_market_order(self, mock_stock: MagicMock) -> None:
        """Test placing a market sell order."""
        trader = Trader()

        order = trader.sell(mock_stock, 50)

        assert order.side == OrderSide.SELL
        assert order.order_type == OrderType.MARKET

    def test_sell_limit_order(self, mock_stock: MagicMock) -> None:
        """Test placing a limit sell order."""
        trader = Trader()

        order = trader.sell(mock_stock, 50, price=Decimal("2600"))

        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("2600")

    def test_make_order(self, mock_stock: MagicMock) -> None:
        """Test submitting a pre-built order."""
        trader = Trader()
        order = Order.market_buy(mock_stock, 100)

        result = trader.make_order(order)

        assert result == order
        assert order in trader.pending_orders()

    def test_cancel_order(self, mock_stock: MagicMock) -> None:
        """Test cancelling a pending order."""
        trader = Trader()
        order = trader.buy(mock_stock, 100)

        result = trader.cancel_order(order)

        assert result is True
        assert order not in trader.pending_orders()
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_non_pending_order(self, mock_stock: MagicMock) -> None:
        """Test cancelling an order not in pending list."""
        trader = Trader()
        order = Order.market_buy(mock_stock, 100)

        result = trader.cancel_order(order)

        assert result is False

    def test_pending_orders(self, mock_stock: MagicMock) -> None:
        """Test getting pending orders."""
        trader = Trader()
        order1 = trader.buy(mock_stock, 100)
        order2 = trader.sell(mock_stock, 50)

        pending = trader.pending_orders()

        assert len(pending) == 2
        assert order1 in pending
        assert order2 in pending

    def test_position_shortcut(self, mock_stock_with_price: MagicMock) -> None:
        """Test position shortcut method."""
        trader = Trader()
        trader.portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        pos = trader.position(mock_stock_with_price)

        assert pos is not None
        assert pos.quantity == 100

    def test_positions_shortcut(self, mock_stock_with_price: MagicMock) -> None:
        """Test positions shortcut method."""
        trader = Trader()
        trader.portfolio.add_position(mock_stock_with_price, 100, Decimal("2400"))

        positions = trader.positions()

        assert len(positions) == 1

    def test_simulate_fills_market_order(self, mock_stock: MagicMock) -> None:
        """Test simulating market order fills."""
        trader = Trader()

        # Setup mock price data
        bar = MagicMock()
        bar.open = Decimal("2500")
        bar.high = Decimal("2550")
        bar.low = Decimal("2450")
        bar.close = Decimal("2530")
        mock_stock.price_bars.return_value = [bar]

        # Setup latest_price for portfolio calculations
        type(mock_stock).latest_price = PropertyMock(return_value=bar)

        order = trader.buy(mock_stock, 100)

        executions = trader.simulate_fills(datetime.date(2024, 1, 15))

        assert len(executions) == 1
        assert executions[0].price == Decimal("2500")  # Filled at open
        assert order.is_filled
        assert order not in trader.pending_orders()

    def test_simulate_fills_limit_buy_triggered(self, mock_stock: MagicMock) -> None:
        """Test simulating limit buy order that gets triggered."""
        trader = Trader()

        bar = MagicMock()
        bar.open = Decimal("2480")
        bar.high = Decimal("2550")
        bar.low = Decimal("2450")
        bar.close = Decimal("2530")
        mock_stock.price_bars.return_value = [bar]
        type(mock_stock).latest_price = PropertyMock(return_value=bar)

        # Limit buy at 2470 - low reaches 2450, should fill
        order = trader.buy(mock_stock, 100, price=Decimal("2470"))

        executions = trader.simulate_fills(datetime.date(2024, 1, 15))

        assert len(executions) == 1
        assert executions[0].price == Decimal("2470")  # Fill at limit price

    def test_simulate_fills_limit_buy_not_triggered(self, mock_stock: MagicMock) -> None:
        """Test simulating limit buy order that doesn't trigger."""
        trader = Trader()

        bar = MagicMock()
        bar.open = Decimal("2500")
        bar.high = Decimal("2550")
        bar.low = Decimal("2480")  # Low is 2480, above limit
        bar.close = Decimal("2530")
        mock_stock.price_bars.return_value = [bar]

        # Limit buy at 2470 - low doesn't reach, shouldn't fill
        order = trader.buy(mock_stock, 100, price=Decimal("2470"))

        executions = trader.simulate_fills(datetime.date(2024, 1, 15))

        assert len(executions) == 0
        assert not order.is_filled
        assert order in trader.pending_orders()

    def test_simulate_fills_no_price_data(self, mock_stock: MagicMock) -> None:
        """Test simulating fills when no price data available."""
        trader = Trader()
        mock_stock.price_bars.return_value = []

        order = trader.buy(mock_stock, 100)

        executions = trader.simulate_fills(datetime.date(2024, 1, 15))

        assert len(executions) == 0
        assert order in trader.pending_orders()
