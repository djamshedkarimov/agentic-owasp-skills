import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";
import type { OAuthTokenVerifier } from "@modelcontextprotocol/sdk/server/auth/provider.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import axios from "axios";
import express from "express";

declare const verifier: OAuthTokenVerifier;
const server = new McpServer({ name: "fixture", version: "0.0.0" });
const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
const result = (text: string) => ({ content: [{ type: "text" as const, text }] });
const UPSTREAM_URL = "https://api.example.com/introspect";
class TokenCache {}

// ruleid: mcp-hardcoded-secret
const SERVICE_API_KEY = "fixture-value-not-a-credential";
// ok: mcp-hardcoded-secret
const API_KEY_ENV = "SERVICE_API_KEY";
// ok: mcp-hardcoded-secret
const password = "";
// ok: mcp-hardcoded-secret
const maxTokens = "4096-tokens-max";
// ok: mcp-hardcoded-secret
const upstreamToken = process.env.UPSTREAM_TOKEN;
const client = axios.create({
  // ruleid: mcp-hardcoded-secret
  auth: { username: "svc", password: "fixture-value-not-a-credential" },
});
// ok: mcp-hardcoded-secret
const registration = { token_endpoint_auth_method: "client_secret_post" };

server.registerTool("sync", { description: "Sync an account." }, async (extra) => {
  // ruleid: mcp-secret-in-log
  console.info(`syncing ${extra.sessionId} with key ${SERVICE_API_KEY}`);
  // ruleid: mcp-secret-in-log
  console.log("token", process.env["UPSTREAM_TOKEN"]);
  // ruleid: mcp-secret-in-log
  console.debug("caller", extra.authInfo?.token);
  // ok: mcp-secret-in-log
  console.info("token refreshed", extra.sessionId);
  // ok: mcp-secret-in-log
  console.info("budget", maxTokens, API_KEY_ENV);
  // ok: mcp-secret-in-log
  console.info("configured", Boolean(upstreamToken));
  const response = await axios.post(UPSTREAM_URL, { token: upstreamToken });
  // ok: mcp-secret-in-log
  console.debug("introspection returned", response.status);
  // ok: mcp-secret-in-log
  console.info("cache", new TokenCache());
  return result("synced");
});

server.registerTool("profile", { description: "Get the caller's profile." }, async (extra) => {
  const response = await fetch("https://api.example.com/me", {
    // ruleid: mcp-token-passthrough
    headers: { Authorization: `Bearer ${extra.authInfo?.token}` },
  });
  // ok: mcp-token-passthrough
  await fetch("https://audit.example.com", { method: "POST", headers: { "X-Client": extra.authInfo?.clientId ?? "" } });
  const headers = new Headers();
  // ruleid: mcp-token-passthrough
  headers.set("Authorization", `Bearer ${extra.authInfo?.token}`);
  // ok: mcp-token-passthrough
  headers.set("Authorization", `Bearer ${upstreamToken}`);
  await client.get("https://api.example.com/me", { headers });
  return result(await response.text());
});

const openApp = express();
openApp.use(express.json());
// ruleid: mcp-http-no-auth
openApp.post("/mcp", async (req, res) => {
  // ruleid: mcp-token-passthrough
  await axios.get("https://api.example.com/me", { headers: { authorization: req.headers.authorization } });
  await transport.handleRequest(req, res, req.body);
});

// ok: mcp-http-no-auth
openApp.post("/mcp", requireBearerAuth({ verifier }), async (req, res) => {
  await transport.handleRequest(req, res, req.body);
});

// ok: mcp-http-no-auth
openApp.get("/health", (_req, res) => res.send("ok"));

const guardedApp = express();
guardedApp.use(requireBearerAuth({ verifier }));
// ok: mcp-http-no-auth
guardedApp.post("/mcp", async (req, res) => {
  await transport.handleRequest(req, res, req.body);
});

// ruleid: mcp-dns-rebinding
createMcpExpressApp({ host: "0.0.0.0" });
// ruleid: mcp-dns-rebinding
createMcpExpressApp({ host: process.env.HOST ?? "::" });
// ok: mcp-dns-rebinding
createMcpExpressApp({ host: "0.0.0.0", allowedHosts: ["mcp.example.com"] });
// ok: mcp-dns-rebinding
createMcpExpressApp({ host: "localhost" });
// ok: mcp-dns-rebinding
createMcpExpressApp();
