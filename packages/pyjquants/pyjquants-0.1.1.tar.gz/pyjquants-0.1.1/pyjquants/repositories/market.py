"""Market data repository."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.models.company import Sector
from pyjquants.models.market import MarginInterest, ShortSelling, TradingCalendarDay
from pyjquants.repositories.base import BaseRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class MarketRepository(BaseRepository):
    """Repository for market-wide data."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def trading_calendar(
        self,
        start: date | None = None,
        end: date | None = None,
        holiday_division: str | None = None,
    ) -> list[TradingCalendarDay]:
        """
        Fetch trading calendar.

        Args:
            start: Start date
            end: End date
            holiday_division: Filter by holiday division (0=trading, 1=holiday)

        Returns:
            List of TradingCalendarDay objects
        """
        params: dict[str, str] = {}
        if start:
            params["from"] = start.strftime("%Y%m%d")
        if end:
            params["to"] = end.strftime("%Y%m%d")
        if holiday_division:
            params["holidaydivision"] = holiday_division

        response = self._session.get("/markets/trading_calendar", params)
        calendar: list[TradingCalendarDay] = []

        for item in response.get("trading_calendar", []):
            try:
                day = TradingCalendarDay.model_validate(item)
                calendar.append(day)
            except Exception:
                continue

        return calendar

    def is_trading_day(self, d: date) -> bool:
        """
        Check if a date is a trading day.

        Args:
            d: Date to check

        Returns:
            True if trading day
        """
        calendar = self.trading_calendar(start=d, end=d)
        if calendar:
            return calendar[0].is_trading_day
        return False

    def trading_days(self, start: date, end: date) -> list[date]:
        """
        Get list of trading days in a range.

        Args:
            start: Start date
            end: End date

        Returns:
            List of trading dates
        """
        calendar = self.trading_calendar(start=start, end=end)
        return [day.date for day in calendar if day.is_trading_day]

    def sectors_17(self) -> list[Sector]:
        """
        Get 17-sector classification list.

        Returns:
            List of Sector objects
        """
        # This data is static, could be cached indefinitely
        response = self._session.get("/listed/info")

        # Extract unique sectors from all listed companies
        sectors_map: dict[str, Sector] = {}
        for item in response.get("info", []):
            code = item.get("Sector17Code", "")
            name = item.get("Sector17CodeName", "")
            if code and name and code not in sectors_map:
                sectors_map[code] = Sector(code=code, name=name)

        return sorted(sectors_map.values(), key=lambda s: s.code)

    def sectors_33(self) -> list[Sector]:
        """
        Get 33-sector classification list.

        Returns:
            List of Sector objects
        """
        response = self._session.get("/listed/info")

        sectors_map: dict[str, Sector] = {}
        for item in response.get("info", []):
            code = item.get("Sector33Code", "")
            name = item.get("Sector33CodeName", "")
            if code and name and code not in sectors_map:
                sectors_map[code] = Sector(code=code, name=name)

        return sorted(sectors_map.values(), key=lambda s: s.code)

    def margin_interest(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[MarginInterest]:
        """
        Fetch margin trading interest data.

        Args:
            code: Stock code (optional)
            start: Start date
            end: End date

        Returns:
            List of MarginInterest objects
        """
        params: dict[str, str] = {}
        if code:
            params["code"] = code
        if start:
            params["from"] = start.strftime("%Y%m%d")
        if end:
            params["to"] = end.strftime("%Y%m%d")

        margin_data: list[MarginInterest] = []
        for item in self._session.get_paginated(
            "/markets/weekly_margin_interest", params, data_key="weekly_margin_interest"
        ):
            try:
                margin = MarginInterest.model_validate(item)
                margin_data.append(margin)
            except Exception:
                continue

        return margin_data

    def margin_interest_as_dataframe(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch margin interest data as DataFrame.

        Returns:
            DataFrame with margin data
        """
        margin_data = self.margin_interest(code=code, start=start, end=end)
        if not margin_data:
            return pd.DataFrame()

        data = [m.model_dump() for m in margin_data]
        return pd.DataFrame(data)

    def short_selling(
        self,
        sector_33_code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[ShortSelling]:
        """
        Fetch short selling data.

        Args:
            sector_33_code: 33-sector code (optional)
            start: Start date
            end: End date

        Returns:
            List of ShortSelling objects
        """
        params: dict[str, str] = {}
        if sector_33_code:
            params["sector33code"] = sector_33_code
        if start:
            params["from"] = start.strftime("%Y%m%d")
        if end:
            params["to"] = end.strftime("%Y%m%d")

        short_data: list[ShortSelling] = []
        for item in self._session.get_paginated(
            "/markets/short_selling", params, data_key="short_selling"
        ):
            try:
                short = ShortSelling.model_validate(item)
                short_data.append(short)
            except Exception:
                continue

        return short_data

    def short_selling_as_dataframe(
        self,
        sector_33_code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch short selling data as DataFrame.

        Returns:
            DataFrame with short selling data
        """
        short_data = self.short_selling(sector_33_code=sector_33_code, start=start, end=end)
        if not short_data:
            return pd.DataFrame()

        data = [s.model_dump() for s in short_data]
        return pd.DataFrame(data)
