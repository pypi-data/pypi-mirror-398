"""Server logs API."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional

from ..exceptions import ClientResponseError
from .base import BaseService


class LogService(BaseService):
    def get_list(
        self,
        *,
        page: int = 1,
        per_page: int = 30,
        filter: Optional[str] = None,
        sort: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        params = dict(query or {})
        params.setdefault("page", page)
        params.setdefault("perPage", per_page)
        if filter is not None:
            params.setdefault("filter", filter)
        if sort is not None:
            params.setdefault("sort", sort)
        return self.client.send("/api/logs", query=params, headers=headers)

    def get_one(
        self,
        log_id: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        if not log_id:
            raise ClientResponseError(
                url=self.client.build_url("/api/logs/"),
                status=404,
                response={
                    "code": 404,
                    "message": "Missing required log id.",
                    "data": {},
                },
            )
        return self.client.send(
            f"/api/logs/{log_id}",
            query=query,
            headers=headers,
        )

    def get_stats(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[Dict[str, Any]]:
        data = self.client.send(
            "/api/logs/stats",
            query=query,
            headers=headers,
        )
        return list(data or [])
