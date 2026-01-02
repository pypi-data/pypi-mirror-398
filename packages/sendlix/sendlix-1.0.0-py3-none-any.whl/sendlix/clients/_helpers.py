"""Shared helpers for the Sendlix clients."""

from __future__ import annotations

import re
from typing import TypedDict, Union

from .._compat import NotRequired
from ..proto import EmailData_pb2

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class EmailAddressDict(TypedDict, total=False):
    email: str
    name: NotRequired[str]


EmailAddress = Union[str, EmailAddressDict]


def to_email_data(value: EmailAddress) -> EmailData_pb2.EmailData:
    email = EmailData_pb2.EmailData()
    if isinstance(value, str):
        _validate_email(value)
        email.email = value
        return email

    address = value.get("email")
    if not address:
        raise ValueError("Email record must include an 'email' value")
    _validate_email(address)
    email.email = address
    if value.get("name"):
        email.name = value["name"]
    return email


def _validate_email(address: str) -> None:
    if not _EMAIL_REGEX.match(address):
        raise ValueError(f"Invalid email address format: {address}")
