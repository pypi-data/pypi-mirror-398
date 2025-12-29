"""Company and sector data models."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import Field, field_validator

from pyjquants.models.base import BaseModel
from pyjquants.models.enums import MarketSegment


class Sector(BaseModel):
    """Sector classification."""

    code: str
    name: str
    name_english: str | None = None

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Sector({self.code}: {self.name})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sector):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other or self.name == other
        return False

    def __hash__(self) -> int:
        return hash(self.code)


class StockInfo(BaseModel):
    """Listed company basic information."""

    code: str = Field(alias="Code")
    company_name: str = Field(alias="CompanyName")
    company_name_english: str | None = Field(alias="CompanyNameEnglish", default=None)

    sector_17_code: str = Field(alias="Sector17Code")
    sector_17_name: str = Field(alias="Sector17CodeName")
    sector_33_code: str = Field(alias="Sector33Code")
    sector_33_name: str = Field(alias="Sector33CodeName")

    market_code: str = Field(alias="MarketCode")
    market_name: str = Field(alias="MarketCodeName")

    scale_category: str | None = Field(alias="ScaleCategory", default=None)
    listing_date: datetime.date | None = Field(alias="Date", default=None)

    @field_validator("listing_date", mode="before")
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

    @property
    def sector_17(self) -> Sector:
        """Get 17-sector classification."""
        return Sector(code=self.sector_17_code, name=self.sector_17_name)

    @property
    def sector_33(self) -> Sector:
        """Get 33-sector classification."""
        return Sector(code=self.sector_33_code, name=self.sector_33_name)

    @property
    def market_segment(self) -> MarketSegment:
        """Get market segment."""
        return MarketSegment.from_code(self.market_code)

    def __repr__(self) -> str:
        return f"StockInfo({self.code}: {self.company_name})"


# Predefined sectors for convenience
class Sector17:
    """17-sector classification constants."""

    FOODS = Sector(code="1", name="食品", name_english="Foods")
    ENERGY_RESOURCES = Sector(code="2", name="エネルギー資源", name_english="Energy Resources")
    CONSTRUCTION_MATERIALS = Sector(
        code="3", name="建設・資材", name_english="Construction & Materials"
    )
    RAW_MATERIALS_CHEMICALS = Sector(
        code="4", name="素材・化学", name_english="Raw Materials & Chemicals"
    )
    PHARMACEUTICALS = Sector(code="5", name="医薬品", name_english="Pharmaceuticals")
    AUTOMOBILES_TRANSPORTATION = Sector(
        code="6", name="自動車・輸送機", name_english="Automobiles & Transportation Equipment"
    )
    STEEL_NONFERROUS = Sector(
        code="7", name="鉄鋼・非鉄", name_english="Steel & Nonferrous Metals"
    )
    MACHINERY = Sector(code="8", name="機械", name_english="Machinery")
    ELECTRIC_PRECISION = Sector(
        code="9", name="電機・精密", name_english="Electric Appliances & Precision Instruments"
    )
    IT_SERVICES = Sector(
        code="10", name="情報通信・サービスその他", name_english="IT & Services, Others"
    )
    ELECTRIC_GAS = Sector(code="11", name="電気・ガス", name_english="Electric Power & Gas")
    TRANSPORTATION_LOGISTICS = Sector(
        code="12", name="運輸・物流", name_english="Transportation & Logistics"
    )
    COMMERCE_WHOLESALE = Sector(code="13", name="商社・卸売", name_english="Commerce & Wholesale")
    RETAIL = Sector(code="14", name="小売", name_english="Retail")
    BANKS = Sector(code="15", name="銀行", name_english="Banks")
    FINANCE_EXCL_BANKS = Sector(
        code="16", name="金融（除く銀行）", name_english="Financials (ex Banks)"
    )
    REAL_ESTATE = Sector(code="17", name="不動産", name_english="Real Estate")
