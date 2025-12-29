"""Company and financial data repository."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.models.company import StockInfo
from pyjquants.models.financials import Dividend, EarningsAnnouncement, FinancialStatement
from pyjquants.repositories.base import BaseRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class CompanyRepository(BaseRepository):
    """Repository for company and financial data."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def listed_info(
        self, code: str | None = None, specific_date: date | None = None
    ) -> list[StockInfo]:
        """
        Fetch listed company information.

        Args:
            code: Stock code (optional, fetches all if not specified)
            specific_date: Date for the information

        Returns:
            List of StockInfo objects
        """
        params: dict[str, str] = {}
        if code:
            params["code"] = code
        if specific_date:
            params["date"] = specific_date.strftime("%Y%m%d")

        response = self._session.get("/listed/info", params)
        stock_infos: list[StockInfo] = []

        for item in response.get("info", []):
            try:
                stock_info = StockInfo.model_validate(item)
                stock_infos.append(stock_info)
            except Exception:
                continue

        return stock_infos

    def listed_info_all(self, specific_date: date | None = None) -> list[StockInfo]:
        """
        Fetch all listed companies.

        Args:
            specific_date: Date for the information

        Returns:
            List of all StockInfo objects
        """
        return self.listed_info(code=None, specific_date=specific_date)

    def statements(
        self, code: str | None = None, specific_date: date | None = None
    ) -> list[FinancialStatement]:
        """
        Fetch financial statements.

        Args:
            code: Stock code (optional)
            specific_date: Disclosure date

        Returns:
            List of FinancialStatement objects
        """
        params: dict[str, str] = {}
        if code:
            params["code"] = code
        if specific_date:
            params["date"] = specific_date.strftime("%Y%m%d")

        statements: list[FinancialStatement] = []
        for item in self._session.get_paginated(
            "/fins/statements", params, data_key="statements"
        ):
            try:
                statement = FinancialStatement.model_validate(item)
                statements.append(statement)
            except Exception:
                continue

        return statements

    def statements_as_dataframe(
        self, code: str | None = None, specific_date: date | None = None
    ) -> pd.DataFrame:
        """
        Fetch financial statements as DataFrame.

        Returns:
            DataFrame with financial data
        """
        statements = self.statements(code=code, specific_date=specific_date)
        if not statements:
            return pd.DataFrame()

        data = [s.model_dump() for s in statements]
        return pd.DataFrame(data)

    def dividends(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[Dividend]:
        """
        Fetch dividend data.

        Args:
            code: Stock code (optional)
            start: Start date
            end: End date

        Returns:
            List of Dividend objects
        """
        params: dict[str, str] = {}
        if code:
            params["code"] = code
        if start:
            params["from"] = start.strftime("%Y%m%d")
        if end:
            params["to"] = end.strftime("%Y%m%d")

        dividends: list[Dividend] = []
        for item in self._session.get_paginated(
            "/fins/dividend", params, data_key="dividend"
        ):
            try:
                dividend = Dividend.model_validate(item)
                dividends.append(dividend)
            except Exception:
                continue

        return dividends

    def dividends_as_dataframe(
        self,
        code: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch dividends as DataFrame.

        Returns:
            DataFrame with dividend data
        """
        dividends = self.dividends(code=code, start=start, end=end)
        if not dividends:
            return pd.DataFrame()

        data = [d.model_dump() for d in dividends]
        return pd.DataFrame(data)

    def announcements(self) -> list[EarningsAnnouncement]:
        """
        Fetch earnings announcements calendar.

        Returns:
            List of EarningsAnnouncement objects
        """
        response = self._session.get("/fins/announcement")
        announcements: list[EarningsAnnouncement] = []

        for item in response.get("announcement", []):
            try:
                announcement = EarningsAnnouncement.model_validate(item)
                announcements.append(announcement)
            except Exception:
                continue

        return announcements

    def next_earnings_date(self, code: str) -> date | None:
        """
        Get next earnings announcement date for a stock.

        Args:
            code: Stock code

        Returns:
            Next earnings date or None if not found
        """
        announcements = self.announcements()
        today = date.today()

        for ann in announcements:
            if ann.code == code and ann.announcement_date >= today:
                return ann.announcement_date

        return None
