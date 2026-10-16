import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve, sep } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { promisify } from "node:util";

import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";
import type { OAuthTokenVerifier } from "@modelcontextprotocol/sdk/server/auth/provider.js";
import type { AuthInfo } from "@modelcontextprotocol/sdk/server/auth/types.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { convert as htmlToText } from "html-to-text";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { z } from "zod";

import { textResult } from "./text-result.js";

const WORKSPACE = resolve("/srv/workspace");
const FETCH_ALLOWED_HOSTS = new Set(["docs.python.org", "developer.mozilla.org"]);
const OPERATORS = {
  "+": (a: number, b: number) => a + b,
  "-": (a: number, b: number) => a - b,
  "*": (a: number, b: number) => a * b,
  "/": (a: number, b: number) => a / b,
} as const;

const env = z
  .object({
    MCP_ISSUER_URL: z.url(),
    MCP_RESOURCE_URL: z.url(),
    MCP_JWKS_URL: z.url(),
    UPSTREAM_API_TOKEN: z.string().min(1),
    PORT: z.coerce.number().int().default(8000),
  })
  .parse(process.env);

const execFileAsync = promisify(execFile);
const jwks = createRemoteJWKSet(new URL(env.MCP_JWKS_URL));

const tokenVerifier: OAuthTokenVerifier = {
  async verifyAccessToken(token): Promise<AuthInfo> {
    const { payload } = await jwtVerify(token, jwks, { issuer: env.MCP_ISSUER_URL, audience: env.MCP_RESOURCE_URL });
    return {
      token,
      clientId: String(payload.client_id),
      scopes: typeof payload.scope === "string" ? payload.scope.split(" ") : [],
      expiresAt: payload.exp,
      resource: new URL(env.MCP_RESOURCE_URL),
    };
  },
};

function buildServer(): McpServer {
  const server = new McpServer({ name: "safe-example", version: "0.0.0" });

  server.registerTool(
    "run_diagnostic",
    {
      description: "Ping a host to check connectivity.",
      inputSchema: z.object({ target: z.union([z.hostname(), z.ipv4(), z.ipv6()]) }).strict(),
    },
    async ({ target }) => {
      // ok: mcp-shell-injection
      const { stdout } = await execFileAsync("ping", ["-c", "1", "--", target], { timeout: 10_000 });
      return textResult(stdout);
    },
  );

  server.registerTool(
    "calculate",
    {
      description: "Evaluate an arithmetic expression.",
      inputSchema: z.object({ left: z.number(), op: z.enum(["+", "-", "*", "/"]), right: z.number() }).strict(),
    },
    // ok: mcp-code-eval
    async ({ left, op, right }) => textResult(String(OPERATORS[op](left, right))),
  );

  server.registerTool(
    "find_user",
    { description: "Look up a user by email.", inputSchema: z.object({ email: z.email() }).strict() },
    async ({ email }) => {
      const db = new DatabaseSync("users.db");
      // ok: mcp-sql-injection
      const rows = db.prepare("SELECT id, name FROM users WHERE email = ?").all(email);
      return textResult(JSON.stringify(rows));
    },
  );

  server.registerTool(
    "read_note",
    {
      description: "Read a note from the workspace.",
      inputSchema: z.object({ filename: z.string().regex(/^[\w.-]{1,128}$/) }).strict(),
    },
    async ({ filename }) => {
      const path = resolve(WORKSPACE, filename);
      if (!path.startsWith(WORKSPACE + sep)) throw new Error("path escapes workspace");
      // ok: mcp-path-traversal
      return textResult(await readFile(path, "utf8"));
    },
  );

  server.registerTool(
    "fetch_page",
    { description: "Fetch a web page for summarization.", inputSchema: z.object({ url: z.url() }).strict() },
    async ({ url }) => {
      const target = new URL(url);
      if (target.protocol !== "https:" || !FETCH_ALLOWED_HOSTS.has(target.hostname)) throw new Error("host not allowed");
      // ok: mcp-ssrf
      const response = await fetch(target, { redirect: "error", signal: AbortSignal.timeout(10_000) });
      // ok: mcp-raw-html-return
      return textResult(htmlToText(await response.text()));
    },
  );

  server.registerTool(
    "sync_account",
    {
      description: "Sync an account with the upstream service.",
      inputSchema: z.object({ accountId: z.uuid() }).strict(),
    },
    async ({ accountId }) => {
      // ok: mcp-secret-in-log
      console.info(`syncing ${accountId}`);
      return textResult("synced");
    },
  );

  server.registerTool(
    "get_profile",
    { description: "Get the caller's profile from the upstream service." },
    async (extra) => {
      const response = await fetch("https://api.example.com/v1/profile", {
        // ok: mcp-token-passthrough
        headers: { Authorization: `Bearer ${env.UPSTREAM_API_TOKEN}`, "X-On-Behalf-Of": extra.authInfo?.clientId ?? "" },
      });
      return textResult(JSON.stringify(await response.json()));
    },
  );

  server.registerTool(
    "get_weather",
    { description: "Get the current weather for a city.", inputSchema: z.object({ city: z.string().max(100) }).strict() },
    async ({ city }) => textResult(`Sunny in ${city}`),
  );

  return server;
}

// ok: mcp-dns-rebinding
const app = createMcpExpressApp();

// ok: mcp-http-no-auth
app.post(
  "/mcp",
  requireBearerAuth({ verifier: tokenVerifier, expectedResource: new URL(env.MCP_RESOURCE_URL) }),
  async (req, res) => {
    const server = buildServer();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    res.on("close", () => {
      void transport.close();
      void server.close();
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  },
);

app.listen(env.PORT, "127.0.0.1");
