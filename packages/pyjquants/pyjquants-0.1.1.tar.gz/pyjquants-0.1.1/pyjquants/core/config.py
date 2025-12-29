"""Configuration loading from environment variables and TOML files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Try to import tomllib (Python 3.11+) or tomli
import sys
from types import ModuleType

_tomllib: ModuleType | None = None
if sys.version_info >= (3, 11):
    import tomllib
    _tomllib = tomllib
else:
    try:
        import tomli as _tomli_module
        _tomllib = _tomli_module
    except ImportError:
        pass


@dataclass
class JQuantsConfig:
    """Configuration for J-Quants API."""

    mail_address: str | None = None
    password: str | None = None
    refresh_token: str | None = None

    # Cache settings
    cache_enabled: bool = True
    cache_directory: Path | None = None
    cache_ttl_seconds: int = 3600

    # Rate limiting
    requests_per_minute: int = 60

    @classmethod
    def from_environment(cls) -> JQuantsConfig:
        """Load configuration from environment variables."""
        cache_dir = os.environ.get("JQUANTS_CACHE_DIR")
        return cls(
            mail_address=os.environ.get("JQUANTS_MAIL_ADDRESS"),
            password=os.environ.get("JQUANTS_PASSWORD"),
            refresh_token=os.environ.get("JQUANTS_REFRESH_TOKEN"),
            cache_enabled=os.environ.get("JQUANTS_CACHE_ENABLED", "true").lower() == "true",
            cache_directory=Path(cache_dir) if cache_dir else None,
            cache_ttl_seconds=int(os.environ.get("JQUANTS_CACHE_TTL", "3600")),
            requests_per_minute=int(os.environ.get("JQUANTS_RATE_LIMIT", "60")),
        )

    @classmethod
    def from_toml(cls, path: Path | None = None) -> JQuantsConfig:
        """Load configuration from TOML file."""
        if _tomllib is None:
            raise ImportError(
                "tomllib/tomli is required for TOML config. "
                "Install with: pip install tomli (Python < 3.11)"
            )

        if path is None:
            # Try default locations
            default_paths = [
                Path.home() / ".jquants" / "config.toml",
                Path.home() / ".config" / "jquants" / "config.toml",
                Path(".jquants.toml"),
            ]
            for default_path in default_paths:
                if default_path.exists():
                    path = default_path
                    break

        if path is None or not path.exists():
            return cls()

        with open(path, "rb") as f:
            data = _tomllib.load(f)

        credentials = data.get("credentials", {})
        cache = data.get("cache", {})
        rate_limit = data.get("rate_limit", {})

        cache_dir = cache.get("directory")
        return cls(
            mail_address=credentials.get("mail_address"),
            password=credentials.get("password"),
            refresh_token=credentials.get("refresh_token"),
            cache_enabled=cache.get("enabled", True),
            cache_directory=Path(cache_dir).expanduser() if cache_dir else None,
            cache_ttl_seconds=cache.get("ttl_seconds", 3600),
            requests_per_minute=rate_limit.get("requests_per_minute", 60),
        )

    @classmethod
    def load(cls, config_path: Path | None = None) -> JQuantsConfig:
        """
        Load configuration with priority: environment > TOML file > defaults.

        Environment variables always take precedence.
        """
        # Start with TOML config or defaults
        config = cls.from_toml(config_path)

        # Override with environment variables
        env_config = cls.from_environment()

        if env_config.mail_address:
            config.mail_address = env_config.mail_address
        if env_config.password:
            config.password = env_config.password
        if env_config.refresh_token:
            config.refresh_token = env_config.refresh_token
        if os.environ.get("JQUANTS_CACHE_ENABLED"):
            config.cache_enabled = env_config.cache_enabled
        if os.environ.get("JQUANTS_CACHE_DIR"):
            config.cache_directory = env_config.cache_directory
        if os.environ.get("JQUANTS_CACHE_TTL"):
            config.cache_ttl_seconds = env_config.cache_ttl_seconds
        if os.environ.get("JQUANTS_RATE_LIMIT"):
            config.requests_per_minute = env_config.requests_per_minute

        return config

    def has_credentials(self) -> bool:
        """Check if credentials are available."""
        return bool(
            self.refresh_token or (self.mail_address and self.password)
        )
