"""Sendlix Python SDK."""

__version__ = "1.0.0"

from .auth import Auth
from .clients.email_client import EmailClient
from .clients.group_client import GroupClient

__all__ = ["Auth", "EmailClient", "GroupClient"]
