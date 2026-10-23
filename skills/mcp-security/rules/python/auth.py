import logging
import os

import httpx
import requests
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request

logger = logging.getLogger(__name__)


class TokenCache:
    pass


UPSTREAM = "https://api.example.com/me"

# ruleid: mcp-hardcoded-secret
SERVICE_API_KEY = "fixture-value-not-a-credential"
# ok: mcp-hardcoded-secret
API_KEY_ENV = "SERVICE_API_KEY"
# ok: mcp-hardcoded-secret
password = ""
# ok: mcp-hardcoded-secret
UPSTREAM_TOKEN = os.environ["UPSTREAM_TOKEN"]
# ok: mcp-hardcoded-secret
MAX_TOKENS = "4096-tokens-max"

# ruleid: mcp-hardcoded-secret
basic = httpx.BasicAuth(username="svc", password="fixture-value-not-a-credential")
# ok: mcp-hardcoded-secret
registration = dict(token_endpoint_auth_method="client_secret_post")

open_server = MCPServer("open")
authed_server = MCPServer("authed", token_verifier=None, auth=AuthSettings(issuer_url="https://auth.example.com"))
# ruleid: mcp-dns-rebinding
legacy = FastMCP("legacy", host="0.0.0.0")
# ok: mcp-dns-rebinding
legacy_local = FastMCP("legacy-local", host="127.0.0.1")


@open_server.tool()
def sync(account_id: str) -> str:
    # ruleid: mcp-secret-in-log
    logger.info("syncing %s with key %s", account_id, SERVICE_API_KEY)
    # ruleid: mcp-secret-in-log
    print(f"token={os.environ['UPSTREAM_TOKEN']}")
    # ok: mcp-secret-in-log
    logger.info("token refreshed for %s", account_id)
    # ok: mcp-secret-in-log
    logger.info("prompt used %d of %d", len(account_id), MAX_TOKENS)
    # ok: mcp-secret-in-log
    logger.debug("credential configured: %s", bool(SERVICE_API_KEY))
    response = httpx.post(UPSTREAM, data={"token": SERVICE_API_KEY})
    # ok: mcp-secret-in-log
    logger.debug("introspection returned %s", response.status_code)
    # ok: mcp-secret-in-log
    print(f"cache: {TokenCache()}")
    return "synced"


@open_server.tool()
def profile() -> dict:
    access = get_access_token()
    # ruleid: mcp-token-passthrough
    response = requests.get(UPSTREAM, headers={"Authorization": f"Bearer {access.token}"}, timeout=5)
    # ok: mcp-token-passthrough
    requests.post(UPSTREAM, headers={"X-Client": access.client_id}, timeout=5)
    return response.json()


async def forward(request: Request) -> str:
    async with httpx.AsyncClient() as http:
        # ruleid: mcp-token-passthrough
        response = await http.get(UPSTREAM, headers={"Authorization": request.headers["authorization"]})
    return response.text


def serve_open() -> None:
    # ruleid: mcp-dns-rebinding, mcp-http-no-auth
    open_server.run(transport="streamable-http", host="0.0.0.0")


def serve_env_host() -> None:
    # ruleid: mcp-dns-rebinding, mcp-http-no-auth
    open_server.run("sse", host=os.environ.get("HOST", "0.0.0.0"))


def serve_local() -> None:
    # ok: mcp-dns-rebinding
    # ruleid: mcp-http-no-auth
    open_server.run(transport="streamable-http")


def serve_protected() -> None:
    # ok: mcp-dns-rebinding, mcp-http-no-auth
    authed_server.run(
        transport="streamable-http",
        host="0.0.0.0",
        transport_security=TransportSecuritySettings(allowed_hosts=["mcp.example.com"]),
    )


def serve_stdio() -> None:
    # ok: mcp-http-no-auth
    open_server.run(transport="stdio")


def asgi_app() -> object:
    # ruleid: mcp-http-no-auth
    return open_server.streamable_http_app()
