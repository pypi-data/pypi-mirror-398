"""Stock price data repository."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.models.price import PriceBar
from pyjquants.repositories.base import BaseRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class StockRepository(BaseRepository):
    """Repository for stock price data."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def daily_quotes(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
        specific_date: date | None = None,
    ) -> list[PriceBar]:
        """
        Fetch daily OHLCV quotes.

        Args:
            code: Stock code (optional, fetches all if not specified)
            start: Start date
            end: End date
            specific_date: Fetch for a specific date only

        Returns:
            List of PriceBar objects
        """
        params: dict[str, str] = {}

        if code:
            params["code"] = code
        if specific_date:
            params["date"] = specific_date.strftime("%Y%m%d")
        else:
            if start:
                params["from"] = start.strftime("%Y%m%d")
            if end:
                params["to"] = end.strftime("%Y%m%d")

        # Use paginated endpoint for bulk fetches
        price_bars: list[PriceBar] = []
        for item in self._session.get_paginated(
            "/prices/daily_quotes", params, data_key="daily_quotes"
        ):
            try:
                price_bar = PriceBar.model_validate(item)
                price_bars.append(price_bar)
            except Exception:
                continue  # Skip invalid data

        return price_bars

    def daily_quotes_recent(self, code: str, days: int = 30) -> list[PriceBar]:
        """
        Fetch recent daily quotes for a stock.

        Args:
            code: Stock code
            days: Number of days to fetch (default 30)

        Returns:
            List of PriceBar objects
        """
        end = date.today()
        # Add buffer for weekends/holidays
        start = end - timedelta(days=days + 15)
        quotes = self.daily_quotes(code=code, start=start, end=end)
        # Return only the most recent N trading days
        return quotes[-days:] if len(quotes) > days else quotes

    def daily_quotes_as_dataframe(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch daily quotes as a pandas DataFrame.

        Args:
            code: Stock code (optional)
            start: Start date
            end: End date

        Returns:
            DataFrame with price data
        """
        price_bars = self.daily_quotes(code=code, start=start, end=end)
        if not price_bars:
            return pd.DataFrame()

        data = [pb.to_dict() for pb in price_bars]
        df = pd.DataFrame(data)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def prices_am(self, code: str | None = None) -> list[PriceBar]:
        """
        Fetch morning session prices.

        Args:
            code: Stock code (optional)

        Returns:
            List of PriceBar objects
        """
        params: dict[str, str] = {}
        if code:
            params["code"] = code

        response = self._session.get("/prices/prices_am", params)
        price_bars: list[PriceBar] = []

        for item in response.get("prices_am", []):
            try:
                price_bar = PriceBar.model_validate(item)
                price_bars.append(price_bar)
            except Exception:
                continue

        return price_bars
