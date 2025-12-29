"""Base repository class for data access."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyjquants.core.session import Session


class BaseRepository:
    """Base class for all repositories."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the session."""
        return self._session
