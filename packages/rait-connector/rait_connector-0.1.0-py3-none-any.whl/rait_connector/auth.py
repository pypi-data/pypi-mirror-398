"""Authentication service for obtaining and caching access tokens.

This module exposes an `AuthenticationService` class that handles
retrieving OAuth2 access tokens (client credentials grant), caching
them with expiration, and providing auth headers to callers. It is
thread-safe and accepts a session factory to make testing easy.

Usage:
    service = AuthenticationService()
    token = service.get_token()
    headers = service.get_auth_headers()
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

import requests

from .config import settings
from .exceptions import AuthenticationError
from .http import HttpSessionFactory

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Obtain and cache OAuth2 access tokens using client credentials.

    The service caches an access token until (expires_at - skew). A
    thread lock protects concurrent refreshes.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        session_factory: Callable[
            [], requests.Session
        ] = HttpSessionFactory.get_default_session,
        clock: Callable[[], float] = time.time,
    ) -> None:
        """Initialize authentication service.

        Args:
            api_url: RAIT API URL (overrides env var)
            client_id: RAIT client ID (overrides env var)
            client_secret: RAIT client secret (overrides env var)
            session_factory: HTTP session factory
            clock: Time function for testing
        """
        self.api_url = api_url or settings.rait_api_url
        self.client_id = client_id or settings.rait_client_id
        self.client_secret = client_secret or settings.rait_client_secret

        if not self.api_url:
            raise AuthenticationError("RAIT API URL not configured")
        if not self.client_id:
            raise AuthenticationError("RAIT client ID not configured")
        if not self.client_secret:
            raise AuthenticationError("RAIT client secret not configured")

        self._session_factory = session_factory
        self._clock = clock

        self._lock = threading.Lock()
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._skew_seconds = 30

    def _needs_refresh(self) -> bool:
        """Check if token needs refresh."""
        now = self._clock()
        return not self._token or (now + self._skew_seconds) >= self._expires_at

    def get_token(self) -> str:
        """Return a valid access token, refreshing it if necessary.

        Returns:
            Access token

        Raises:
            AuthenticationError: On failure to obtain a token
        """
        if not self._needs_refresh():
            return self._token

        with self._lock:
            if not self._needs_refresh():
                return self._token

            token_url = f"{self.api_url}/api/model-registry/token/"

            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            try:
                session = self._session_factory()
                response = session.post(
                    token_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                token = data.get("access_token")
                if not token:
                    raise AuthenticationError(
                        "Authentication response missing access_token"
                    )

                expires_in = data.get("expires_in")
                now = self._clock()
                if isinstance(expires_in, (int, float)):
                    self._expires_at = now + float(expires_in)
                else:
                    self._expires_at = now + 300

                self._token = token

                logger.info(
                    "Obtained auth token (expires in %s seconds)",
                    data.get("expires_in"),
                )
                return token

            except requests.HTTPError as e:
                msg = f"HTTP error obtaining auth token: {getattr(e.response, 'status_code', '')}"
                logger.error(msg)
                raise AuthenticationError(msg) from e
            except requests.RequestException as e:
                msg = f"Network error obtaining auth token: {e}"
                logger.error(msg)
                raise AuthenticationError(msg) from e
            except ValueError as e:
                msg = f"Invalid JSON response from auth server: {e}"
                logger.error(msg)
                raise AuthenticationError(msg) from e
            except Exception as e:
                msg = f"Unexpected error obtaining auth token: {e}"
                logger.error(msg)
                raise AuthenticationError(msg) from e

    def get_auth_headers(self) -> dict:
        """Return a headers dict containing the Authorization header.

        Returns:
            Headers dictionary with Bearer token
        """
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}


__all__ = [
    "AuthenticationService",
    "AuthenticationError",
]
