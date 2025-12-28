"""Superuser SQL execution helpers."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .. import types as sdk_types
from .base import BaseService


class SQLService(BaseService):
    """Executes SQL statements against the BosBase backend."""

    def execute(
        self,
        query: str,
        *,
        query_params: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> sdk_types.SQLExecuteResponse:
        trimmed = (query or "").strip()
        if not trimmed:
            raise ValueError("query must be non-empty")

        data = self.client.send(
            "/api/sql/execute",
            method="POST",
            body={"query": trimmed},
            query=query_params,
            headers=headers,
            timeout=timeout,
        )
        return sdk_types.SQLExecuteResponse.from_dict(data or {})
