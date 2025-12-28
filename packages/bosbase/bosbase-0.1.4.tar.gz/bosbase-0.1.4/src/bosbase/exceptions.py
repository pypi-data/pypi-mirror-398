"""SDK specific exceptions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ClientResponseError(Exception):
    """Raised when a BosBase HTTP call fails."""

    url: Optional[str] = None
    status: int = 0
    response: Dict[str, Any] = field(default_factory=dict)
    is_abort: bool = False
    original_error: Optional[Exception] = None

    def __str__(self) -> str:
        return (
            f"ClientResponseError(status={self.status}, url={self.url}, "
            f"response={self.response or {}}, is_abort={self.is_abort})"
        )
