import ipaddress
import logging
import operator
import os
import re
import sqlite3
import subprocess
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal

import jwt
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

WORKSPACE = Path("/srv/workspace").resolve()
ISSUER_URL = os.environ["MCP_ISSUER_URL"]
RESOURCE_URL = os.environ["MCP_RESOURCE_URL"]
FETCH_ALLOWED_HOSTS = frozenset({"docs.python.org", "developer.mozilla.org"})
HOSTNAME = re.compile(r"^(?=.{1,253}$)([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9-]{1,63}$")
OPERATORS = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}

logger = logging.getLogger(__name__)


class JwtTokenVerifier:
    def __init__(self, public_key: str) -> None:
        self._public_key = public_key

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            claims = jwt.decode(token, self._public_key, algorithms=["RS256"], audience=RESOURCE_URL, issuer=ISSUER_URL)
        except jwt.InvalidTokenError:
            return None
        return AccessToken(
            token=token,
            client_id=claims["client_id"],
            scopes=claims.get("scope", "").split(),
            expires_at=claims["exp"],
            resource=RESOURCE_URL,
            subject=claims.get("sub"),
        )


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.chunks.append(data.strip())


FETCH_OPENER = urllib.request.build_opener(_RejectRedirects)

mcp = MCPServer(
    "safe-example",
    token_verifier=JwtTokenVerifier(os.environ["MCP_JWT_PUBLIC_KEY"]),
    auth=AuthSettings(
        issuer_url=ISSUER_URL,
        resource_server_url=RESOURCE_URL,
        required_scopes=["notes:read"],
        validate_token_resource=True,
    ),
)


@mcp.tool()
def run_diagnostic(target: str) -> str:
    """Ping a host to check connectivity."""
    if not HOSTNAME.fullmatch(target):
        ipaddress.ip_address(target)
    # ok: mcp-shell-injection
    return subprocess.run(["ping", "-c", "1", "--", target], capture_output=True, text=True, timeout=10).stdout


@mcp.tool()
def calculate(left: float, op: Literal["+", "-", "*", "/"], right: float) -> str:
    """Evaluate an arithmetic expression."""
    # ok: mcp-code-eval
    return str(OPERATORS[op](left, right))


@mcp.tool()
def find_user(email: str) -> list[tuple]:
    """Look up a user by email."""
    with sqlite3.connect("users.db") as db:
        # ok: mcp-sql-injection
        return db.execute("SELECT id, name FROM users WHERE email = ?", (email,)).fetchall()


@mcp.tool()
def read_note(filename: str) -> str:
    """Read a note from the workspace."""
    path = (WORKSPACE / filename).resolve()
    if not path.is_relative_to(WORKSPACE):
        raise ValueError("path escapes workspace")
    # ok: mcp-path-traversal
    return path.read_text()


@mcp.tool()
def fetch_page(url: str) -> str:
    """Fetch a web page for summarization."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in FETCH_ALLOWED_HOSTS:
        raise ValueError("host not allowed")
    # ok: mcp-ssrf
    with FETCH_OPENER.open(url, timeout=10) as response:
        extractor = _TextExtractor()
        extractor.feed(response.read(1_000_000).decode(errors="replace"))
    # ok: mcp-raw-html-return
    return "\n".join(extractor.chunks)


@mcp.tool()
def sync_account(account_id: str) -> str:
    """Sync an account with the upstream service."""
    # ok: mcp-secret-in-log
    logger.info("syncing account %s", account_id)
    return "synced"


@mcp.tool(description="Get the current weather for a city.")
def get_weather(city: str) -> str:
    return f"Sunny in {city}"


if __name__ == "__main__":
    # ok: mcp-dns-rebinding, mcp-http-no-auth
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        transport_security=TransportSecuritySettings(
            allowed_hosts=["127.0.0.1:*", "localhost:*"],
            allowed_origins=["http://localhost:*"],
        ),
    )
