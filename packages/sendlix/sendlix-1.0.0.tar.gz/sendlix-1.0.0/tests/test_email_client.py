from __future__ import annotations

from pathlib import Path

import pytest

import sendlix.clients.email_client as email_module
from sendlix.clients.email_client import EmailClient
from sendlix.proto import email_pb2


class _FakeEmailStub:
    def __init__(self, channel):
        self.channel = channel
        self.sent_emails: list[email_pb2.SendMailRequest] = []
        self.raw_emails: list[email_pb2.EmlMailRequest] = []
        self.group_emails: list[email_pb2.GroupMailData] = []

    def SendEmail(self, request):
        self.sent_emails.append(request)
        response = email_pb2.SendEmailResponse()
        response.message.extend(["msg-1", "msg-2"])
        response.emailsLeft = 123
        return response

    def SendEmlEmail(self, request):
        self.raw_emails.append(request)
        response = email_pb2.SendEmailResponse()
        response.message.append("raw-msg")
        return response

    def SendGroupEmail(self, request):
        self.group_emails.append(request)
        return email_pb2.SendEmailResponse()


@pytest.fixture()
def fake_email_stub(monkeypatch: pytest.MonkeyPatch) -> _FakeEmailStub:
    stub = _FakeEmailStub(None)
    monkeypatch.setattr(email_module.email_pb2_grpc,
                        "EmailStub", lambda channel: stub)
    return stub


def test_send_email_builds_payload(fake_email_stub: _FakeEmailStub):
    client = EmailClient("secret.1")
    response = client.send_email(
        {
            "from": {"email": "sender@example.com", "name": "Sender"},
            "to": [
                {"email": "a@example.com", "name": "A"},
                "b@example.com",
            ],
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "replyTo": "reply@example.com",
            "subject": "Hello",
            "html": "<p>Hi</p>",
            "images": [
                {"placeholder": "logo", "data": b"123", "type": "PNG"},
            ],
        },
        additional_options={
            "attachments": [
                {"contentURL": "https://example.com", "filename": "file.txt"}
            ],
            "category": "welcome",
        },
    )

    assert response == ["msg-1", "msg-2"]
    request = fake_email_stub.sent_emails[0]
    assert getattr(request, "from").email == "sender@example.com"
    assert request.to[0].name == "A"
    assert request.cc[0].email == "cc@example.com"
    assert request.bcc[0].email == "bcc@example.com"
    assert request.reply_to.email == "reply@example.com"
    assert request.additionalInfos.attachments[0].filename == "file.txt"


def test_send_email_missing_content_raises(fake_email_stub: _FakeEmailStub):
    client = EmailClient("secret.1")
    with pytest.raises(ValueError):
        client.send_email(
            {"from": "a@example.com", "to": ["b@example.com"], "subject": "Hi"})


def test_send_eml_email_accepts_path(tmp_path: Path, fake_email_stub: _FakeEmailStub):
    eml_file = tmp_path / "mail.eml"
    eml_file.write_text("From: example@example.com")

    client = EmailClient("secret.1")
    response = client.send_eml_email(str(eml_file))

    assert response == ["raw-msg"]
    assert fake_email_stub.raw_emails[0].mail


def test_send_group_email_builds_request(fake_email_stub: _FakeEmailStub):
    client = EmailClient("secret.1")
    client.send_group_email(
        {
            "from": "sender@example.com",
            "groupId": "group-1",
            "subject": "Greetings",
            "text": "Hello",
            "category": "marketing",
        }
    )

    request = fake_email_stub.group_emails[0]
    assert request.groupId == "group-1"
    assert request.category == "marketing"


def test_send_group_email_requires_fields(fake_email_stub: _FakeEmailStub):
    client = EmailClient("secret.1")
    with pytest.raises(ValueError):
        client.send_group_email({"groupId": "missing"})
