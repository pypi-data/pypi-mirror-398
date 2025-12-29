from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, overload
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .errors import AuthError


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    token_type: str | None
    expires_in: int | None
    refresh_token: str | None
    scope: str | None
    issued_at: datetime
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TokenResponse":
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AuthError("Token response missing access_token")
        token_type = payload.get("token_type")
        expires_in = _as_int(payload.get("expires_in"))
        refresh_token = payload.get("refresh_token")
        scope = payload.get("scope")
        return cls(
            access_token=access_token,
            token_type=token_type if isinstance(token_type, str) else None,
            expires_in=expires_in,
            refresh_token=refresh_token if isinstance(refresh_token, str) else None,
            scope=scope if isinstance(scope, str) else None,
            issued_at=datetime.now(timezone.utc),
            raw=payload,
        )


@dataclass(frozen=True)
class AuthClientConfig:
    issuer: str | None
    client_id: str
    client_secret: str
    token_endpoint: str | None = None
    timeout_seconds: float = 10.0
    default_audience: str | None = None
    user_agent: str = "arp-auth/0.2.0"

    def resolved_token_endpoint(self) -> str:
        if self.token_endpoint:
            return self.token_endpoint
        if not self.issuer:
            raise AuthError("issuer or token_endpoint is required")
        return token_endpoint_from_issuer(self.issuer)


class AuthClient:
    def __init__(self, config: AuthClientConfig) -> None:
        self._config = config
        self._token_endpoint = config.resolved_token_endpoint()

    @classmethod
    def from_env(cls) -> "AuthClient":
        issuer = _read_env("ARP_AUTH_ISSUER", required=False)
        token_endpoint = _read_env("ARP_AUTH_TOKEN_ENDPOINT", required=False)
        client_id = _read_env("ARP_AUTH_CLIENT_ID")
        client_secret = _read_env("ARP_AUTH_CLIENT_SECRET")
        audience = _read_env("ARP_AUTH_AUDIENCE", required=False) or _read_env(
            "ARP_AUTH_SERVICE_ID", required=False
        )
        timeout_seconds = _read_env("ARP_AUTH_TIMEOUT_SECS", required=False)
        timeout = 10.0
        if timeout_seconds:
            try:
                timeout = float(timeout_seconds)
            except ValueError as exc:
                raise AuthError("ARP_AUTH_TIMEOUT_SECS must be a number") from exc
        config = AuthClientConfig(
            issuer=issuer,
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=token_endpoint,
            timeout_seconds=timeout,
            default_audience=audience,
        )
        return cls(config)

    def client_credentials(self, *, audience: str | None = None, scope: str | None = None) -> TokenResponse:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        if scope:
            payload["scope"] = scope
        resolved_audience = audience or self._config.default_audience
        if resolved_audience:
            payload["audience"] = resolved_audience
        return self._post_form(payload)

    def exchange_token(
        self,
        *,
        subject_token: str,
        audience: str | None = None,
        scope: str | None = None,
        subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
        requested_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
        actor_token: str | None = None,
    ) -> TokenResponse:
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "subject_token": subject_token,
            "subject_token_type": subject_token_type,
            "requested_token_type": requested_token_type,
        }
        if scope:
            payload["scope"] = scope
        resolved_audience = audience or self._config.default_audience
        if resolved_audience:
            payload["audience"] = resolved_audience
        if actor_token:
            payload["actor_token"] = actor_token
            payload["actor_token_type"] = "urn:ietf:params:oauth:token-type:access_token"
        return self._post_form(payload)

    def refresh_token(self, *, refresh_token: str, scope: str | None = None) -> TokenResponse:
        payload = {
            "grant_type": "refresh_token",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "refresh_token": refresh_token,
        }
        if scope:
            payload["scope"] = scope
        return self._post_form(payload)

    def _post_form(self, payload: dict[str, str]) -> TokenResponse:
        data = urlencode(payload).encode("utf-8")
        request = Request(self._token_endpoint, data=data, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", self._config.user_agent)
        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                return _parse_token_response(response.read())
        except HTTPError as exc:
            return _raise_from_http_error(exc)


def token_endpoint_from_issuer(issuer: str) -> str:
    issuer = issuer.rstrip("/")
    return f"{issuer}/protocol/openid-connect/token"


def _parse_token_response(raw: bytes) -> TokenResponse:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthError("Token response was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise AuthError("Token response must be a JSON object")
    return TokenResponse.from_dict(payload)


def _raise_from_http_error(exc: HTTPError) -> TokenResponse:
    try:
        raw = exc.read()
    except Exception:
        raw = b""
    payload: dict[str, Any] = {}
    if raw:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {"raw": raw.decode("utf-8", errors="replace")}
    raise AuthError(
        "Token request failed",
        status_code=exc.code,
        error=_as_str(payload.get("error")),
        error_description=_as_str(payload.get("error_description")),
        details=payload if payload else None,
    )


@overload
def _read_env(name: str, *, required: Literal[True] = True) -> str:
    ...


@overload
def _read_env(name: str, *, required: Literal[False]) -> str | None:
    ...


def _read_env(name: str, *, required: bool = True) -> str | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        if required:
            raise AuthError(f"Missing required env var: {name}")
        return None
    return value.strip()


def _as_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _as_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None
