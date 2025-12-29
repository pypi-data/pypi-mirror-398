"""Tests for pyjquants entities."""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd
import pytest

from pyjquants.entities.stock import Stock
from pyjquants.entities.index import Index
from pyjquants.models.company import Sector, StockInfo
from pyjquants.models.enums import MarketSegment
from pyjquants.models.price import PriceBar


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock session."""
    return MagicMock()


@pytest.fixture
def sample_stock_info() -> StockInfo:
    """Create sample StockInfo."""
    return StockInfo.model_validate({
        "Code": "7203",
        "CompanyName": "トヨタ自動車",
        "CompanyNameEnglish": "Toyota Motor Corporation",
        "Sector17Code": "6",
        "Sector17CodeName": "自動車・輸送機",
        "Sector33Code": "3050",
        "Sector33CodeName": "輸送用機器",
        "MarketCode": "0111",
        "MarketCodeName": "プライム",
        "Date": "1949-05-16",
    })


@pytest.fixture
def sample_price_bars() -> list[PriceBar]:
    """Create sample price bars."""
    return [
        PriceBar(
            date=datetime.date(2024, 1, 15),
            open=Decimal("2500"),
            high=Decimal("2550"),
            low=Decimal("2480"),
            close=Decimal("2530"),
            volume=1000000,
        ),
        PriceBar(
            date=datetime.date(2024, 1, 16),
            open=Decimal("2530"),
            high=Decimal("2580"),
            low=Decimal("2520"),
            close=Decimal("2570"),
            volume=1200000,
        ),
    ]


class TestStock:
    """Tests for Stock entity."""

    def test_init(self, mock_session: MagicMock) -> None:
        """Test Stock initialization."""
        stock = Stock("7203", session=mock_session)

        assert stock.code == "7203"

    def test_str(self, mock_session: MagicMock) -> None:
        """Test Stock string representation."""
        stock = Stock("7203", session=mock_session)

        assert str(stock) == "7203"

    def test_equality_with_stock(self, mock_session: MagicMock) -> None:
        """Test Stock equality with another Stock."""
        stock1 = Stock("7203", session=mock_session)
        stock2 = Stock("7203", session=mock_session)
        stock3 = Stock("6758", session=mock_session)

        assert stock1 == stock2
        assert stock1 != stock3

    def test_equality_with_string(self, mock_session: MagicMock) -> None:
        """Test Stock equality with string code."""
        stock = Stock("7203", session=mock_session)

        assert stock == "7203"
        assert stock != "6758"

    def test_hash(self, mock_session: MagicMock) -> None:
        """Test Stock can be used in sets."""
        stock1 = Stock("7203", session=mock_session)
        stock2 = Stock("7203", session=mock_session)

        stock_set = {stock1, stock2}
        assert len(stock_set) == 1

    @patch("pyjquants.entities.stock.CompanyRepository")
    def test_name(
        self,
        mock_company_repo_cls: MagicMock,
        mock_session: MagicMock,
        sample_stock_info: StockInfo,
    ) -> None:
        """Test Stock name property."""
        mock_repo = MagicMock()
        mock_repo.listed_info.return_value = [sample_stock_info]
        mock_company_repo_cls.return_value = mock_repo

        stock = Stock("7203", session=mock_session)

        assert stock.name == "トヨタ自動車"
        mock_repo.listed_info.assert_called_once_with(code="7203")

    @patch("pyjquants.entities.stock.CompanyRepository")
    def test_name_english(
        self,
        mock_company_repo_cls: MagicMock,
        mock_session: MagicMock,
        sample_stock_info: StockInfo,
    ) -> None:
        """Test Stock name_english property."""
        mock_repo = MagicMock()
        mock_repo.listed_info.return_value = [sample_stock_info]
        mock_company_repo_cls.return_value = mock_repo

        stock = Stock("7203", session=mock_session)

        assert stock.name_english == "Toyota Motor Corporation"

    @patch("pyjquants.entities.stock.CompanyRepository")
    def test_sector_33(
        self,
        mock_company_repo_cls: MagicMock,
        mock_session: MagicMock,
        sample_stock_info: StockInfo,
    ) -> None:
        """Test Stock sector_33 property."""
        mock_repo = MagicMock()
        mock_repo.listed_info.return_value = [sample_stock_info]
        mock_company_repo_cls.return_value = mock_repo

        stock = Stock("7203", session=mock_session)

        assert stock.sector_33.code == "3050"
        assert stock.sector_33.name == "輸送用機器"

    @patch("pyjquants.entities.stock.CompanyRepository")
    def test_market_segment(
        self,
        mock_company_repo_cls: MagicMock,
        mock_session: MagicMock,
        sample_stock_info: StockInfo,
    ) -> None:
        """Test Stock market_segment property."""
        mock_repo = MagicMock()
        mock_repo.listed_info.return_value = [sample_stock_info]
        mock_company_repo_cls.return_value = mock_repo

        stock = Stock("7203", session=mock_session)

        assert stock.market_segment == MarketSegment.TSE_PRIME

    @patch("pyjquants.entities.stock.CompanyRepository")
    def test_stock_not_found(
        self,
        mock_company_repo_cls: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test Stock raises error when not found."""
        mock_repo = MagicMock()
        mock_repo.listed_info.return_value = []
        mock_company_repo_cls.return_value = mock_repo

        stock = Stock("9999", session=mock_session)

        with pytest.raises(ValueError, match="Stock not found"):
            _ = stock.name

    @patch("pyjquants.entities.stock.StockRepository")
    @patch("pyjquants.entities.stock.CompanyRepository")
    @patch("pyjquants.entities.stock.MarketRepository")
    def test_prices(
        self,
        mock_market_repo_cls: MagicMock,
        mock_company_repo_cls: MagicMock,
        mock_stock_repo_cls: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test Stock prices property."""
        mock_stock_repo = MagicMock()
        mock_stock_repo.daily_quotes_as_dataframe.return_value = pd.DataFrame({
            "date": [datetime.date(2024, 1, 15)],
            "open": [2500.0],
            "high": [2550.0],
            "low": [2480.0],
            "close": [2530.0],
            "volume": [1000000],
        })
        mock_stock_repo_cls.return_value = mock_stock_repo

        stock = Stock("7203", session=mock_session)
        prices = stock.prices

        assert len(prices) == 1
        mock_stock_repo.daily_quotes_as_dataframe.assert_called_once()

    @patch("pyjquants.entities.stock.StockRepository")
    @patch("pyjquants.entities.stock.CompanyRepository")
    @patch("pyjquants.entities.stock.MarketRepository")
    def test_latest_price(
        self,
        mock_market_repo_cls: MagicMock,
        mock_company_repo_cls: MagicMock,
        mock_stock_repo_cls: MagicMock,
        mock_session: MagicMock,
        sample_price_bars: list[PriceBar],
    ) -> None:
        """Test Stock latest_price property."""
        mock_stock_repo = MagicMock()
        mock_stock_repo.daily_quotes_recent.return_value = sample_price_bars
        mock_stock_repo_cls.return_value = mock_stock_repo

        stock = Stock("7203", session=mock_session)
        latest = stock.latest_price

        assert latest is not None
        assert latest.close == Decimal("2570")

    @patch("pyjquants.entities.stock.StockRepository")
    @patch("pyjquants.entities.stock.CompanyRepository")
    @patch("pyjquants.entities.stock.MarketRepository")
    def test_latest_price_none(
        self,
        mock_market_repo_cls: MagicMock,
        mock_company_repo_cls: MagicMock,
        mock_stock_repo_cls: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test Stock latest_price returns None when no data."""
        mock_stock_repo = MagicMock()
        mock_stock_repo.daily_quotes_recent.return_value = []
        mock_stock_repo_cls.return_value = mock_stock_repo

        stock = Stock("7203", session=mock_session)
        latest = stock.latest_price

        assert latest is None

    @patch("pyjquants.entities.stock.StockRepository")
    @patch("pyjquants.entities.stock.CompanyRepository")
    @patch("pyjquants.entities.stock.MarketRepository")
    def test_price_bars(
        self,
        mock_market_repo_cls: MagicMock,
        mock_company_repo_cls: MagicMock,
        mock_stock_repo_cls: MagicMock,
        mock_session: MagicMock,
        sample_price_bars: list[PriceBar],
    ) -> None:
        """Test Stock price_bars method."""
        mock_stock_repo = MagicMock()
        mock_stock_repo.daily_quotes.return_value = sample_price_bars
        mock_stock_repo_cls.return_value = mock_stock_repo

        stock = Stock("7203", session=mock_session)
        bars = stock.price_bars(datetime.date(2024, 1, 15), datetime.date(2024, 1, 16))

        assert len(bars) == 2
        assert all(isinstance(bar, PriceBar) for bar in bars)


class TestIndex:
    """Tests for Index entity."""

    def test_init(self, mock_session: MagicMock) -> None:
        """Test Index initialization."""
        index = Index("0000", session=mock_session)

        assert index.code == "0000"

    @patch("pyjquants.entities.index.IndexRepository")
    def test_str(
        self,
        mock_repo_cls: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test Index string representation."""
        mock_repo = MagicMock()
        mock_repo.index_info.return_value = [MagicMock(short_name="TOPIX")]
        mock_repo_cls.return_value = mock_repo

        index = Index("0000", session=mock_session)

        assert str(index) == "TOPIX"

    def test_equality(self, mock_session: MagicMock) -> None:
        """Test Index equality."""
        idx1 = Index("0000", session=mock_session)
        idx2 = Index("0000", session=mock_session)
        idx3 = Index("0001", session=mock_session)

        assert idx1 == idx2
        assert idx1 != idx3
        assert idx1 == "0000"

    def test_hash(self, mock_session: MagicMock) -> None:
        """Test Index can be used in sets."""
        idx1 = Index("0000", session=mock_session)
        idx2 = Index("0000", session=mock_session)

        idx_set = {idx1, idx2}
        assert len(idx_set) == 1

    @patch("pyjquants.entities.index._get_global_session")
    @patch("pyjquants.entities.index.IndexRepository")
    def test_topix(
        self,
        mock_repo_cls: MagicMock,
        mock_get_session: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test Index.topix() class method."""
        mock_get_session.return_value = mock_session

        topix = Index.topix()

        assert topix.code == "0000"
