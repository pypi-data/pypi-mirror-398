"""Index entity class."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from pyjquants.core.session import _get_global_session
from pyjquants.models.price import PriceBar
from pyjquants.repositories.index import IndexRepository

if TYPE_CHECKING:
    from pyjquants.core.session import Session


# Known index codes
TOPIX_CODE = "0000"
NIKKEI225_CODE = "0001"


class Index:
    """
    Market index with all data as attributes.

    Usage:
        topix = Index.topix()
        topix.code      # "0000"
        topix.name      # "TOPIX"
        topix.prices    # Recent 30 days
    """

    # Known indices
    _KNOWN_INDICES = {
        TOPIX_CODE: "TOPIX",
        NIKKEI225_CODE: "Nikkei 225",
    }

    def __init__(self, code: str, name: str | None = None, session: Session | None = None) -> None:
        """
        Initialize Index.

        Args:
            code: Index code
            name: Index name (optional)
            session: Optional session (uses global session if not provided)
        """
        self.code = code
        self._name = name or self._KNOWN_INDICES.get(code)
        self._session = session or _get_global_session()
        self._index_repo = IndexRepository(self._session)

    @property
    def name(self) -> str:
        """Index name."""
        return self._name or self.code

    # === PRICE DATA ===

    @property
    def prices(self) -> pd.DataFrame:
        """Recent 30 days of price data."""
        if self.code == TOPIX_CODE:
            return self._index_repo.topix_as_dataframe().tail(30)
        return self._index_repo.indices_as_dataframe(code=self.code).tail(30)

    @property
    def latest_price(self) -> PriceBar | None:
        """Most recent price bar."""
        if self.code == TOPIX_CODE:
            bars = self._index_repo.topix()
        else:
            bars = self._index_repo.indices_recent(code=self.code, days=1)
        return bars[-1] if bars else None

    def prices_between(self, start: date, end: date) -> pd.DataFrame:
        """Price data for custom date range."""
        if self.code == TOPIX_CODE:
            return self._index_repo.topix_as_dataframe(start=start, end=end)
        return self._index_repo.indices_as_dataframe(code=self.code, start=start, end=end)

    def price_bars(self, start: date, end: date) -> list[PriceBar]:
        """Returns typed PriceBar objects instead of DataFrame."""
        if self.code == TOPIX_CODE:
            return self._index_repo.topix(start=start, end=end)
        return self._index_repo.indices(code=self.code, start=start, end=end)

    # === FACTORY METHODS ===

    @classmethod
    def topix(cls, session: Session | None = None) -> Index:
        """Get TOPIX index."""
        return cls(code=TOPIX_CODE, name="TOPIX", session=session)

    @classmethod
    def nikkei225(cls, session: Session | None = None) -> Index:
        """Get Nikkei 225 index."""
        return cls(code=NIKKEI225_CODE, name="Nikkei 225", session=session)

    @classmethod
    def all(cls, session: Session | None = None) -> list[Index]:
        """Get all available indices."""
        session = session or _get_global_session()
        # Return known indices
        return [
            cls(code=code, name=name, session=session)
            for code, name in cls._KNOWN_INDICES.items()
        ]

    # === MAGIC METHODS ===

    def __repr__(self) -> str:
        return f"Index({self.code}: {self.name})"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Index):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other
        return False

    def __hash__(self) -> int:
        return hash(self.code)
