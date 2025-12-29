"""Index data repository."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.models.price import PriceBar
from pyjquants.repositories.base import BaseRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class IndexRepository(BaseRepository):
    """Repository for index data."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def indices(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[PriceBar]:
        """
        Fetch index price data.

        Args:
            code: Index code (optional)
            start: Start date
            end: End date

        Returns:
            List of PriceBar objects
        """
        params: dict[str, str] = {}
        if code:
            params["code"] = code
        if start:
            params["from"] = start.strftime("%Y%m%d")
        if end:
            params["to"] = end.strftime("%Y%m%d")

        price_bars: list[PriceBar] = []
        for item in self._session.get_paginated("/indices", params, data_key="indices"):
            try:
                price_bar = PriceBar.model_validate(item)
                price_bars.append(price_bar)
            except Exception:
                continue

        return price_bars

    def indices_recent(self, code: str, days: int = 30) -> list[PriceBar]:
        """
        Fetch recent index prices.

        Args:
            code: Index code
            days: Number of days (default 30)

        Returns:
            List of PriceBar objects
        """
        end = date.today()
        start = end - timedelta(days=days + 15)  # Buffer for holidays
        quotes = self.indices(code=code, start=start, end=end)
        return quotes[-days:] if len(quotes) > days else quotes

    def indices_as_dataframe(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch index prices as DataFrame.

        Returns:
            DataFrame with price data
        """
        price_bars = self.indices(code=code, start=start, end=end)
        if not price_bars:
            return pd.DataFrame()

        data = [pb.to_dict() for pb in price_bars]
        df = pd.DataFrame(data)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def topix(self, start: date | None = None, end: date | None = None) -> list[PriceBar]:
        """
        Fetch TOPIX index data.

        Args:
            start: Start date
            end: End date

        Returns:
            List of PriceBar objects
        """
        params: dict[str, str] = {}
        if start:
            params["from"] = start.strftime("%Y%m%d")
        if end:
            params["to"] = end.strftime("%Y%m%d")

        price_bars: list[PriceBar] = []
        for item in self._session.get_paginated(
            "/indices/topix", params, data_key="topix"
        ):
            try:
                price_bar = PriceBar.model_validate(item)
                price_bars.append(price_bar)
            except Exception:
                continue

        return price_bars

    def topix_as_dataframe(
        self, start: date | None = None, end: date | None = None
    ) -> pd.DataFrame:
        """
        Fetch TOPIX data as DataFrame.

        Returns:
            DataFrame with TOPIX data
        """
        price_bars = self.topix(start=start, end=end)
        if not price_bars:
            return pd.DataFrame()

        data = [pb.to_dict() for pb in price_bars]
        df = pd.DataFrame(data)
        df = df.sort_values("date").reset_index(drop=True)
        return df
