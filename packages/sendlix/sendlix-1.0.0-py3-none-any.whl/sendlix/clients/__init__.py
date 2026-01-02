"""Client implementations for the Sendlix SDK."""

from .email_client import EmailClient
from .group_client import GroupClient
from .client import Client

__all__ = ["Client", "EmailClient", "GroupClient"]
