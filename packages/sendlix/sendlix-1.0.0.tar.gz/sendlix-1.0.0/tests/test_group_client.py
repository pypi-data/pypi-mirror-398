from __future__ import annotations

import pytest

import sendlix.clients.group_client as group_module
from sendlix.clients.group_client import GroupClient
from sendlix.proto import group_pb2


class _FakeGroupStub:
    def __init__(self, channel):
        self.channel = channel
        self.insert_requests: list[group_pb2.InsertEmailToGroupRequest] = []
        self.remove_requests: list[group_pb2.RemoveEmailFromGroupRequest] = []
        self.check_requests: list[group_pb2.CheckEmailInGroupRequest] = []
        self.insert_response = group_pb2.UpdateResponse(success=True)
        self.remove_response = group_pb2.UpdateResponse(success=True)
        self.check_response = group_pb2.CheckEmailInGroupResponse(exists=True)

    def InsertEmailToGroup(self, request):
        self.insert_requests.append(request)
        return self.insert_response

    def RemoveEmailFromGroup(self, request):
        self.remove_requests.append(request)
        return self.remove_response

    def CheckEmailInGroup(self, request):
        self.check_requests.append(request)
        return self.check_response


@pytest.fixture()
def fake_group_stub(monkeypatch: pytest.MonkeyPatch) -> _FakeGroupStub:
    stub = _FakeGroupStub(None)
    monkeypatch.setattr(group_module.group_pb2_grpc,
                        "GroupStub", lambda channel: stub)
    return stub


def test_insert_email_builds_entries(fake_group_stub: _FakeGroupStub):
    client = GroupClient("secret.2")
    client.insert_email_into_group(
        "group-1",
        [
            {"email": "a@example.com"},
            {"email": {"email": "b@example.com", "name": "B"},
                "substitutions": {"tier": "pro"}},
        ],
    )

    request = fake_group_stub.insert_requests[0]
    assert request.groupId == "group-1"
    assert len(request.entries) == 2
    assert request.entries[1].email.name == "B"
    assert request.entries[1].substitutions["tier"] == "pro"


def test_insert_email_propagates_rpc_error(fake_group_stub: _FakeGroupStub):
    fake_group_stub.insert_response.success = False
    fake_group_stub.insert_response.message = "failure"
    client = GroupClient("secret.2")
    with pytest.raises(RuntimeError):
        client.insert_email_into_group("group-1", {"email": "a@example.com"})


def test_delete_email_from_group(fake_group_stub: _FakeGroupStub):
    client = GroupClient("secret.2")
    assert client.delete_email_from_group("group-1", "a@example.com")
    request = fake_group_stub.remove_requests[0]
    assert request.groupId == "group-1"


def test_delete_email_failure_raises(fake_group_stub: _FakeGroupStub):
    fake_group_stub.remove_response.success = False
    fake_group_stub.remove_response.message = "nope"
    client = GroupClient("secret.2")
    with pytest.raises(RuntimeError):
        client.delete_email_from_group("group-1", "a@example.com")


def test_contains_email_in_group(fake_group_stub: _FakeGroupStub):
    client = GroupClient("secret.2")
    assert client.contains_email_in_group("group-1", "a@example.com")
    fake_group_stub.check_response.exists = False
    assert not client.contains_email_in_group("group-1", "a@example.com")
