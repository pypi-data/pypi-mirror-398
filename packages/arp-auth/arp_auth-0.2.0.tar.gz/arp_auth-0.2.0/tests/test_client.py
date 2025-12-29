import json
import os
from urllib.parse import parse_qs

import pytest

from arp_auth.client import AuthClient, AuthClientConfig, TokenResponse, token_endpoint_from_issuer
from arp_auth.errors import AuthError


class _Response:
    def __init__(self, payload: dict) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
        return False


def test_token_endpoint_from_issuer_trims_slash() -> None:
    endpoint = token_endpoint_from_issuer("http://localhost:8080/realms/arp-dev/")
    assert endpoint == "http://localhost:8080/realms/arp-dev/protocol/openid-connect/token"


def test_token_response_missing_access_token() -> None:
    with pytest.raises(AuthError):
        TokenResponse.from_dict({"token_type": "bearer"})


def test_from_env_requires_required_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARP_AUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("ARP_AUTH_CLIENT_SECRET", raising=False)
    with pytest.raises(AuthError):
        AuthClient.from_env()


def test_from_env_resolves_token_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARP_AUTH_ISSUER", "http://localhost:8080/realms/arp-dev")
    monkeypatch.setenv("ARP_AUTH_CLIENT_ID", "arp-run-gateway")
    monkeypatch.setenv("ARP_AUTH_CLIENT_SECRET", "secret")
    client = AuthClient.from_env()
    assert client._token_endpoint.endswith("/protocol/openid-connect/token")


def test_client_credentials_includes_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def _fake_urlopen(request, timeout=10):  # type: ignore[no-untyped-def]
        data = request.data.decode("utf-8") if request.data else ""
        captured["payload"] = parse_qs(data)
        return _Response({"access_token": "token", "token_type": "bearer"})

    monkeypatch.setattr("arp_auth.client.urlopen", _fake_urlopen)
    client = AuthClient(
        AuthClientConfig(
            issuer="http://localhost:8080/realms/arp-dev",
            client_id="arp-run-gateway",
            client_secret="secret",
            default_audience="arp-run-coordinator",
        )
    )
    token = client.client_credentials()
    assert token.access_token == "token"
    assert captured["payload"]["audience"] == ["arp-run-coordinator"]
