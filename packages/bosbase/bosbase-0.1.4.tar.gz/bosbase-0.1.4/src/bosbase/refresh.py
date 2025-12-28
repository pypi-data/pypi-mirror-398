"""Helpers for auto-refreshing auth tokens."""

from __future__ import annotations

from typing import Callable

from .auth import is_token_expired


def reset_auto_refresh(client: object) -> None:
    reset = getattr(client, "_reset_auto_refresh", None)
    if callable(reset):
        reset()


def register_auto_refresh(
    client: object,
    threshold: int,
    refresh_func: Callable[[], None],
    reauthenticate_func: Callable[[], None],
) -> None:
    reset_auto_refresh(client)

    old_before_send = getattr(client, "before_send", None)
    old_record = getattr(client, "auth_store").record

    def on_store_change(token: str, record):
        if not token:
            reset_auto_refresh(client)
            return

        old_id = old_record.get("id") if isinstance(old_record, dict) else None
        new_id = record.get("id") if isinstance(record, dict) else None
        if new_id != old_id:
            reset_auto_refresh(client)
            return

        old_collection = (
            old_record.get("collectionId") if isinstance(old_record, dict) else None
        )
        new_collection = record.get("collectionId") if isinstance(record, dict) else None
        if (new_collection or old_collection) and new_collection != old_collection:
            reset_auto_refresh(client)
            return

    unsubscribe = getattr(client, "auth_store").on_change(on_store_change)

    def reset() -> None:
        unsubscribe()
        setattr(client, "before_send", old_before_send)
        try:
            delattr(client, "_reset_auto_refresh")
        except AttributeError:
            pass

    setattr(client, "_reset_auto_refresh", reset)

    def before_send(url: str, options):
        query = options.get("query") or {}
        if query.get("autoRefresh") or query.get("auto_refresh"):
            return old_before_send(url, options) if old_before_send else None

        auth_store = getattr(client, "auth_store")
        old_token = auth_store.token

        is_valid = auth_store.is_valid()
        if is_valid and is_token_expired(auth_store.token, threshold):
            try:
                refresh_func()
            except Exception:
                is_valid = False

        if not is_valid:
            reauthenticate_func()

        headers = dict(options.get("headers") or {})
        for key, value in list(headers.items()):
            if key.lower() == "authorization" and value == old_token and auth_store.token:
                headers[key] = auth_store.token
                break
        options["headers"] = headers

        return old_before_send(url, options) if old_before_send else None

    setattr(client, "before_send", before_send)
