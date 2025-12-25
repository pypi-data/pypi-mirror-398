"""HTTP session factory with retry configuration.

This module centralizes creation of `requests.Session` objects configured
with a retry strategy. It provides a small `RetryConfig` data holder and
an `HttpSessionFactory` that can produce cached default sessions or new
sessions with custom retry settings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behaviour.

    Fields default to values from `config.settings` when `None` is provided.
    """

    total: Optional[int] = None
    backoff_factor: Optional[float] = None
    status_forcelist: Optional[Iterable[int]] = None
    allowed_methods: Optional[Iterable[str]] = None

    @classmethod
    def from_settings(cls) -> "RetryConfig":
        return cls(
            total=getattr(settings, "api_retry_attempts", 3),
            backoff_factor=getattr(settings, "api_retry_backoff", 0.3),
            status_forcelist=getattr(
                settings, "api_retry_status_forcelist", [429, 500, 502, 503, 504]
            ),
            allowed_methods=getattr(
                settings, "api_retry_allowed_methods", ["GET", "POST"]
            ),
        )


class HttpSessionFactory:
    """Factory for `requests.Session` objects with retry adapters.

    Use `get_default_session()` to obtain a shared session configured from
    application settings, or call `create_session()` to obtain a fresh
    session with a custom `RetryConfig`.
    """

    _default_session: Optional[requests.Session] = None

    @classmethod
    def create_session(
        cls, retry_config: Optional[RetryConfig] = None
    ) -> requests.Session:
        """Create a new `requests.Session` configured with retry behaviour.

        Args:
            retry_config: optional `RetryConfig` to override defaults.

        Returns:
            requests.Session: configured session
        """
        if retry_config is None:
            retry_config = RetryConfig.from_settings()

        session = requests.Session()

        retry_strategy = Retry(
            total=retry_config.total,
            backoff_factor=retry_config.backoff_factor,
            status_forcelist=list(retry_config.status_forcelist)
            if retry_config.status_forcelist is not None
            else None,
            allowed_methods=list(retry_config.allowed_methods)
            if retry_config.allowed_methods is not None
            else None,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        logger.debug(
            "Created new requests.Session with retry strategy: %s", retry_config
        )
        return session

    @classmethod
    def get_default_session(cls) -> requests.Session:
        """Return a cached default session using application settings.

        The session is lazily created and cached on the class. This is useful
        for most application code that wants a shared session with retry.
        """
        if cls._default_session is None:
            cls._default_session = cls.create_session(RetryConfig.from_settings())
        return cls._default_session


def get_retry_session() -> requests.Session:
    """Convenience function for backwards-compatibility.

    Returns the shared default session configured from settings.
    """
    return HttpSessionFactory.get_default_session()


__all__ = ["RetryConfig", "HttpSessionFactory", "get_retry_session"]
