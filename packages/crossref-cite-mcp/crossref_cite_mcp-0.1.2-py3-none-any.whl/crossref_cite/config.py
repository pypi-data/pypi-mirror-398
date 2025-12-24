"""Configuration management via environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    # Crossref API
    mailto: str
    user_agent: str

    # Cache
    cache_ttl: int
    cache_backend: Literal["memory", "json"]
    cache_path: Path

    # Logging
    log_level: str


def load_config() -> Config:
    """Load configuration from environment variables with sensible defaults."""
    mailto = os.getenv("CROSSREF_MAILTO", "").strip()
    if not mailto:
        # Log warning but don't fail - polite pool is recommended but not required
        import logging

        logging.getLogger("crossref_cite").warning(
            "CROSSREF_MAILTO not set. Requests will use anonymous pool with lower rate limits."
        )

    user_agent = os.getenv("CROSSREF_USER_AGENT", "crossref-cite-mcp/0.1").strip()

    cache_ttl = int(os.getenv("CROSSREF_CACHE_TTL", "1209600"))  # 14 days

    cache_backend_raw = os.getenv("CROSSREF_CACHE_BACKEND", "memory").strip().lower()
    cache_backend: Literal["memory", "json"] = "json" if cache_backend_raw == "json" else "memory"

    cache_path_raw = os.getenv("CROSSREF_CACHE_PATH", "~/.crossref-cite/cache.json").strip()
    cache_path = Path(cache_path_raw).expanduser()

    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    return Config(
        mailto=mailto,
        user_agent=user_agent,
        cache_ttl=cache_ttl,
        cache_backend=cache_backend,
        cache_path=cache_path,
        log_level=log_level,
    )


# Singleton config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance (lazy-loaded)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset the configuration (useful for testing)."""
    global _config
    _config = None
