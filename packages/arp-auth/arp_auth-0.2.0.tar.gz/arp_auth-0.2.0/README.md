# ARP Auth

Auth helpers for ARP components. This package provides a small, dependency-free
OIDC client for client-credentials and token-exchange flows (Keycloak-friendly).

## Install

```bash
pip install arp-auth
```

## Quick start (client credentials)

```python
from arp_auth import AuthClient, AuthClientConfig

config = AuthClientConfig(
    issuer="http://localhost:8080/realms/arp-dev",
    client_id="arp-run-gateway",
    client_secret="arp-run-gateway-secret",
)
client = AuthClient(config)

token = client.client_credentials(audience="arp-run-coordinator")
print(token.access_token)
```

## Token exchange

```python
from arp_auth import AuthClient, AuthClientConfig

client = AuthClient(
    AuthClientConfig(
        issuer="http://localhost:8080/realms/arp-dev",
        client_id="arp-run-gateway",
        client_secret="arp-run-gateway-secret",
    )
)

exchanged = client.exchange_token(
    subject_token="<incoming-user-jwt>",
    audience="arp-run-coordinator",
)
print(exchanged.access_token)
```

## Environment-based config

Use `AuthClient.from_env()` with:

- `ARP_AUTH_ISSUER` (example: `http://localhost:8080/realms/arp-dev`)
- `ARP_AUTH_CLIENT_ID`
- `ARP_AUTH_CLIENT_SECRET`
- `ARP_AUTH_TOKEN_ENDPOINT` (optional override; defaults to issuer + `/protocol/openid-connect/token`)
- `ARP_AUTH_AUDIENCE` or `ARP_AUTH_SERVICE_ID` (optional default audience)
- `ARP_AUTH_TIMEOUT_SECS` (optional; default `10`)

## Notes

- This library does not cache or refresh tokens automatically; callers should cache tokens
  and refresh based on `expires_in` in `TokenResponse`.
- For local dev, use `arp-sts-keycloak` to stand up a Keycloak realm with ARP clients.
