"""Compatibility helpers.

Provides a dataclass decorator that sets ``slots=True`` only on Python >= 3.10.
This avoids TypeError on older interpreters where the ``slots`` argument is not supported.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass as _dataclass
from typing import Any

# TypedDict optional keys compatibility
try:  # Python >= 3.11
    from typing import NotRequired as NotRequired  # type: ignore
    from typing import Required as Required  # type: ignore
except Exception:  # Python < 3.11
    from typing_extensions import NotRequired as NotRequired  # type: ignore
    from typing_extensions import Required as Required  # type: ignore


def dataclass(*args: Any, **kwargs: Any):
    """Dataclass decorator compatible across Python 3.9+.

    - On Python >= 3.10, ensures ``slots=True`` by default unless explicitly overridden.
    - On Python < 3.10, silently ignores the ``slots`` kwarg.
    """
    if sys.version_info >= (3, 10):
        # Default to slots=True if not provided.
        kwargs.setdefault("slots", True)
    else:
        # Remove unsupported kwarg on older Python versions.
        kwargs.pop("slots", None)
    return _dataclass(*args, **kwargs)
