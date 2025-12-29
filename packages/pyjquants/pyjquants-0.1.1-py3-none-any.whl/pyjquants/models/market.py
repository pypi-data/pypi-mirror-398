"""Market data models."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import Field, field_validator

from pyjquants.models.base import BaseModel


class TradingCalendarDay(BaseModel):
    """Single trading calendar day."""

    date: datetime.date = Field(alias="Date")
    holiday_division: str = Field(alias="HolidayDivision")

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            if "-" in v:
                return datetime.date.fromisoformat(v)
            return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        raise ValueError(f"Cannot parse date: {v}")

    @property
    def is_trading_day(self) -> bool:
        """Check if this is a trading day."""
        # HolidayDivision: 0 = trading day, 1 = holiday/non-trading day
        return self.holiday_division == "0"

    @property
    def is_holiday(self) -> bool:
        """Check if this is a holiday."""
        return not self.is_trading_day


class MarginInterest(BaseModel):
    """Margin trading interest data."""

    code: str = Field(alias="Code")
    date: datetime.date = Field(alias="Date")

    # Margin buying
    margin_buying_balance: int | None = Field(alias="MarginBuyingBalance", default=None)
    margin_buying_value: float | None = Field(alias="MarginBuyingValue", default=None)
    margin_buying_new: int | None = Field(alias="MarginBuyingNew", default=None)
    margin_buying_repay: int | None = Field(alias="MarginBuyingRepay", default=None)

    # Margin selling
    margin_selling_balance: int | None = Field(alias="MarginSellingBalance", default=None)
    margin_selling_value: float | None = Field(alias="MarginSellingValue", default=None)
    margin_selling_new: int | None = Field(alias="MarginSellingNew", default=None)
    margin_selling_repay: int | None = Field(alias="MarginSellingRepay", default=None)

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            if "-" in v:
                return datetime.date.fromisoformat(v)
            return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        raise ValueError(f"Cannot parse date: {v}")


class ShortSelling(BaseModel):
    """Short selling data."""

    date: datetime.date = Field(alias="Date")
    sector_33_code: str = Field(alias="Sector33Code")

    selling_value: float | None = Field(alias="SellingValue", default=None)
    selling_value_with_restriction: float | None = Field(
        alias="SellingValueWithRestriction", default=None
    )
    selling_value_without_restriction: float | None = Field(
        alias="SellingValueWithoutRestriction", default=None
    )

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            if "-" in v:
                return datetime.date.fromisoformat(v)
            return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        raise ValueError(f"Cannot parse date: {v}")
