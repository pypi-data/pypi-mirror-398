"""Base model configuration for pyjquants."""

from __future__ import annotations

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        frozen=True,  # Immutable by default
        extra="ignore",  # Ignore extra fields from API
        populate_by_name=True,  # Allow both alias and field name
    )
