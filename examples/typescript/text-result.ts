import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

export const textResult = (text: string): CallToolResult => ({ content: [{ type: "text", text }] });
