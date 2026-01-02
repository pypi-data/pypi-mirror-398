"""Base gRPC client utilities for the Sendlix SDK."""

from __future__ import annotations

from typing import Protocol, Tuple, Type, TypeVar

import grpc

from ..auth import Auth
from ..constants import API_HOST, USER_AGENT

TStub = TypeVar("TStub")


class SupportsAuthHeader(Protocol):
    """Protocol describing objects that can provide an auth header."""

    def get_auth_header(self) -> Tuple[str, str]:
        ...


class Client:
    """Base class that wires authentication metadata into a gRPC stub."""

    def __init__(
        self,
        auth: SupportsAuthHeader | str,
        stub_cls: Type[TStub],
        *,
        host: str = API_HOST,
    ) -> None:
        if isinstance(auth, str):
            auth = Auth(auth, host=host)

        if not hasattr(auth, "get_auth_header"):
            raise TypeError(
                "auth must be an API key string or expose get_auth_header()")

        self._auth = auth
        self._host = host

        metadata_credentials = grpc.metadata_call_credentials(
            self._build_metadata_callback()
        )
        channel_credentials = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(),
            metadata_credentials,
        )
        options = (("grpc.primary_user_agent", USER_AGENT),)
        self._channel = grpc.secure_channel(
            host, channel_credentials, options=options)
        self.client: TStub = stub_cls(self._channel)

    def _build_metadata_callback(self):  # type: ignore[override]
        def callback(context, callback_func):
            try:
                header_name, header_value = self._auth.get_auth_header()
                callback_func(((header_name, header_value),), None)
            except Exception as exc:  # pragma: no cover - exercised via client calls
                callback_func((), exc)

        return callback

    def close(self) -> None:
        """Close the underlying gRPC channel."""

        self._channel.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
