"""Market collection class for market-wide data."""

from __future__ import annotations

from datetime import date, timedelta
from functools import cached_property
from typing import TYPE_CHECKING

from pyjquants.core.session import _get_global_session
from pyjquants.models.company import Sector
from pyjquants.models.market import TradingCalendarDay
from pyjquants.repositories.market import MarketRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class Market:
    """
    Market-wide data and utilities. Standalone entity.

    Usage:
        market = Market()
        market.is_trading_day(date(2024, 12, 25))
    """

    def __init__(self, session: Session | None = None) -> None:
        """
        Initialize Market.

        Args:
            session: Optional session (uses global session if not provided)
        """
        self._session = session or _get_global_session()
        self._market_repo = MarketRepository(self._session)

    # === TRADING CALENDAR ===

    def trading_calendar(self, start: date, end: date) -> list[TradingCalendarDay]:
        """Get trading calendar for date range."""
        return self._market_repo.trading_calendar(start=start, end=end)

    def is_trading_day(self, d: date) -> bool:
        """Check if a date is a trading day."""
        return self._market_repo.is_trading_day(d)

    def trading_days(self, start: date, end: date) -> list[date]:
        """Get list of trading days in a range."""
        return self._market_repo.trading_days(start=start, end=end)

    def next_trading_day(self, from_date: date) -> date:
        """Get the next trading day after a given date."""
        # Look ahead up to 10 days to find next trading day
        check_date = from_date + timedelta(days=1)
        for _ in range(10):
            if self.is_trading_day(check_date):
                return check_date
            check_date += timedelta(days=1)
        # If not found within 10 days, return the check date
        return check_date

    def prev_trading_day(self, from_date: date) -> date:
        """Get the previous trading day before a given date."""
        check_date = from_date - timedelta(days=1)
        for _ in range(10):
            if self.is_trading_day(check_date):
                return check_date
            check_date -= timedelta(days=1)
        return check_date

    # === SECTOR DATA ===

    @cached_property
    def sectors_17(self) -> list[Sector]:
        """Get 17-sector classification list."""
        return self._market_repo.sectors_17()

    @cached_property
    def sectors_33(self) -> list[Sector]:
        """Get 33-sector classification list."""
        return self._market_repo.sectors_33()

    def __repr__(self) -> str:
        return "Market()"
