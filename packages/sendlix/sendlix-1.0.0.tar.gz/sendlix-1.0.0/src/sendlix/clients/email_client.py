"""Email client implementation mirroring the reference SDK behavior."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, MutableMapping, Sequence, TypedDict
from .._compat import NotRequired

from google.protobuf.timestamp_pb2 import Timestamp

from ..proto import email_pb2, email_pb2_grpc
from ._helpers import EmailAddress, EmailAddressDict, to_email_data
from .client import Client, SupportsAuthHeader


class ImageConfig(TypedDict):
    placeholder: str
    data: bytes | bytearray | memoryview
    type: str


class AttachmentConfig(TypedDict, total=False):
    contentURL: str
    filename: str
    contentType: NotRequired[str]


class AdditionalEmailOptions(TypedDict, total=False):
    attachments: Sequence[AttachmentConfig]
    category: str
    send_at: datetime


MailOptions = TypedDict(
    "MailOptions",
    {
        "from": EmailAddress,
        "to": Sequence[EmailAddress],
        "cc": Sequence[EmailAddress],
        "bcc": Sequence[EmailAddress],
        "subject": str,
        "replyTo": EmailAddress,
        "html": str,
        "text": str,
        "tracking": bool,
        "images": Sequence[ImageConfig],
    },
    total=False,
)


GroupMailOptions = TypedDict(
    "GroupMailOptions",
    {
        "from": EmailAddress,
        "groupId": str,
        "subject": str,
        "category": str,
        "html": str,
        "text": str,
        "tracking": bool,
        "images": Sequence[ImageConfig],
    },
    total=False,
)


class EmailClient(Client):
    """Client for interacting with the Sendlix email gRPC service."""

    def __init__(self, auth: SupportsAuthHeader | str) -> None:
        super().__init__(auth, email_pb2_grpc.EmailStub)

    def send_email(
        self,
        mail_options: MailOptions,
        additional_options: AdditionalEmailOptions | None = None,
    ) -> list[str]:
        self._validate_mail_options(mail_options)

        request = email_pb2.SendMailRequest()
        getattr(request, "from").CopyFrom(to_email_data(mail_options["from"]))
        request.to.extend(to_email_data(entry) for entry in mail_options["to"])
        request.subject = mail_options["subject"]
        request.TextContent.CopyFrom(_build_mail_content(mail_options))

        if mail_options.get("cc"):
            request.cc.extend(to_email_data(addr)
                              for addr in mail_options["cc"])
        if mail_options.get("bcc"):
            request.bcc.extend(to_email_data(addr)
                               for addr in mail_options["bcc"])
        if mail_options.get("replyTo"):
            request.reply_to.CopyFrom(to_email_data(mail_options["replyTo"]))

        if additional_options:
            request.additionalInfos.CopyFrom(
                _build_additional_infos(additional_options))

        response = self.client.SendEmail(request)
        return list(response.message)

    def send_eml_email(
        self,
        eml: str | Path | bytes | bytearray | memoryview,
        additional_options: AdditionalEmailOptions | None = None,
    ) -> list[str]:
        raw_bytes = _coerce_eml_bytes(eml)
        request = email_pb2.EmlMailRequest(mail=raw_bytes)
        if additional_options:
            request.additionalInfos.CopyFrom(
                _build_additional_infos(additional_options))

        response = self.client.SendEmlEmail(request)
        return list(response.message)

    def send_group_email(self, group_mail: GroupMailOptions) -> list[str]:
        required = ("from", "groupId", "subject")
        missing = [field for field in required if not group_mail.get(field)]
        if missing:
            raise ValueError(
                f"Missing required group_mail field(s): {', '.join(missing)}")

        request = email_pb2.GroupMailData(
            groupId=group_mail["groupId"],
            subject=group_mail["subject"],
        )
        getattr(request, "from").CopyFrom(to_email_data(group_mail["from"]))
        request.TextContent.CopyFrom(_build_mail_content(group_mail))

        if group_mail.get("category"):
            request.category = group_mail["category"]

        response = self.client.SendGroupEmail(request)
        return list(response.message)

    # Aliases matching the reference client's naming
    sendEmail = send_email
    sendEmlEmail = send_eml_email
    sendGroupEmail = send_group_email

    def _validate_mail_options(self, mail_options: MailOptions) -> None:
        required = ("from", "to", "subject")
        missing = [field for field in required if not mail_options.get(field)]
        if missing:
            raise ValueError(
                f"Missing required mail_options field(s): {', '.join(missing)}")

        if not mail_options.get("html") and not mail_options.get("text"):
            raise ValueError(
                "Either 'html' or 'text' content must be provided")


def _build_mail_content(source: MutableMapping[str, object]) -> email_pb2.MailContent:
    content = email_pb2.MailContent(
        html=source.get("html", "") or "",
        text=source.get("text", "") or "",
        tracking=bool(source.get("tracking", False)),
    )
    if source.get("images"):
        content.Images.extend(_build_images(source["images"]))
    return content


def _build_images(images: Sequence[ImageConfig]) -> Iterable[email_pb2.Images]:
    for image in images:
        payload = email_pb2.Images(
            placeholder=image["placeholder"],
            Image=bytes(image["data"]),
        )
        mime = image.get("type", "PNG").upper()
        if mime not in email_pb2.MimeType.keys():
            raise ValueError(f"Unsupported image MIME type: {mime}")
        payload.type = email_pb2.MimeType.Value(mime)
        yield payload


def _build_additional_infos(options: AdditionalEmailOptions) -> email_pb2.AdditionalInfos:
    info = email_pb2.AdditionalInfos()
    if options.get("attachments"):
        for attachment in options["attachments"]:
            data = email_pb2.AttachmentData(
                contentUrl=attachment["contentURL"],
                filename=attachment["filename"],
            )
            if attachment.get("contentType"):
                data.type = attachment["contentType"]
            info.attachments.append(data)
    if options.get("category"):
        info.category = options["category"]
    if options.get("send_at"):
        timestamp = Timestamp()
        send_at = options["send_at"]
        if send_at.tzinfo is None:
            send_at = send_at.replace(tzinfo=timezone.utc)
        timestamp.FromDatetime(send_at.astimezone(timezone.utc))
        info.send_at.CopyFrom(timestamp)
    return info


def _coerce_eml_bytes(eml: str | Path | bytes | bytearray | memoryview) -> bytes:
    if isinstance(eml, (bytes, bytearray, memoryview)):
        return bytes(eml)
    path = Path(eml)
    return path.read_bytes()
