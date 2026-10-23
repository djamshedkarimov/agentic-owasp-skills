import asyncio
import os
import shlex
import sqlite3
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import httpx
import mcp.types as types
import requests
from fastmcp import FastMCP as StandaloneFastMCP
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel import Server
from mcp.server.mcpserver import MCPServer

ROOT = Path("/srv/data")
ALLOWED_HOSTS = {"api.example.com"}
SETTINGS = {"region": "eu"}

v2 = MCPServer("v2")
v1 = FastMCP("v1")
standalone = StandaloneFastMCP("standalone")
lowlevel = Server("lowlevel")
opener = urllib.request.build_opener()


def validate_path(name: str, root: Path) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("outside root")
    return path


@v2.tool()
def shell_run(host: str) -> str:
    # ruleid: mcp-shell-injection
    return subprocess.run(f"ping {host}", shell=True, capture_output=True, text=True).stdout


@v1.tool()
def shell_system(host: str) -> int:
    # ruleid: mcp-shell-injection
    return os.system("ping " + host)


@standalone.tool
async def shell_async(host: str) -> None:
    # ruleid: mcp-shell-injection
    await asyncio.create_subprocess_shell(f"ping {host}")


@v2.tool()
def shell_argv(host: str) -> str:
    # ok: mcp-shell-injection
    return subprocess.run(["ping", "-c", "1", host], capture_output=True, text=True).stdout


@v2.tool()
def shell_quoted(host: str) -> str:
    # ok: mcp-shell-injection
    return subprocess.check_output(f"ping {shlex.quote(host)}", shell=True, text=True)


def not_a_tool(host: str) -> int:
    # ok: mcp-shell-injection
    return os.system("ping " + host)


@v2.tool()
def code_eval(expression: str) -> str:
    # ruleid: mcp-code-eval
    return str(eval(expression))


@v1.tool()
def code_exec(source: str) -> None:
    # ruleid: mcp-code-eval
    exec(source)


@v2.tool()
def code_constant() -> str:
    # ok: mcp-code-eval
    return str(eval("1 + 1"))


@v2.tool()
def sql_fstring(email: str) -> list:
    with sqlite3.connect("app.db") as db:
        # ruleid: mcp-sql-injection
        return db.execute(f"SELECT * FROM users WHERE email = '{email}'").fetchall()


@standalone.tool
def sql_concat(name: str) -> None:
    cursor = sqlite3.connect("app.db").cursor()
    query = "DELETE FROM users WHERE name = '" + name + "'"
    # ruleid: mcp-sql-injection
    cursor.execute(query)


@v2.tool()
def sql_bound(email: str) -> list:
    with sqlite3.connect("app.db") as db:
        # ok: mcp-sql-injection
        return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchall()


@v2.tool()
def path_join(name: str) -> str:
    # ruleid: mcp-path-traversal
    return (ROOT / name).read_text()


@v1.tool()
def path_open(name: str) -> str:
    # ruleid: mcp-path-traversal
    with open(os.path.join("/srv/data", name)) as handle:
        return handle.read()


@v2.tool()
def path_contained(name: str) -> str:
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("outside root")
    # ok: mcp-path-traversal
    return path.read_text()


@v2.tool()
def path_basename(name: str) -> str:
    # ok: mcp-path-traversal
    return (ROOT / os.path.basename(name)).read_text()


@v2.tool()
def path_validated(name: str) -> str:
    path = validate_path(name, ROOT)
    # ok: mcp-path-traversal
    return path.read_text()


@v2.tool()
def ssrf_urlopen(url: str) -> bytes:
    # ruleid: mcp-ssrf
    return urllib.request.urlopen(url).read()


@v1.tool()
def ssrf_requests(url: str) -> str:
    # ruleid: mcp-ssrf
    return requests.get(url, timeout=5).text


@standalone.tool
async def ssrf_httpx_client(path: str) -> str:
    async with httpx.AsyncClient() as client:
        # ruleid: mcp-ssrf
        response = await client.get(f"http://{path}")
    return response.text


@v2.tool()
def ssrf_opener(url: str) -> bytes:
    # ruleid: mcp-ssrf
    return opener.open(url).read()


@v2.tool()
def ssrf_allowlisted(url: str) -> bytes:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise ValueError("host not allowed")
    # ok: mcp-ssrf
    return opener.open(url).read()


@v2.tool()
def ssrf_fixed_host(region: str) -> str:
    # ok: mcp-ssrf
    return SETTINGS.get(region, "unknown")


@v2.tool()
def ssrf_inline_guard(url: str) -> str:
    if urllib.parse.urlsplit(url).hostname not in ALLOWED_HOSTS:
        raise ValueError("host not allowed")
    # ok: mcp-ssrf
    return requests.get(url, timeout=5).text


@lowlevel.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "ping":
        # ruleid: mcp-shell-injection
        output = subprocess.run(f"ping {arguments['host']}", shell=True, capture_output=True, text=True).stdout
        return [types.TextContent(type="text", text=output)]
    # ruleid: mcp-path-traversal
    return [types.TextContent(type="text", text=(ROOT / arguments["name"]).read_text())]
