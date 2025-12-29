"""Stock entity class."""

from __future__ import annotations

from datetime import date
from functools import cached_property
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.core.session import _get_global_session
from pyjquants.models.company import Sector, StockInfo
from pyjquants.models.enums import MarketSegment
from pyjquants.models.price import PriceBar
from pyjquants.repositories.company import CompanyRepository
from pyjquants.repositories.market import MarketRepository
from pyjquants.repositories.stock import StockRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class Stock:
    """
    Stock entity with all data as attributes.
    All attributes are lazy-loaded from API when accessed.

    Usage:
        stock = Stock("7203")
        stock.code          # "7203" (local)
        stock.name          # "Toyota Motor Corporation" (API, cached)
        stock.prices        # Recent 30 days DataFrame (API)
        stock.financials    # Latest financials (API)
    """

    def __init__(self, code: str, session: Session | None = None) -> None:
        """
        Initialize Stock with code.

        Args:
            code: Stock code (4 or 5 digits)
            session: Optional session (uses global session if not provided)
        """
        self.code = code
        self._session = session or _get_global_session()
        self._stock_repo = StockRepository(self._session)
        self._company_repo = CompanyRepository(self._session)
        self._market_repo = MarketRepository(self._session)
        self._info: StockInfo | None = None

    def _load_info(self) -> StockInfo:
        """Load stock info from API."""
        if self._info is None:
            infos = self._company_repo.listed_info(code=self.code)
            if not infos:
                raise ValueError(f"Stock not found: {self.code}")
            self._info = infos[0]
        return self._info

    # === BASIC INFO (lazy-loaded, cached) ===

    @cached_property
    def name(self) -> str:
        """Company name (Japanese)."""
        return self._load_info().company_name

    @cached_property
    def name_english(self) -> str | None:
        """Company name (English)."""
        return self._load_info().company_name_english

    @cached_property
    def sector_17(self) -> Sector:
        """17-sector classification."""
        return self._load_info().sector_17

    @cached_property
    def sector_33(self) -> Sector:
        """33-sector classification."""
        return self._load_info().sector_33

    @cached_property
    def market_segment(self) -> MarketSegment:
        """Market segment (Prime, Standard, Growth)."""
        return self._load_info().market_segment

    @cached_property
    def listing_date(self) -> date | None:
        """Listing date."""
        return self._load_info().listing_date

    # === PRICE DATA ===

    @property
    def prices(self) -> pd.DataFrame:
        """Recent 30 trading days of price data."""
        return self._stock_repo.daily_quotes_as_dataframe(
            code=self.code,
            start=None,
            end=None,
        ).tail(30)

    @property
    def adjusted_prices(self) -> pd.DataFrame:
        """Recent 30 days adjusted for splits/dividends."""
        df = self.prices.copy()
        if df.empty:
            return df
        # Keep only adjusted columns
        return df[
            ["date", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close", "adjusted_volume"]
        ].rename(
            columns={
                "adjusted_open": "open",
                "adjusted_high": "high",
                "adjusted_low": "low",
                "adjusted_close": "close",
                "adjusted_volume": "volume",
            }
        )

    @property
    def latest_price(self) -> PriceBar | None:
        """Most recent price bar."""
        bars = self._stock_repo.daily_quotes_recent(code=self.code, days=1)
        return bars[-1] if bars else None

    def prices_between(self, start: date, end: date) -> pd.DataFrame:
        """Price data for custom date range."""
        return self._stock_repo.daily_quotes_as_dataframe(
            code=self.code, start=start, end=end
        )

    def adjusted_prices_between(self, start: date, end: date) -> pd.DataFrame:
        """Adjusted prices for custom range."""
        df = self.prices_between(start, end)
        if df.empty:
            return df
        return df[
            ["date", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close", "adjusted_volume"]
        ].rename(
            columns={
                "adjusted_open": "open",
                "adjusted_high": "high",
                "adjusted_low": "low",
                "adjusted_close": "close",
                "adjusted_volume": "volume",
            }
        )

    def price_bars(self, start: date, end: date) -> list[PriceBar]:
        """Returns typed PriceBar objects instead of DataFrame."""
        return self._stock_repo.daily_quotes(code=self.code, start=start, end=end)

    # === FINANCIAL DATA ===

    @property
    def financials(self) -> pd.DataFrame:
        """Latest financial statements."""
        return self._company_repo.statements_as_dataframe(code=self.code)

    @property
    def dividends(self) -> pd.DataFrame:
        """Recent dividend history."""
        return self._company_repo.dividends_as_dataframe(code=self.code)

    @property
    def next_earnings(self) -> date | None:
        """Next earnings announcement date."""
        return self._company_repo.next_earnings_date(code=self.code)

    def dividends_between(self, start: date, end: date) -> pd.DataFrame:
        """Dividends for custom range."""
        return self._company_repo.dividends_as_dataframe(code=self.code, start=start, end=end)

    # === MARKET DATA ===

    @property
    def margin_data(self) -> pd.DataFrame:
        """Recent margin trading data."""
        return self._market_repo.margin_interest_as_dataframe(code=self.code)

    @property
    def short_selling(self) -> pd.DataFrame:
        """Recent short selling data (by sector)."""
        return self._market_repo.short_selling_as_dataframe(
            sector_33_code=self.sector_33.code
        )

    def margin_data_between(self, start: date, end: date) -> pd.DataFrame:
        """Margin trading data for custom range."""
        return self._market_repo.margin_interest_as_dataframe(
            code=self.code, start=start, end=end
        )

    def short_selling_between(self, start: date, end: date) -> pd.DataFrame:
        """Short selling data for custom range."""
        return self._market_repo.short_selling_as_dataframe(
            sector_33_code=self.sector_33.code, start=start, end=end
        )

    # === DISCOVERY ===

    @classmethod
    def all(cls, session: Session | None = None) -> list[Stock]:
        """Get all listed stocks."""
        session = session or _get_global_session()
        company_repo = CompanyRepository(session)
        infos = company_repo.listed_info_all()
        return [cls(info.code, session) for info in infos]

    @classmethod
    def search(cls, query: str, session: Session | None = None) -> list[Stock]:
        """Search stocks by name or code."""
        session = session or _get_global_session()
        company_repo = CompanyRepository(session)
        infos = company_repo.listed_info_all()

        query_lower = query.lower()
        matching = [
            info
            for info in infos
            if query_lower in info.code.lower()
            or query_lower in info.company_name.lower()
            or (info.company_name_english and query_lower in info.company_name_english.lower())
        ]

        return [cls(info.code, session) for info in matching]

    # === MAGIC METHODS ===

    def __repr__(self) -> str:
        try:
            return f"Stock({self.code}: {self.name})"
        except Exception:
            return f"Stock({self.code})"

    def __str__(self) -> str:
        return self.code

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Stock):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other
        return False

    def __hash__(self) -> int:
        return hash(self.code)
