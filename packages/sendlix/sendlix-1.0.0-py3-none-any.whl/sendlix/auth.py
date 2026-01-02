"""Authentication helpers for the Sendlix SDK."""

from __future__ import annotations

import time
from typing import Tuple

import grpc

from .constants import API_HOST, USER_AGENT
from .proto import auth_pb2, auth_pb2_grpc
from ._compat import dataclass


@dataclass(slots=True)
class _CachedToken:
    value: str
    expires_at: float


class Auth:
    """Fetches and caches JWT tokens using an API key."""

    def __init__(self, api_key: str, *, host: str = API_HOST) -> None:
        secret, key_id = self._split_api_key(api_key)
        self._api_key = auth_pb2.ApiKey(secret=secret, keyID=int(key_id))
        self._host = host
        self._channel = grpc.secure_channel(
            host,
            grpc.ssl_channel_credentials(),
            options=(("grpc.primary_user_agent", USER_AGENT),),
        )
        self._client = auth_pb2_grpc.AuthStub(self._channel)
        self._token_cache: _CachedToken | None = None

    def _split_api_key(self, api_key: str) -> Tuple[str, str]:
        parts = api_key.split(".")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                "Invalid API key format. Expected format: 'key.value'.")
        return parts[0], parts[1]

    def get_auth_header(self) -> Tuple[str, str]:
        """Return the Authorization header tuple expected by gRPC metadata."""

        token = self._get_token()
        return "authorization", f"Bearer {token}"

    def _get_token(self) -> str:
        now = time.time()
        if self._token_cache and self._token_cache.expires_at - 5 > now:
            return self._token_cache.value

        request = auth_pb2.AuthRequest(apiKey=self._api_key)
        response = self._client.GetJwtToken(request)
        if not response or not response.token:
            raise RuntimeError(
                "Authentication failed: empty response from server")

        ttl_seconds = response.expires.seconds if response.HasField(
            "expires") else 0
        expires_at = now + ttl_seconds
        self._token_cache = _CachedToken(response.token, expires_at)
        return response.token

    def invalidate_cache(self) -> None:
        """Force fetching a new token on the next request."""

        self._token_cache = None

    def close(self) -> None:
        """Dispose the gRPC channel."""

        self._channel.close()

    def __enter__(self) -> "Auth":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Auth(host={self._host!r}, token_cached={self._token_cache is not None})"
