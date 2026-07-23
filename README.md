# Druthers MCP

> **[Druthers](https://druthers.io)** is social taste-sharing for the things you love —
> **Movies, TV, Books, and Games**.

This is a [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes your Druthers library as **tools**, so an assistant like Claude can search,
track, and annotate on your behalf — "add *Dune* to my watchlist", "mark episode 3
watched", "what games have I 100%'d?". Backed by
[`druthers-api`](https://github.com/ALeonard9/druthers-api).

## Tools

The server exposes a consistent set of tools across every domain — **movies, tv,
books, games**:

| Verb | Example | What it does |
|---|---|---|
| `search_*` | `search_movies("dune")` | Find titles in the external catalog |
| `add_*` | `add_book(...)` | Add an item to your library |
| `list_my_*` | `list_my_games()` | List your tracked items with status + notes |
| `*_detail` | `tv_show_detail(id)` | Full metadata for one item |
| `mark_*` | `mark_watched` · `mark_episode_watched` · `mark_game_100_percent` | Update status |
| `set_*` | `set_note` · `set_completed_date` | Personal notes and completion dates |

## Add it to Claude

Register the stdio server — it shows up in your client as **`druthers`**
(`mcp__druthers__*` tools):

```bash
# Claude Code (local checkout)
claude mcp add druthers --scope user -- /path/to/druthers-mcp/bin/aleonard-mcp

# Claude Desktop / Code (containerized, pointed at prod)
claude mcp add druthers \
  -e API_BASE_URL=https://api.druthers.io \
  -e API_TOKEN=drk_... \
  -- python -m aleonard_mcp.server
```

Or run the published image `ghcr.io/aleonard9/druthers-mcp` with the same env.

## Authentication — use an API key

Point the server at a real environment with a personal **API key** (not your password):

```bash
curl -X POST https://api.druthers.io/v1/users/me/api-keys \
  -H "Authorization: Bearer <your-jwt>" -H "Content-Type: application/json" \
  -d '{"name": "laptop mcp"}'
```

Copy the `drk_…` key from the response (**shown once**) into `API_TOKEN`. Keys
don't expire; revoke any time with `DELETE /v1/users/me/api-keys/{id}`.

## Run locally

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp env/dev.env.template env/dev.env          # set API_BASE_URL + API_TOKEN
set -a && . env/dev.env && set +a
python -m aleonard_mcp.server                # stdio server
# or explore: mcp dev aleonard_mcp/server.py
```

Against a local `druthers-api` (`API_BASE_URL=http://127.0.0.1:8000`), an
email/password pair also works.

| Env var | Description |
|---|---|
| `API_BASE_URL` | Base URL of `druthers-api` |
| `API_TOKEN` | Personal API key (`drk_…`) — preferred |
| `API_EMAIL` / `API_PASSWORD` | Local-dev fallback credentials |

## Develop

`task test` (pytest) · `task lint` (pylint) · `task format` (black). Pre-commit runs
Gitleaks + lint on commit; tests run at pre-push (changed-only). CI runs the full
suite, and Gitleaks/Semgrep/Trivy scan every PR.

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
