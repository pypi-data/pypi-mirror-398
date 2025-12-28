"""GraphQL service."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from .base import BaseService


class GraphQLService(BaseService):
    def query(
        self,
        query: str,
        *,
        variables: Optional[Mapping[str, Any]] = None,
        operation_name: Optional[str] = None,
        query_params: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "query": query,
            "variables": dict(variables or {}),
        }
        if operation_name is not None:
            payload["operationName"] = operation_name

        return self.client.send(
            "/api/graphql",
            method="POST",
            query=query_params,
            headers=headers,
            body=payload,
            timeout=timeout,
        )
