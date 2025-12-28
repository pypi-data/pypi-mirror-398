"""Base service abstractions."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional

from ..exceptions import ClientResponseError
from ..utils import encode_path_segment


class BaseService:
    def __init__(self, client: "BosBase") -> None:
        self.client = client


class BaseCrudService(BaseService):
    @property
    def base_crud_path(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def get_full_list(
        self,
        *,
        batch: int = 500,
        expand: Optional[str] = None,
        filter: Optional[str] = None,
        sort: Optional[str] = None,
        fields: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[Any]:
        if batch <= 0:
            raise ValueError("batch must be > 0")

        result: list[Any] = []
        page = 1

        while True:
            data = self.get_list(
                page=page,
                per_page=batch,
                skip_total=True,
                expand=expand,
                filter=filter,
                sort=sort,
                fields=fields,
                query=query,
                headers=headers,
            )
            items = data.get("items", [])
            result.extend(items)

            if len(items) < data.get("perPage", batch):
                break
            page += 1

        return result

    def get_list(
        self,
        *,
        page: int = 1,
        per_page: int = 30,
        skip_total: bool = False,
        expand: Optional[str] = None,
        filter: Optional[str] = None,
        sort: Optional[str] = None,
        fields: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = dict(query or {})
        params.setdefault("page", page)
        params.setdefault("perPage", per_page)
        params.setdefault("skipTotal", skip_total)
        if filter is not None:
            params.setdefault("filter", filter)
        if sort is not None:
            params.setdefault("sort", sort)
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        return self.client.send(
            self.base_crud_path,
            query=params,
            headers=headers,
        )

    def get_one(
        self,
        record_id: str,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        if not record_id:
            raise ClientResponseError(
                url=self.client.build_url(f"{self.base_crud_path}/"),
                status=404,
                response={
                    "code": 404,
                    "message": "Missing required record id.",
                    "data": {},
                },
            )

        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        encoded_id = encode_path_segment(record_id)

        return self.client.send(
            f"{self.base_crud_path}/{encoded_id}",
            query=params,
            headers=headers,
        )

    def get_first_list_item(
        self,
        filter: str,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        data = self.get_list(
            page=1,
            per_page=1,
            skip_total=True,
            filter=filter,
            expand=expand,
            fields=fields,
            query=query,
            headers=headers,
        )
        items = data.get("items") or []
        if not items:
            raise ClientResponseError(
                status=404,
                response={
                    "code": 404,
                    "message": "The requested resource wasn't found.",
                    "data": {},
                },
            )
        return items[0]

    def create(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        return self.client.send(
            self.base_crud_path,
            method="POST",
            body=body,
            query=params,
            files=files,
            headers=headers,
        )

    def update(
        self,
        record_id: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        encoded_id = encode_path_segment(record_id)

        return self.client.send(
            f"{self.base_crud_path}/{encoded_id}",
            method="PATCH",
            body=body,
            query=params,
            files=files,
            headers=headers,
        )

    def delete(
        self,
        record_id: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        encoded_id = encode_path_segment(record_id)

        self.client.send(
            f"{self.base_crud_path}/{encoded_id}",
            method="DELETE",
            body=body,
            query=query,
            headers=headers,
        )
