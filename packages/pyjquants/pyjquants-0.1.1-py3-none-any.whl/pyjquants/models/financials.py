"""Financial statement and dividend data models."""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from pyjquants.models.base import BaseModel


class FinancialStatement(BaseModel):
    """Financial statement data."""

    # Identifiers
    code: str = Field(alias="LocalCode")
    disclosure_date: datetime.date = Field(alias="DisclosedDate")

    # Fiscal period info
    type_of_document: str | None = Field(alias="TypeOfDocument", default=None)
    fiscal_year_end_basic: str | None = Field(alias="FiscalYearEndBasic", default=None)
    type_of_current_period: str | None = Field(alias="TypeOfCurrentPeriod", default=None)

    # Current period figures
    net_sales: Decimal | None = Field(alias="NetSales", default=None)
    operating_profit: Decimal | None = Field(alias="OperatingProfit", default=None)
    ordinary_profit: Decimal | None = Field(alias="OrdinaryProfit", default=None)
    profit: Decimal | None = Field(alias="Profit", default=None)  # Net income

    # Per share data
    earnings_per_share: Decimal | None = Field(alias="EarningsPerShare", default=None)
    diluted_earnings_per_share: Decimal | None = Field(
        alias="DilutedEarningsPerShare", default=None
    )
    book_value_per_share: Decimal | None = Field(alias="BookValuePerShare", default=None)

    # Balance sheet items
    total_assets: Decimal | None = Field(alias="TotalAssets", default=None)
    equity: Decimal | None = Field(alias="Equity", default=None)
    equity_to_asset_ratio: float | None = Field(alias="EquityToAssetRatio", default=None)

    # Ratios
    roe: float | None = Field(alias="ROE", default=None)
    roa: float | None = Field(alias="ROA", default=None)

    # Forecast
    forecast_net_sales: Decimal | None = Field(alias="ForecastNetSales", default=None)
    forecast_operating_profit: Decimal | None = Field(
        alias="ForecastOperatingProfit", default=None
    )
    forecast_ordinary_profit: Decimal | None = Field(
        alias="ForecastOrdinaryProfit", default=None
    )
    forecast_profit: Decimal | None = Field(alias="ForecastProfit", default=None)
    forecast_earnings_per_share: Decimal | None = Field(
        alias="ForecastEarningsPerShare", default=None
    )

    # Dividends
    forecast_dividend_per_share_annual: Decimal | None = Field(
        alias="ForecastDividendPerShareAnnual", default=None
    )

    @field_validator("disclosure_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            if "-" in v:
                return datetime.date.fromisoformat(v)
            return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        raise ValueError(f"Cannot parse date: {v}")

    @field_validator(
        "net_sales",
        "operating_profit",
        "ordinary_profit",
        "profit",
        "earnings_per_share",
        "diluted_earnings_per_share",
        "book_value_per_share",
        "total_assets",
        "equity",
        "forecast_net_sales",
        "forecast_operating_profit",
        "forecast_ordinary_profit",
        "forecast_profit",
        "forecast_earnings_per_share",
        "forecast_dividend_per_share_annual",
        mode="before",
    )
    @classmethod
    def parse_decimal(cls, v: Any) -> Decimal | None:
        if v is None or v == "":
            return None
        return Decimal(str(v))

    @field_validator("equity_to_asset_ratio", "roe", "roa", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> float | None:
        if v is None or v == "":
            return None
        return float(v)

    @property
    def eps(self) -> Decimal | None:
        """Alias for earnings per share."""
        return self.earnings_per_share

    @property
    def bps(self) -> Decimal | None:
        """Alias for book value per share."""
        return self.book_value_per_share

    @property
    def net_income(self) -> Decimal | None:
        """Alias for profit (net income)."""
        return self.profit


class Dividend(BaseModel):
    """Dividend data."""

    code: str = Field(alias="Code")
    announcement_date: datetime.date | None = Field(alias="AnnouncementDate", default=None)
    record_date: datetime.date = Field(alias="RecordDate")
    ex_dividend_date: datetime.date | None = Field(alias="ExDividendDate", default=None)
    payment_date: datetime.date | None = Field(alias="PaymentDate", default=None)

    dividend_per_share: Decimal = Field(alias="DividendPerShare")
    forecast_dividend_per_share: Decimal | None = Field(
        alias="ForecastDividendPerShare", default=None
    )

    @field_validator(
        "announcement_date",
        "record_date",
        "ex_dividend_date",
        "payment_date",
        mode="before",
    )
    @classmethod
    def parse_date(cls, v: Any) -> datetime.date | None:
        if v is None or v == "":
            return None
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            if "-" in v:
                return datetime.date.fromisoformat(v)
            return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        return None

    @field_validator("dividend_per_share", "forecast_dividend_per_share", mode="before")
    @classmethod
    def parse_decimal(cls, v: Any) -> Decimal | None:
        if v is None or v == "":
            return None
        return Decimal(str(v))


class EarningsAnnouncement(BaseModel):
    """Earnings announcement calendar entry."""

    code: str = Field(alias="Code")
    company_name: str = Field(alias="CompanyName")
    announcement_date: datetime.date = Field(alias="Date")
    fiscal_quarter: str | None = Field(alias="FiscalQuarter", default=None)

    @field_validator("announcement_date", mode="before")
    @classmethod
    def parse_announcement_date(cls, v: Any) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            if "-" in v:
                return datetime.date.fromisoformat(v)
            return datetime.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        raise ValueError(f"Cannot parse date: {v}")
