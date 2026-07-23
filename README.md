# druthers-mcp

An [MCP](https://modelcontextprotocol.io) server that exposes the personal
[aleonard.us](https://www.aleonard.us) trackers as tools, so an LLM (e.g. Claude)
can manage them on your behalf. Backed by
[`druthers-api`](https://github.com/ALeonard9/druthers-api). First slice:
**Movies**.

## Tools

| Tool | Description |
|------|-------------|
| `search_movies(query)` | Search the catalog (OMDB proxy) by title. |
| `list_my_movies()` | List your tracked movies with watched status + notes. |
| `movie_detail(movie_id)` | Full detail: plot, director, cast, genre, year, rating. |
| `add_movie(imdb_id, title, poster_url?)` | Add a movie to your watchlist. |
| `mark_watched(movie_id, watched=True)` | Toggle a movie's watched flag. |
| `set_note(movie_id, note)` | Set your personal note on a movie. |

## Register it (Claude, Antigravity, OpenCode)

The launcher `bin/aleonard-mcp` sources `env/local.env` and runs the server over
stdio. See [`configs/`](configs/) for per-tool snippets. Quick start for Claude Code:

```bash
claude mcp add aleonard-us --scope user -- /Users/adam/dev/druthers-mcp/bin/aleonard-mcp
```

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp env/dev.env.template env/dev.env      # set API_BASE_URL + creds

# stdio server:
set -a && . env/dev.env && set +a
python -m aleonard_mcp.server

# or explore with the MCP Inspector:
mcp dev aleonard_mcp/server.py
```

## Get an API key (recommended auth)

The clean way to point this server at a real environment is a personal
**API key** instead of your password:

1. Sign in to the site and mint a key (or via curl):
   ```bash
   curl -X POST https://api.druthers.io/v1/users/me/api-keys \
     -H "Authorization: Bearer <your-jwt>" \
     -H "Content-Type: application/json" -d '{"name": "laptop mcp"}'
   ```
2. Copy the `key` from the response (`drk_…`) — **it is shown exactly once**.
3. Use it as `API_TOKEN` below. Keys don't expire; revoke one any time with
   `DELETE /v1/users/me/api-keys/{id}` and it stops working immediately.

## Register with Claude

Claude Desktop / Claude Code — add to your MCP config:

```json
{
  "mcpServers": {
    "aleonard-us": {
      "command": "python",
      "args": ["-m", "aleonard_mcp.server"],
      "env": {
        "API_BASE_URL": "https://api.druthers.io",
        "API_TOKEN": "drk_..."
      }
    }
  }
}
```

- **Claude Code (CLI):** `claude mcp add aleonard-us -e API_BASE_URL=https://api.druthers.io -e API_TOKEN=drk_... -- python -m aleonard_mcp.server`
- **claude.ai / mobile:** custom connectors need a remote MCP endpoint — not
  this stdio server. Until a remote transport ships, use Desktop/Code.
- **Local dev:** point `API_BASE_URL` at `http://127.0.0.1:8000` — the
  email/password pair still works there (`env/dev.env.template`).

Or run the container (`ghcr.io/aleonard9/druthers-mcp`) with the same env.

## Config

| Var | Description |
|-----|-------------|
| `API_BASE_URL` | Base URL of `druthers-api`. |
| `API_TOKEN` | Personal API key (`drk_…`, mint above) or any pre-issued bearer token. Preferred. |
| `API_EMAIL` / `API_PASSWORD` | Credentials exchanged for a token (local dev fallback). |
| `LOG_LEVEL`, `LZ`, `ENV` | Logging / landing-zone metadata. |

## Develop

`task test` (pytest), `task lint` (pylint), `task format` (black). CI runs
lint + black + pytest; `publish_docker.yaml` pushes to GHCR on release.
