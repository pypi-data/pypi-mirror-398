"""Universe collection class for filterable stock collections."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.core.session import _get_global_session
from pyjquants.entities.stock import Stock
from pyjquants.models.company import Sector
from pyjquants.models.enums import MarketSegment
from pyjquants.repositories.company import CompanyRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class Universe:
    """
    Filterable stock collection with method chaining.

    Usage:
        universe = Universe.all()
        tech = universe.filter_by_sector(Sector.TECHNOLOGY).head(20)
    """

    def __init__(self, stocks: list[Stock], session: Session | None = None) -> None:
        """
        Initialize Universe with a list of stocks.

        Args:
            stocks: List of Stock objects
            session: Optional session
        """
        self._stocks = stocks
        self._session = session or _get_global_session()

    # === FACTORY METHODS ===

    @classmethod
    def all(cls, session: Session | None = None) -> Universe:
        """Get universe of all listed stocks."""
        session = session or _get_global_session()
        company_repo = CompanyRepository(session)
        infos = company_repo.listed_info_all()
        stocks = [Stock(info.code, session) for info in infos]
        return cls(stocks, session)

    @classmethod
    def from_codes(cls, codes: list[str], session: Session | None = None) -> Universe:
        """Create universe from stock codes."""
        session = session or _get_global_session()
        stocks = [Stock(code, session) for code in codes]
        return cls(stocks, session)

    # === FILTERING ===

    def filter(self, predicate: Callable[[Stock], bool]) -> Universe:
        """Filter stocks by custom predicate."""
        filtered = [s for s in self._stocks if predicate(s)]
        return Universe(filtered, self._session)

    def filter_by_sector(self, sector: Sector | str) -> Universe:
        """Filter stocks by 33-sector classification."""
        if isinstance(sector, str):
            return self.filter(
                lambda s: s.sector_33.code == sector or s.sector_33.name == sector
            )
        return self.filter(lambda s: s.sector_33 == sector)

    def filter_by_sector_17(self, sector: Sector | str) -> Universe:
        """Filter stocks by 17-sector classification."""
        if isinstance(sector, str):
            return self.filter(
                lambda s: s.sector_17.code == sector or s.sector_17.name == sector
            )
        return self.filter(lambda s: s.sector_17 == sector)

    def filter_by_market(self, segment: MarketSegment | str) -> Universe:
        """Filter stocks by market segment."""
        if isinstance(segment, str):
            return self.filter(lambda s: s.market_segment.value == segment)
        return self.filter(lambda s: s.market_segment == segment)

    def filter_by_code(self, codes: list[str]) -> Universe:
        """Filter stocks by code list."""
        code_set = set(codes)
        return self.filter(lambda s: s.code in code_set)

    # === SORTING ===

    def sort_by(self, key: str, ascending: bool = True) -> Universe:
        """
        Sort stocks by attribute.

        Args:
            key: Attribute name to sort by (e.g., "code", "name")
            ascending: Sort order

        Returns:
            New sorted Universe
        """

        def get_sort_key(stock: Stock) -> str:
            return getattr(stock, key, "")

        sorted_stocks = sorted(self._stocks, key=get_sort_key, reverse=not ascending)
        return Universe(sorted_stocks, self._session)

    # === SLICING ===

    def head(self, n: int) -> Universe:
        """Get first N stocks."""
        return Universe(self._stocks[:n], self._session)

    def tail(self, n: int) -> Universe:
        """Get last N stocks."""
        return Universe(self._stocks[-n:], self._session)

    # === DATA ACCESS ===

    @property
    def prices(self) -> pd.DataFrame:
        """Recent 30 days for all stocks in universe (wide format)."""
        if not self._stocks:
            return pd.DataFrame()

        # Collect prices for each stock
        dfs = []
        for stock in self._stocks:
            df = stock.prices.copy()
            if not df.empty:
                df = df[["date", "close"]].copy()
                df = df.rename(columns={"close": stock.code})
                dfs.append(df.set_index("date"))

        if not dfs:
            return pd.DataFrame()

        # Merge all DataFrames
        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how="outer")

        return result.reset_index()

    def prices_between(self, start: date, end: date) -> pd.DataFrame:
        """Price data for custom date range (wide format)."""
        if not self._stocks:
            return pd.DataFrame()

        dfs = []
        for stock in self._stocks:
            df = stock.prices_between(start, end)
            if not df.empty:
                df = df[["date", "close"]].copy()
                df = df.rename(columns={"close": stock.code})
                dfs.append(df.set_index("date"))

        if not dfs:
            return pd.DataFrame()

        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how="outer")

        return result.reset_index()

    def returns_between(self, start: date, end: date) -> pd.DataFrame:
        """Calculate returns for custom date range."""
        prices = self.prices_between(start, end)
        if prices.empty:
            return pd.DataFrame()

        # Calculate returns
        returns = prices.set_index("date").pct_change().dropna()
        return returns.reset_index()

    # === CONVERSION ===

    def to_list(self) -> list[Stock]:
        """Get stocks as list."""
        return list(self._stocks)

    def codes(self) -> list[str]:
        """Get stock codes."""
        return [s.code for s in self._stocks]

    # === MAGIC METHODS ===

    def __iter__(self) -> Iterator[Stock]:
        return iter(self._stocks)

    def __len__(self) -> int:
        return len(self._stocks)

    def __getitem__(self, index: int) -> Stock:
        return self._stocks[index]

    def __repr__(self) -> str:
        return f"Universe({len(self._stocks)} stocks)"
