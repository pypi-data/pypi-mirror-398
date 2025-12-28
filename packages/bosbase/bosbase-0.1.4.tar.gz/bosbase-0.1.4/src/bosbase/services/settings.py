"""Application settings API."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional

from .base import BaseService


class SettingsService(BaseService):
    def get_all(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        return self.client.send("/api/settings", query=query, headers=headers)

    def update(
        self,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        return self.client.send(
            "/api/settings",
            method="PATCH",
            body=body,
            query=query,
            headers=headers,
        )

    def test_s3(
        self,
        *,
        filesystem: str = "storage",
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload.setdefault("filesystem", filesystem)
        self.client.send(
            "/api/settings/test/s3",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def test_email(
        self,
        to_email: str,
        template: str,
        *,
        collection: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload.setdefault("email", to_email)
        payload.setdefault("template", template)
        if collection:
            payload.setdefault("collection", collection)
        self.client.send(
            "/api/settings/test/email",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def generate_apple_client_secret(
        self,
        client_id: str,
        team_id: str,
        key_id: str,
        private_key: str,
        duration: int,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        payload = dict(body or {})
        payload.setdefault("clientId", client_id)
        payload.setdefault("teamId", team_id)
        payload.setdefault("keyId", key_id)
        payload.setdefault("privateKey", private_key)
        payload.setdefault("duration", duration)
        return self.client.send(
            "/api/settings/apple/generate-client-secret",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def get_category(
        self,
        category: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        settings = self.get_all(query=query, headers=headers)
        return settings.get(category)

    def update_meta(
        self,
        *,
        app_name: Optional[str] = None,
        app_url: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_address: Optional[str] = None,
        hide_controls: Optional[bool] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        meta = {
            key: value
            for key, value in {
                "appName": app_name,
                "appURL": app_url,
                "senderName": sender_name,
                "senderAddress": sender_address,
                "hideControls": hide_controls,
            }.items()
            if value is not None
        }
        return self.update(body={"meta": meta}, query=query, headers=headers)

    def get_application_settings(
        self,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        settings = self.get_all(query=query, headers=headers)
        return {
            "meta": settings.get("meta"),
            "trustedProxy": settings.get("trustedProxy"),
            "rateLimits": settings.get("rateLimits"),
            "batch": settings.get("batch"),
        }

    def update_application_settings(
        self,
        *,
        meta: Optional[Mapping[str, Any]] = None,
        trusted_proxy: Optional[Mapping[str, Any]] = None,
        rate_limits: Optional[Mapping[str, Any]] = None,
        batch: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if meta is not None:
            payload["meta"] = dict(meta)
        if trusted_proxy is not None:
            payload["trustedProxy"] = dict(trusted_proxy)
        if rate_limits is not None:
            payload["rateLimits"] = dict(rate_limits)
        if batch is not None:
            payload["batch"] = dict(batch)
        return self.update(body=payload, query=query, headers=headers)
