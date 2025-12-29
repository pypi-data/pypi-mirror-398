"""Tests for pyjquants models."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from pyjquants.models.price import PriceBar
from pyjquants.models.company import Sector, StockInfo
from pyjquants.models.enums import MarketSegment, OrderSide, OrderType, OrderStatus
from pyjquants.models.financials import FinancialStatement, Dividend
from pyjquants.models.market import TradingCalendarDay


class TestPriceBar:
    """Tests for PriceBar model."""

    def test_create_from_dict(self) -> None:
        """Test creating PriceBar from API response dict."""
        data = {
            "Date": "2024-01-15",
            "Open": "2500.0",
            "High": "2550.0",
            "Low": "2480.0",
            "Close": "2530.0",
            "Volume": 1000000,
        }
        bar = PriceBar.model_validate(data)

        assert bar.date == datetime.date(2024, 1, 15)
        assert bar.open == Decimal("2500.0")
        assert bar.high == Decimal("2550.0")
        assert bar.low == Decimal("2480.0")
        assert bar.close == Decimal("2530.0")
        assert bar.volume == 1000000

    def test_create_with_yyyymmdd_date(self) -> None:
        """Test parsing YYYYMMDD date format."""
        data = {
            "Date": "20240115",
            "Open": "2500.0",
            "High": "2550.0",
            "Low": "2480.0",
            "Close": "2530.0",
            "Volume": 1000000,
        }
        bar = PriceBar.model_validate(data)
        assert bar.date == datetime.date(2024, 1, 15)

    def test_adjusted_prices_default(self, sample_price_bar: PriceBar) -> None:
        """Test adjusted prices with factor 1.0."""
        assert sample_price_bar.adjusted_open == sample_price_bar.open
        assert sample_price_bar.adjusted_close == sample_price_bar.close
        assert sample_price_bar.adjusted_volume == sample_price_bar.volume

    def test_adjusted_prices_with_factor(self) -> None:
        """Test adjusted prices with adjustment factor."""
        bar = PriceBar(
            date=datetime.date(2024, 1, 15),
            open=Decimal("2500.0"),
            high=Decimal("2550.0"),
            low=Decimal("2480.0"),
            close=Decimal("2530.0"),
            volume=1000000,
            adjustment_factor=Decimal("2.0"),
        )
        assert bar.adjusted_open == Decimal("5000.0")
        assert bar.adjusted_close == Decimal("5060.0")

    def test_to_dict(self, sample_price_bar: PriceBar) -> None:
        """Test converting to dictionary."""
        d = sample_price_bar.to_dict()
        assert d["date"] == datetime.date(2024, 1, 15)
        assert d["close"] == 2530.0
        assert d["volume"] == 1000000


class TestSector:
    """Tests for Sector model."""

    def test_create_sector(self) -> None:
        """Test creating a Sector."""
        sector = Sector(code="3050", name="輸送用機器", name_english="Transportation Equipment")
        assert sector.code == "3050"
        assert sector.name == "輸送用機器"
        assert str(sector) == "輸送用機器"

    def test_sector_equality(self) -> None:
        """Test Sector equality."""
        s1 = Sector(code="3050", name="輸送用機器")
        s2 = Sector(code="3050", name="輸送用機器")
        s3 = Sector(code="3100", name="電気機器")

        assert s1 == s2
        assert s1 != s3
        assert s1 == "3050"  # Can compare with code string

    def test_sector_hash(self) -> None:
        """Test Sector can be used in sets."""
        s1 = Sector(code="3050", name="輸送用機器")
        s2 = Sector(code="3050", name="輸送用機器")

        sector_set = {s1, s2}
        assert len(sector_set) == 1


class TestStockInfo:
    """Tests for StockInfo model."""

    def test_create_from_api_data(self, sample_stock_info_data: dict) -> None:
        """Test creating StockInfo from API response."""
        info = StockInfo.model_validate(sample_stock_info_data)

        assert info.code == "7203"
        assert info.company_name == "トヨタ自動車"
        assert info.company_name_english == "Toyota Motor Corporation"
        assert info.sector_33_code == "3050"

    def test_sector_properties(self, sample_stock_info: StockInfo) -> None:
        """Test sector property accessors."""
        assert sample_stock_info.sector_17.code == "6"
        assert sample_stock_info.sector_33.code == "3050"

    def test_market_segment(self, sample_stock_info: StockInfo) -> None:
        """Test market segment conversion."""
        assert sample_stock_info.market_segment == MarketSegment.TSE_PRIME

    def test_listing_date(self, sample_stock_info: StockInfo) -> None:
        """Test listing date parsing."""
        assert sample_stock_info.listing_date == datetime.date(2024, 1, 15)


class TestMarketSegment:
    """Tests for MarketSegment enum."""

    def test_from_code(self) -> None:
        """Test converting market codes."""
        assert MarketSegment.from_code("0111") == MarketSegment.TSE_PRIME
        assert MarketSegment.from_code("0112") == MarketSegment.TSE_STANDARD
        assert MarketSegment.from_code("0113") == MarketSegment.TSE_GROWTH
        assert MarketSegment.from_code("0105") == MarketSegment.TOKYO_PRO
        assert MarketSegment.from_code("0109") == MarketSegment.OTHER
        assert MarketSegment.from_code("9999") == MarketSegment.OTHER


class TestTradingCalendarDay:
    """Tests for TradingCalendarDay model."""

    def test_trading_day(self) -> None:
        """Test trading day identification."""
        day = TradingCalendarDay(
            date=datetime.date(2024, 1, 15),
            holiday_division="0",
        )
        assert day.is_trading_day is True
        assert day.is_holiday is False

    def test_holiday(self) -> None:
        """Test holiday identification."""
        day = TradingCalendarDay(
            date=datetime.date(2024, 1, 1),
            holiday_division="1",
        )
        assert day.is_trading_day is False
        assert day.is_holiday is True


class TestEnums:
    """Tests for enum types."""

    def test_order_side(self) -> None:
        """Test OrderSide enum."""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"

    def test_order_type(self) -> None:
        """Test OrderType enum."""
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"

    def test_order_status(self) -> None:
        """Test OrderStatus enum."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.CANCELLED.value == "cancelled"
