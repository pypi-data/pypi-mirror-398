from __future__ import annotations

import pytest
from google.protobuf.timestamp_pb2 import Timestamp

import sendlix.auth as auth_module
from sendlix.auth import Auth
from sendlix.proto import auth_pb2


class _FakeAuthStub:
    def __init__(self, channel):
        self.channel = channel
        self.calls = 0

    def GetJwtToken(self, request):
        self.calls += 1
        response = auth_pb2.AuthResponse(token="token-123")
        expires = Timestamp()
        expires.seconds = 60
        response.expires.CopyFrom(expires)
        return response


def test_auth_rejects_invalid_keys():
    with pytest.raises(ValueError):
        Auth("invalid")


def test_auth_caches_token(monkeypatch: pytest.MonkeyPatch):
    fake_stub = _FakeAuthStub(None)
    monkeypatch.setattr(auth_module.auth_pb2_grpc,
                        "AuthStub", lambda channel: fake_stub)

    auth = Auth("secret.42")
    header1 = auth.get_auth_header()
    header2 = auth.get_auth_header()

    assert header1 == ("authorization", "Bearer token-123")
    assert header1 == header2
    assert fake_stub.calls == 1

    auth.invalidate_cache()
    auth.get_auth_header()
    assert fake_stub.calls == 2
