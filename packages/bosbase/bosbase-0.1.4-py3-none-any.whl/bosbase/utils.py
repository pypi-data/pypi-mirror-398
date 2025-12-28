"""Internal helpers for request serialization."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Mapping, Tuple, Union
from urllib.parse import quote, urlencode


def to_serializable(value: Any) -> Any:
    """Convert dataclasses or custom objects to JSON-compatible structures."""

    if value is None:
        return None

    if is_dataclass(value):
        return {
            key: to_serializable(val)
            for key, val in asdict(value).items()
            if val is not None
        }

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if hasattr(value, "to_json"):
        result = value.to_json()
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return result
        return result

    if isinstance(value, Mapping):
        return {
            key: to_serializable(val)
            for key, val in value.items()
            if val is not None
        }

    if isinstance(value, (list, tuple, set)):
        return [to_serializable(item) for item in value]

    return value


def normalize_query_params(params: Mapping[str, Any] | None) -> Dict[str, list[str]]:
    """Convert query dict to {key: [value,...]} as expected by urllib."""
    if not params:
        return {}

    normalized: Dict[str, list[str]] = {}
    for key, value in params.items():
        if value is None:
            continue

        values: Iterable[Any]
        if isinstance(value, (list, tuple, set)):
            values = value
        else:
            values = (value,)

        bucket = normalized.setdefault(str(key), [])
        for item in values:
            if item is None:
                continue
            bucket.append(str(item))

        if not bucket:
            normalized.pop(str(key), None)

    return normalized


def ensure_file_tuples(
    files: Union[
        Mapping[str, Any],
        Iterable[Tuple[str, Any]],
        None,
    ]
) -> list[Tuple[str, Tuple[str, Any, str]]]:
    """Normalize requests-style files argument."""

    if not files:
        return []

    normalized: list[Tuple[str, Tuple[str, Any, str]]] = []

    def _normalize(key: str, value: Any) -> None:
        if isinstance(value, tuple):
            if len(value) == 2:
                filename, fileobj = value
                content_type = "application/octet-stream"
            elif len(value) == 3:
                filename, fileobj, content_type = value
            else:
                raise ValueError("file tuples must be (filename, fileobj, [content_type])")
        else:
            filename, fileobj, content_type = key, value, "application/octet-stream"

        normalized.append((key, (filename, fileobj, content_type)))

    if isinstance(files, Mapping):
        for k, v in files.items():
            _normalize(str(k), v)
        return normalized

    for key, value in files:
        _normalize(str(key), value)

    return normalized


def encode_path_segment(value: Any) -> str:
    """Encode a single URL path segment."""
    return quote(str(value), safe="")


def build_relative_url(path: str, query: Mapping[str, Any] | None = None) -> str:
    """Build a relative URL (without base host) with encoded query parameters."""
    rel = "/" + path.lstrip("/")

    if not query:
        return rel

    normalized = normalize_query_params(query)
    if not normalized:
        return rel

    return rel + "?" + urlencode(normalized, doseq=True)
