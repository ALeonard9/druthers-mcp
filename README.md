# aleonard.us-mcp

An [MCP](https://modelcontextprotocol.io) server that exposes the personal
[aleonard.us](https://www.aleonard.us) trackers as tools, so an LLM (e.g. Claude)
can manage them on your behalf. Backed by
[`aleonard.us-api`](https://github.com/ALeonard9/aleonard.us-api). First slice:
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
claude mcp add aleonard-us --scope user -- /Users/adam/dev/aleonard.us-mcp/bin/aleonard-mcp
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

## Register with Claude

Claude Desktop / Claude Code — add to your MCP config:

```json
{
  "mcpServers": {
    "aleonard-us": {
      "command": "python",
      "args": ["-m", "aleonard_mcp.server"],
      "env": {
        "API_BASE_URL": "http://127.0.0.1:8000",
        "API_EMAIL": "you@example.com",
        "API_PASSWORD": "..."
      }
    }
  }
}
```

Or run the container (`ghcr.io/aleonard9/aleonard.us-mcp`) with the same env.

## Config

| Var | Description |
|-----|-------------|
| `API_BASE_URL` | Base URL of `aleonard.us-api`. |
| `API_TOKEN` | Pre-issued bearer token (alternative to email/password). |
| `API_EMAIL` / `API_PASSWORD` | Credentials exchanged for a token. |
| `LOG_LEVEL`, `LZ`, `ENV` | Logging / landing-zone metadata. |

## Develop

`task test` (pytest), `task lint` (pylint), `task format` (black). CI runs
lint + black + pytest; `publish_docker.yaml` pushes to GHCR on release.
