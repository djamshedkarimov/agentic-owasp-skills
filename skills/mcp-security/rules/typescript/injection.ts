import * as cp from "node:child_process";
import { exec, execFileSync, execSync as run, spawn } from "node:child_process";
import fs from "node:fs";
import { readFile } from "node:fs/promises";
import { basename, join, resolve, sep } from "node:path";
import vm from "node:vm";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import axios from "axios";
import { z } from "zod";

const server = new McpServer({ name: "fixture", version: "0.0.0" });
const ROOT = "/srv/data";
const ALLOWED_HOSTS = new Set(["api.example.com"]);
const result = (text: string) => ({ content: [{ type: "text" as const, text }] });
declare function validatePath(path: string, allowed: string[]): Promise<string>;

server.registerTool("shell_exec", { inputSchema: { host: z.string() } }, async ({ host }) => {
  // ruleid: mcp-shell-injection
  exec(`ping ${host}`);
  return result("ok");
});

// ruleid: mcp-shell-injection
server.registerTool("shell_alias", { inputSchema: { host: z.string() } }, async ({ host }) => result(run("ping " + host).toString()));

server.registerTool("shell_namespace", { inputSchema: { host: z.string() } }, async (args) => {
  // ruleid: mcp-shell-injection
  cp.execSync(`ping ${args.host}`);
  return result("ok");
});

server.registerTool("shell_spawn", { inputSchema: { host: z.string() } }, async ({ host }) => {
  // ruleid: mcp-shell-injection
  spawn(`ping ${host}`, [], { shell: true });
  return result("ok");
});

server.tool("shell_deprecated", { host: z.string() }, async ({ host }) => {
  // ruleid: mcp-shell-injection
  exec(`ping ${host}`);
  return result("ok");
});

server.registerTool("shell_argv", { inputSchema: { host: z.string() } }, async ({ host }) => {
  // ok: mcp-shell-injection
  return result(execFileSync("ping", ["-c", "1", host]).toString());
});

server.registerTool("regex_exec", { inputSchema: { text: z.string() } }, async ({ text }) => {
  // ok: mcp-shell-injection
  return result(String(/\d+/.exec(text)));
});

function notATool(host: string) {
  // ok: mcp-shell-injection
  exec(`ping ${host}`);
}

server.registerTool("code_eval", { inputSchema: { expression: z.string() } }, async ({ expression }) => {
  // ruleid: mcp-code-eval
  return result(String(eval(expression)));
});

server.registerTool("code_function", { inputSchema: { body: z.string() } }, async ({ body }) => {
  // ruleid: mcp-code-eval
  return result(String(new Function("x", body)(1)));
});

server.registerTool("code_vm", { inputSchema: { source: z.string() } }, async ({ source }) => {
  // ruleid: mcp-code-eval
  return result(String(vm.runInNewContext(source)));
});

server.registerTool("code_json", { inputSchema: { payload: z.string() } }, async ({ payload }) => {
  // ok: mcp-code-eval
  return result(JSON.stringify(JSON.parse(payload)));
});

server.registerTool("sql_template", { inputSchema: { email: z.string() } }, async ({ email }, extra) => {
  // ruleid: mcp-sql-injection
  const rows = db.prepare(`SELECT * FROM users WHERE email = '${email}'`).all();
  return result(JSON.stringify(rows));
});

server.registerTool("sql_pg", { inputSchema: { name: z.string() } }, async ({ name }) => {
  // ruleid: mcp-sql-injection
  const rows = await pool.query("SELECT * FROM users WHERE name = '" + name + "'");
  return result(JSON.stringify(rows));
});

server.registerTool("sql_prisma", { inputSchema: { id: z.string() } }, async ({ id }) => {
  // ruleid: mcp-sql-injection
  return result(JSON.stringify(await prisma.$queryRawUnsafe(`SELECT * FROM users WHERE id = ${id}`)));
});

server.registerTool("sql_bound", { inputSchema: { email: z.string() } }, async ({ email }) => {
  // ok: mcp-sql-injection
  const rows = db.prepare("SELECT * FROM users WHERE email = ?").all(email);
  return result(JSON.stringify(rows));
});

server.registerTool("path_join", { inputSchema: { name: z.string() } }, async ({ name }) => {
  // ruleid: mcp-path-traversal
  return result(await readFile(join(ROOT, name), "utf8"));
});

server.registerTool("path_fs", { inputSchema: { name: z.string() } }, async ({ name }) => {
  // ruleid: mcp-path-traversal
  fs.unlinkSync(`${ROOT}/${name}`);
  return result("deleted");
});

server.registerTool("path_contained", { inputSchema: { name: z.string() } }, async ({ name }) => {
  const path = resolve(ROOT, name);
  if (!path.startsWith(ROOT + sep)) throw new Error("outside root");
  // ok: mcp-path-traversal
  return result(await readFile(path, "utf8"));
});

server.registerTool("path_basename", { inputSchema: { name: z.string() } }, async ({ name }) => {
  // ok: mcp-path-traversal
  return result(fs.readFileSync(join(ROOT, basename(name)), "utf8"));
});

server.registerTool("path_validated", { inputSchema: { name: z.string() } }, async ({ name }) => {
  const path = await validatePath(name, [ROOT]);
  // ok: mcp-path-traversal
  return result(await readFile(path, "utf8"));
});

server.registerTool("ssrf_fetch", { inputSchema: { url: z.string() } }, async ({ url }) => {
  // ruleid: mcp-ssrf
  const response = await fetch(url);
  return result(await response.text());
});

server.registerTool("ssrf_axios", { inputSchema: { host: z.string() } }, async ({ host }) => {
  // ruleid: mcp-ssrf
  const response = await axios.get(`http://${host}/status`);
  return result(String(response.data));
});

server.registerTool("ssrf_allowlisted", { inputSchema: { url: z.string() } }, async ({ url }) => {
  const target = new URL(url);
  if (!ALLOWED_HOSTS.has(target.hostname)) throw new Error("host not allowed");
  // ok: mcp-ssrf
  const response = await fetch(target);
  return result(await response.text());
});

server.registerTool("ssrf_fixed", { inputSchema: { city: z.string() } }, async ({ city }) => {
  // ok: mcp-ssrf
  const response = await fetch("https://api.example.com/weather", { method: "POST", body: city });
  return result(await response.text());
});

server.registerTool("ssrf_compound_guard", { inputSchema: { url: z.string() } }, async ({ url }) => {
  const target = new URL(url);
  if (target.protocol !== "https:" || !ALLOWED_HOSTS.has(target.hostname)) throw new Error("host not allowed");
  // ok: mcp-ssrf
  const response = await fetch(target);
  return result(await response.text());
});

server.registerTool("ssrf_guard_other_url", { inputSchema: { url: z.string(), backup: z.string() } }, async ({ url, backup }) => {
  const target = new URL(url);
  if (!ALLOWED_HOSTS.has(target.hostname)) throw new Error("host not allowed");
  // ruleid: mcp-ssrf
  const response = await fetch(backup);
  return result(await response.text());
});

server.registerTool("ssrf_inline_guard", { inputSchema: { url: z.string() } }, async ({ url }) => {
  if (!ALLOWED_HOSTS.has(new URL(url).hostname)) throw new Error("host not allowed");
  // ok: mcp-ssrf
  const response = await fetch(url);
  return result(await response.text());
});
