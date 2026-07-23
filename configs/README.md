# Registering the aleonard.us MCP server

The server runs over stdio via the launcher `bin/aleonard-mcp`, which sources
`env/local.env` (copy from `../env/dev.env.template`) and runs the venv. Point
`API_BASE_URL` at whichever API you want (local `http://127.0.0.1:8000`, dev, or
`https://api.aleonard.us`).

Registered in three tools:

## Claude Code

```bash
claude mcp add aleonard-us --scope user -- /Users/adam/dev/druthers-mcp/bin/aleonard-mcp
```

## Antigravity (`~/.gemini/config/mcp_config.json`)

See [`mcpServers.json`](mcpServers.json) — merge the `aleonard-us` entry into the
existing `mcpServers` map. (Claude Desktop uses the same format at
`~/Library/Application Support/Claude/claude_desktop_config.json`.)

## OpenCode (`~/.config/opencode/opencode.jsonc`)

See [`opencode.jsonc`](opencode.jsonc) — merge the `aleonard-us` entry into the
`mcp` map.

After editing, restart the tool (or reload MCP servers). Verify in Claude Code
with `claude mcp get aleonard-us` (expect "✔ Connected").
