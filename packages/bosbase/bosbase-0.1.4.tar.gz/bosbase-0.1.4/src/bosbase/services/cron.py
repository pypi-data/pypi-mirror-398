"""Cron jobs API."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService
from ..utils import encode_path_segment


class CronService(BaseService):
    def get_full_list(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[dict]:
        data = self.client.send("/api/crons", query=query, headers=headers)
        return list(data or [])

    def run(
        self,
        job_id: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.client.send(
            f"/api/crons/{encode_path_segment(job_id)}",
            method="POST",
            body=body,
            query=query,
            headers=headers,
        )
