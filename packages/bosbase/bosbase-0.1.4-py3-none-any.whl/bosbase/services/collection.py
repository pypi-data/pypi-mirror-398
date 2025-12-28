"""Collection management service."""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional, Sequence

from .base import BaseCrudService
from ..utils import encode_path_segment


class CollectionService(BaseCrudService):
    @property
    def base_crud_path(self) -> str:
        return "/api/collections"

    def delete_collection(
        self,
        collection_id_or_name: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self.delete(
            collection_id_or_name,
            body=body,
            query=query,
            headers=headers,
        )

    def truncate(
        self,
        collection_id_or_name: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        encoded = encode_path_segment(collection_id_or_name)
        self.client.send(
            f"{self.base_crud_path}/{encoded}/truncate",
            method="DELETE",
            body=body,
            query=query,
            headers=headers,
        )

    def register_sql_tables(
        self,
        tables: Sequence[str],
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[Dict[str, Any]]:
        if not tables:
            raise ValueError("tables must contain at least one table name")

        payload = {"tables": list(tables)}
        if body:
            payload.update(body)

        data = self.client.send(
            f"{self.base_crud_path}/sql/tables",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )
        return list(data or [])

    def import_sql_tables(
        self,
        tables: Sequence[Mapping[str, Any]],
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        if not tables:
            raise ValueError("tables must contain at least one table definition")

        payload = {"tables": list(tables)}
        if body:
            payload.update(body)

        return self.client.send(
            f"{self.base_crud_path}/sql/import",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def import_collections(
        self,
        collections: Any,
        *,
        delete_missing: bool = False,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["collections"] = collections
        payload["deleteMissing"] = delete_missing

        self.client.send(
            f"{self.base_crud_path}/import",
            method="PUT",
            body=payload,
            query=query,
            headers=headers,
        )

    def export_collections(
        self,
        filter_collections: Optional[Callable[[Dict[str, Any]], bool]] = None,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[Dict[str, Any]]:
        collections = self.get_full_list(query=query, headers=headers)
        if filter_collections:
            collections = [
                item for item in collections if filter_collections(item)
            ]

        cleaned: list[Dict[str, Any]] = []
        for collection in collections:
            item = dict(collection or {})
            item.pop("created", None)
            item.pop("updated", None)

            oauth2 = item.get("oauth2")
            if isinstance(oauth2, Mapping) and "providers" in oauth2:
                oauth2_copy = dict(oauth2)
                oauth2_copy.pop("providers", None)
                item["oauth2"] = oauth2_copy

            cleaned.append(item)
        return cleaned

    def normalize_for_import(
        self,
        collections: Sequence[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        seen_ids = set()
        unique_collections: list[Mapping[str, Any]] = []
        for collection in collections:
            cid = collection.get("id") if isinstance(collection, Mapping) else None
            if cid and cid in seen_ids:
                continue
            if cid:
                seen_ids.add(cid)
            unique_collections.append(collection)

        normalized: list[Dict[str, Any]] = []
        for collection in unique_collections:
            item = dict(collection or {})
            item.pop("created", None)
            item.pop("updated", None)

            fields = item.get("fields")
            if isinstance(fields, list):
                seen_field_ids = set()
                deduped_fields = []
                for field in fields:
                    if isinstance(field, Mapping):
                        field_id = field.get("id")
                        if field_id and field_id in seen_field_ids:
                            continue
                        if field_id:
                            seen_field_ids.add(field_id)
                    deduped_fields.append(field)
                item["fields"] = deduped_fields

            normalized.append(item)

        return normalized

    def get_scaffolds(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        payload = dict(body or {})
        return self.client.send(
            f"{self.base_crud_path}/meta/scaffolds",
            body=payload,
            query=query,
            headers=headers,
        )

    def create_from_scaffold(
        self,
        scaffold_type: str,
        name: str,
        *,
        overrides: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        scaffolds = self.get_scaffolds(query=query, headers=headers)
        scaffold = scaffolds.get(scaffold_type)
        if not scaffold:
            raise ValueError(f"Scaffold for type '{scaffold_type}' not found.")

        data = dict(scaffold)
        data["name"] = name
        if overrides:
            data.update(overrides)
        if body:
            data.update(body)
        return self.create(body=data, query=query, headers=headers)

    def create_base(
        self,
        name: str,
        *,
        overrides: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        return self.create_from_scaffold(
            "base",
            name,
            overrides=overrides,
            body=body,
            query=query,
            headers=headers,
        )

    def create_auth(
        self,
        name: str,
        *,
        overrides: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        return self.create_from_scaffold(
            "auth",
            name,
            overrides=overrides,
            body=body,
            query=query,
            headers=headers,
        )

    def create_view(
        self,
        name: str,
        *,
        view_query: Optional[str] = None,
        overrides: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        scaffold_overrides = dict(overrides or {})
        if view_query is not None:
            scaffold_overrides["viewQuery"] = view_query
        return self.create_from_scaffold(
            "view",
            name,
            overrides=scaffold_overrides,
            body=body,
            query=query,
            headers=headers,
        )

    def add_index(
        self,
        collection_id_or_name: str,
        columns: Sequence[str],
        *,
        unique: bool = False,
        index_name: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        if not columns:
            raise ValueError("At least one column must be specified.")

        collection = self.get_one(collection_id_or_name, query=query, headers=headers)
        fields = collection.get("fields") or []
        field_names = [
            (field.get("name") if isinstance(field, Mapping) else None)
            for field in fields
        ]
        field_names = [name for name in field_names if name]

        for column in columns:
            if column != "id" and column not in field_names:
                raise ValueError(f'Field "{column}" does not exist in the collection.')

        collection_name = collection.get("name") or collection_id_or_name
        idx_name = index_name or f"idx_{collection_name}_{'_'.join(columns)}"
        columns_str = ", ".join(f"`{column}`" for column in columns)
        index_sql = (
            f"CREATE UNIQUE INDEX `{idx_name}` ON `{collection_name}` ({columns_str})"
            if unique
            else f"CREATE INDEX `{idx_name}` ON `{collection_name}` ({columns_str})"
        )

        indexes = list(collection.get("indexes") or [])
        if index_sql in indexes:
            raise ValueError("Index already exists.")

        indexes.append(index_sql)
        collection["indexes"] = indexes
        return self.update(
            collection_id_or_name,
            body=collection,
            query=query,
            headers=headers,
        )

    def remove_index(
        self,
        collection_id_or_name: str,
        columns: Sequence[str],
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        if not columns:
            raise ValueError("At least one column must be specified.")

        collection = self.get_one(collection_id_or_name, query=query, headers=headers)
        indexes = list(collection.get("indexes") or [])
        initial_length = len(indexes)

        def matches(idx: str) -> bool:
            for column in columns:
                backticked = f"`{column}`"
                if (
                    backticked in idx
                    or f"({column})" in idx
                    or f"({column}," in idx
                    or f", {column})" in idx
                ):
                    continue
                return False
            return True

        indexes = [idx for idx in indexes if not matches(idx)]
        if len(indexes) == initial_length:
            raise ValueError("Index not found.")

        collection["indexes"] = indexes
        return self.update(
            collection_id_or_name,
            body=collection,
            query=query,
            headers=headers,
        )

    def get_indexes(
        self,
        collection_id_or_name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> list[str]:
        collection = self.get_one(collection_id_or_name, query=query, headers=headers)
        existing = collection.get("indexes") or []
        return [idx for idx in existing if isinstance(idx, str)]

    def get_schema(
        self,
        collection_id_or_name: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        encoded = encode_path_segment(collection_id_or_name)
        return self.client.send(
            f"{self.base_crud_path}/{encoded}/schema",
            query=query,
            headers=headers,
        )

    def get_all_schemas(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        return self.client.send(
            f"{self.base_crud_path}/schemas",
            query=query,
            headers=headers,
        )
