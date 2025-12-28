"""Record service with CRUD and auth helpers."""

from __future__ import annotations

import base64
import json
import threading
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, MutableMapping, Optional

from ..exceptions import ClientResponseError
from ..refresh import register_auto_refresh, reset_auto_refresh
from ..utils import encode_path_segment
from .base import BaseCrudService

if TYPE_CHECKING:  # pragma: no cover
    from ..client import BosBase


SubscriptionCallback = Callable[[Dict[str, Any]], None]


def _with_auto_refresh(query: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    params = dict(query or {})
    params["autoRefresh"] = True
    return params


class RecordService(BaseCrudService):
    def __init__(self, client: BosBase, collection_id_or_name: str) -> None:
        super().__init__(client)
        self.collection_id_or_name = collection_id_or_name

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    @property
    def base_collection_path(self) -> str:
        encoded = encode_path_segment(self.collection_id_or_name)
        return f"/api/collections/{encoded}"

    @property
    def base_crud_path(self) -> str:
        return f"{self.base_collection_path}/records"

    @property
    def is_superusers(self) -> bool:
        return self.collection_id_or_name in ("_superusers", "_pbc_2773867675")

    # ------------------------------------------------------------------
    # Realtime
    # ------------------------------------------------------------------
    def subscribe(
        self,
        topic: str,
        callback: SubscriptionCallback,
        *,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Callable[[], None]:
        if not topic:
            raise ValueError("topic must be set")

        full_topic = f"{self.collection_id_or_name}/{topic}"
        return self.client.realtime.subscribe(
            full_topic,
            callback,
            query=query,
            headers=headers,
        )

    def unsubscribe(self, topic: Optional[str] = None) -> None:
        if topic:
            self.client.realtime.unsubscribe(f"{self.collection_id_or_name}/{topic}")
        else:
            self.client.realtime.unsubscribe_by_prefix(self.collection_id_or_name)

    # ------------------------------------------------------------------
    # CRUD sync with auth store
    # ------------------------------------------------------------------
    def update(self, record_id: str, **kwargs: Any) -> Dict[str, Any]:
        item = super().update(record_id, **kwargs)
        self._maybe_update_auth_record(item)
        return item

    def delete(self, record_id: str, **kwargs: Any) -> None:
        super().delete(record_id, **kwargs)
        if self._is_auth_record(record_id):
            self.client.auth_store.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_count(
        self,
        *,
        filter: Optional[str] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> int:
        params = dict(query or {})
        if filter is not None:
            params.setdefault("filter", filter)
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        data = self.client.send(
            f"{self.base_crud_path}/count",
            query=params,
            headers=headers,
        )
        return int(data.get("count", 0))

    def list_auth_methods(
        self,
        *,
        fields: Optional[str] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        params = dict(query or {})
        params.setdefault("fields", fields or "mfa,otp,password,oauth2")
        return self.client.send(
            f"{self.base_collection_path}/auth-methods",
            query=params,
            headers=headers,
        )

    def auth_with_password(
        self,
        identity: str,
        password: str,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        auto_refresh_threshold: Optional[int] = None,
        auto_refresh: bool = True,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        threshold = None
        if self.is_superusers:
            threshold = auto_refresh_threshold
            if not auto_refresh:
                reset_auto_refresh(self.client)

        payload = dict(body or {})
        payload["identity"] = identity
        payload["password"] = password

        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        data = self.client.send(
            f"{self.base_collection_path}/auth-with-password",
            method="POST",
            body=payload,
            query=params,
            headers=headers,
        )
        data = self._auth_response(data)

        if threshold and self.is_superusers and auto_refresh:
            register_auto_refresh(
                self.client,
                int(threshold),
                lambda: self.auth_refresh(query=_with_auto_refresh(query)),
                lambda: self.auth_with_password(
                    identity,
                    password,
                    expand=expand,
                    fields=fields,
                    body=body,
                    query=_with_auto_refresh(query),
                    headers=headers,
                    auto_refresh=True,
                ),
            )

        return data

    def bind_custom_token(
        self,
        email: str,
        password: str,
        token: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> bool:
        payload = dict(body or {})
        payload["email"] = email
        payload["password"] = password
        payload["token"] = token
        self.client.send(
            f"{self.base_collection_path}/bind-token",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )
        return True

    def unbind_custom_token(
        self,
        email: str,
        password: str,
        token: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> bool:
        payload = dict(body or {})
        payload["email"] = email
        payload["password"] = password
        payload["token"] = token
        self.client.send(
            f"{self.base_collection_path}/unbind-token",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )
        return True

    def auth_with_token(
        self,
        token: str,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        auto_refresh_threshold: Optional[int] = None,
        auto_refresh: bool = True,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        threshold = None
        if self.is_superusers:
            threshold = auto_refresh_threshold
            if not auto_refresh:
                reset_auto_refresh(self.client)

        payload = dict(body or {})
        payload["token"] = token

        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        data = self.client.send(
            f"{self.base_collection_path}/auth-with-token",
            method="POST",
            body=payload,
            query=params,
            headers=headers,
        )
        data = self._auth_response(data)

        if threshold and self.is_superusers and auto_refresh:
            register_auto_refresh(
                self.client,
                int(threshold),
                lambda: self.auth_refresh(query=_with_auto_refresh(query)),
                lambda: self.auth_with_token(
                    token,
                    expand=expand,
                    fields=fields,
                    body=body,
                    query=_with_auto_refresh(query),
                    headers=headers,
                    auto_refresh=True,
                ),
            )

        return data

    def auth_with_oauth2_code(
        self,
        provider: str,
        code: str,
        code_verifier: str,
        redirect_url: str,
        *,
        create_data: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = dict(body or {})
        payload.setdefault("provider", provider)
        payload.setdefault("code", code)
        payload.setdefault("codeVerifier", code_verifier)
        payload.setdefault("redirectURL", redirect_url)
        if create_data is not None:
            payload.setdefault("createData", create_data)

        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        data = self.client.send(
            f"{self.base_collection_path}/auth-with-oauth2",
            method="POST",
            body=payload,
            query=params,
            headers=headers,
        )
        return self._auth_response(data)

    def auth_with_oauth2(
        self,
        provider_name: str,
        url_callback: Callable[[str], None],
        *,
        scopes: Optional[list[str]] = None,
        create_data: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        timeout: float = 180.0,
    ) -> Dict[str, Any]:
        auth_methods = self.list_auth_methods()
        providers = (
            auth_methods.get("oauth2", {}).get("providers", []) if auth_methods else []
        )
        provider = next(
            (p for p in providers if p.get("name") == provider_name),
            None,
        )
        if not provider:
            raise ClientResponseError(
                response={"message": f"missing provider {provider_name}"}
            )

        redirect_url = self.client.build_url("/api/oauth2-redirect")
        event = threading.Event()
        result: Dict[str, Any] = {}
        error_holder: list[Exception] = []

        def handler(payload: Dict[str, Any]) -> None:
            try:
                state = payload.get("state")
                code = payload.get("code")
                err = payload.get("error")
                if state != self.client.realtime.client_id:
                    return
                if err:
                    raise ClientResponseError(response={"message": err})
                if not code:
                    raise ClientResponseError(
                        response={"message": "OAuth2 redirect missing code"}
                    )

                auth = self.auth_with_oauth2_code(
                    provider_name,
                    code,
                    provider.get("codeVerifier", ""),
                    redirect_url,
                    create_data=create_data,
                    body=body,
                    query=query,
                    headers=headers,
                    expand=expand,
                    fields=fields,
                )
                result.update(auth)
            except Exception as exc:  # pragma: no cover - network heavy
                error_holder.append(exc if isinstance(exc, Exception) else Exception(str(exc)))
            finally:
                event.set()

        unsubscribe = self.client.realtime.subscribe("@oauth2", handler)

        try:
            # ensure realtime connected to obtain state
            self.client.realtime.ensure_connected(timeout=10.0)
            state = self.client.realtime.client_id

            auth_url = provider.get("authURL", "") + redirect_url
            from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

            parsed = urlsplit(auth_url)
            params = dict(parse_qsl(parsed.query))
            params["state"] = state
            if scopes:
                params["scope"] = " ".join(scopes)
            query_string = urlencode(params)
            full_url = urlunsplit(parsed._replace(query=query_string))
            url_callback(full_url)

            if not event.wait(timeout):
                raise ClientResponseError(
                    response={"message": "OAuth2 flow timed out"}
                )

            if error_holder:
                raise error_holder[0]

            return result
        finally:
            unsubscribe()

    def auth_refresh(
        self,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        data = self.client.send(
            f"{self.base_collection_path}/auth-refresh",
            method="POST",
            body=body,
            query=params,
            headers=headers,
        )
        return self._auth_response(data)

    def request_password_reset(
        self,
        email: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["email"] = email
        self.client.send(
            f"{self.base_collection_path}/request-password-reset",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def confirm_password_reset(
        self,
        token: str,
        password: str,
        password_confirm: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["token"] = token
        payload["password"] = password
        payload["passwordConfirm"] = password_confirm
        self.client.send(
            f"{self.base_collection_path}/confirm-password-reset",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def request_verification(
        self,
        email: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["email"] = email
        self.client.send(
            f"{self.base_collection_path}/request-verification",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def confirm_verification(
        self,
        token: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["token"] = token
        self.client.send(
            f"{self.base_collection_path}/confirm-verification",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )
        self._mark_verified(token)

    def request_email_change(
        self,
        new_email: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["newEmail"] = new_email
        self.client.send(
            f"{self.base_collection_path}/request-email-change",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def confirm_email_change(
        self,
        token: str,
        password: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        payload = dict(body or {})
        payload["token"] = token
        payload["password"] = password
        self.client.send(
            f"{self.base_collection_path}/confirm-email-change",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )
        self._clear_if_same_token(token)

    def request_otp(
        self,
        email: str,
        *,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        payload = dict(body or {})
        payload.setdefault("email", email)
        return self.client.send(
            f"{self.base_collection_path}/request-otp",
            method="POST",
            body=payload,
            query=query,
            headers=headers,
        )

    def auth_with_otp(
        self,
        otp_id: str,
        password: str,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, Any]:
        payload = dict(body or {})
        payload.setdefault("otpId", otp_id)
        payload.setdefault("password", password)

        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        data = self.client.send(
            f"{self.base_collection_path}/auth-with-otp",
            method="POST",
            body=payload,
            query=params,
            headers=headers,
        )
        return self._auth_response(data)

    def impersonate(
        self,
        record_id: str,
        duration: int,
        *,
        expand: Optional[str] = None,
        fields: Optional[str] = None,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[MutableMapping[str, str]] = None,
    ) -> BosBase:
        payload = dict(body or {})
        payload.setdefault("duration", duration)

        params = dict(query or {})
        if expand is not None:
            params.setdefault("expand", expand)
        if fields is not None:
            params.setdefault("fields", fields)

        enriched_headers = dict(headers or {})
        enriched_headers.setdefault("Authorization", self.client.auth_store.token)

        new_client = BosBase(self.client.base_url, lang=self.client.lang)
        data = new_client.send(
            f"{self.base_collection_path}/impersonate/{encode_path_segment(record_id)}",
            method="POST",
            body=payload,
            query=params,
            headers=enriched_headers,
        )
        new_client.auth_store.save(data.get("token", ""), data.get("record"))
        return new_client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _auth_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        token = data.get("token", "")
        record = data.get("record")
        if token and record:
            self.client.auth_store.save(token, record)
        return data

    def _maybe_update_auth_record(self, item: Dict[str, Any]) -> None:
        current = self.client.auth_store.record
        if not current:
            return
        if current.get("id") != item.get("id"):
            return
        if current.get("collectionId") not in (
            self.collection_id_or_name,
            current.get("collectionName"),
        ):
            return
        merged = dict(current)
        merged.update(item)
        if "expand" in current and "expand" in item:
            expand = dict(current["expand"])
            expand.update(item["expand"])
            merged["expand"] = expand
        self.client.auth_store.save(self.client.auth_store.token, merged)

    def _is_auth_record(self, record_id: str) -> bool:
        current = self.client.auth_store.record
        return bool(
            current
            and current.get("id") == record_id
            and current.get("collectionId") in (self.collection_id_or_name, current.get("collectionName"))
        )

    def _mark_verified(self, token: str) -> None:
        current = self.client.auth_store.record
        if not current:
            return
        payload = self._decode_token_payload(token)
        if (
            payload
            and current.get("id") == payload.get("id")
            and current.get("collectionId") == payload.get("collectionId")
            and not current.get("verified")
        ):
            current["verified"] = True
            self.client.auth_store.save(self.client.auth_store.token, current)

    def _clear_if_same_token(self, token: str) -> None:
        current = self.client.auth_store.record
        payload = self._decode_token_payload(token)
        if (
            current
            and payload
            and current.get("id") == payload.get("id")
            and current.get("collectionId") == payload.get("collectionId")
        ):
            self.client.auth_store.clear()

    @staticmethod
    def _decode_token_payload(token: str) -> Optional[Dict[str, Any]]:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_part = parts[1] + "=" * (-len(parts[1]) % 4)
        try:
            decoded = base64.urlsafe_b64decode(payload_part.encode("utf-8"))
            return json.loads(decoded.decode("utf-8"))
        except Exception:  # pragma: no cover - malformed tokens
            return None
