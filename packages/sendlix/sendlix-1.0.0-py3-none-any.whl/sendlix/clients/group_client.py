"""Group management client mirroring the reference SDK behavior."""

from __future__ import annotations

from typing import Mapping, MutableMapping, Sequence, TypedDict, Union

from .._compat import NotRequired
from ..proto import EmailData_pb2, group_pb2, group_pb2_grpc
from ._helpers import EmailAddress, to_email_data
from .client import Client, SupportsAuthHeader


class EmailRecord(TypedDict, total=False):
    email: Union[EmailAddress, EmailData_pb2.EmailData]
    substitutions: Mapping[str, str]


GroupEmailInput = Union[EmailAddress, EmailRecord]


class GroupClient(Client):
    """Client for the Sendlix group gRPC service."""

    def __init__(self, auth: SupportsAuthHeader | str) -> None:
        super().__init__(auth, group_pb2_grpc.GroupStub)

    def insert_email_into_group(
        self,
        group_id: str,
        email: GroupEmailInput | Sequence[GroupEmailInput],
        fail_handling: str = "ABORT",
    ) -> bool:
        if not group_id:
            raise ValueError("group_id is required")

        entries = email if isinstance(email, Sequence) and not isinstance(
            email, (str, bytes)) else [email]

        request = group_pb2.InsertEmailToGroupRequest(groupId=group_id)
        request.onFailure = _resolve_failure_handler(fail_handling)

        for record in entries:
            request.entries.append(_build_group_entry(record))

        response = self.client.InsertEmailToGroup(request)
        if not response.success:
            raise RuntimeError(response.message or "InsertEmailToGroup failed")
        return True

    def delete_email_from_group(self, group_id: str, email: str) -> bool:
        if not group_id or not email:
            raise ValueError("Both group_id and email are required")

        request = group_pb2.RemoveEmailFromGroupRequest(
            groupId=group_id, email=email)
        response = self.client.RemoveEmailFromGroup(request)
        if not response.success:
            raise RuntimeError(
                response.message or "RemoveEmailFromGroup failed")
        return True

    def contains_email_in_group(self, group_id: str, email: str) -> bool:
        if not group_id or not email:
            raise ValueError("Both group_id and email are required")

        request = group_pb2.CheckEmailInGroupRequest(
            groupId=group_id, email=email)
        response = self.client.CheckEmailInGroup(request)
        return bool(response.exists)

    # Aliases to mirror the reference client's naming
    insertEmailIntoGroup = insert_email_into_group
    deleteEmailFromGroup = delete_email_from_group
    containsEmailInGroup = contains_email_in_group


def _resolve_failure_handler(value: str) -> int:
    try:
        return group_pb2.FailureHandler.Value(value.upper())
    except ValueError as exc:  # pragma: no cover - defensive guard
        valid = ", ".join(group_pb2.FailureHandler.keys())
        raise ValueError(
            f"Invalid fail_handling '{value}'. Expected one of: {valid}") from exc


def _build_group_entry(record: GroupEmailInput) -> group_pb2.GroupEntry:
    entry = group_pb2.GroupEntry()
    substitutions = {}

    if isinstance(record, dict):
        is_email_record = "substitutions" in record or isinstance(
            record.get("email"), (dict, EmailData_pb2.EmailData)
        )
        if is_email_record and "email" in record:
            recipient = record["email"]
            entry.email.CopyFrom(to_email_data(recipient))
            substitutions = record.get("substitutions") or {}
        else:
            entry.email.CopyFrom(to_email_data(record))
    else:
        entry.email.CopyFrom(to_email_data(record))

    if substitutions:
        entry.substitutions.update(substitutions)

    return entry
