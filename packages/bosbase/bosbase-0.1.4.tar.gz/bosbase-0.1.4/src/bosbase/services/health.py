"""Health check API."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService


class HealthService(BaseService):
    def check(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> dict:
        return self.client.send("/api/health", query=query, headers=headers)
