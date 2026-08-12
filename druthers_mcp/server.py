"""
Druthers MCP server.

Exposes the personal media trackers (Movies, TV, Books) as MCP
tools backed by the Druthers API, so an LLM (e.g. Claude) can search,
list, add, and annotate them on the user's behalf — including TV episode
watch marks. Runs over stdio.
"""

import logging
from typing import Optional

try:
    from mcp.server.fastmcp import (
        FastMCP,
    )  # pylint: disable=import-error,no-name-in-module
except ImportError:
    try:
        from mcp.server import FastMCP  # pylint: disable=import-error,no-name-in-module
    except ImportError:
        from mcp.server import (
            MCPServer as FastMCP,
        )  # pylint: disable=import-error,no-name-in-module

from druthers_mcp.api_client import ApiClient, ApiError
from druthers_mcp.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger("druthers_mcp")

if settings.env != "prod":
    logger.warning(
        "Running in %s environment against %s", settings.env, settings.api_base_url
    )
else:
    logger.info(
        "Running in %s environment against %s", settings.env, settings.api_base_url
    )

mcp = FastMCP("druthers")

_client: Optional[ApiClient] = None


def client() -> ApiClient:
    """Return a lazily-initialized, reused API client."""
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = ApiClient()
    return _client


@mcp.tool()
def search_movies(query: str) -> list[dict]:
    """
    Search for movies by title. Returns catalog candidates with their tmdb id,
    title, year and poster. Use the tmdb id + title with `add_movie`.
    """
    try:
        return client().search_movies(query)
    except ApiError as err:
        if err.status == 503:
            return [{"error": "Movie search is not configured on the server."}]
        raise


@mcp.tool()
def list_my_movies() -> list[dict]:
    """
    List the movies the user is tracking, with watched status and notes.
    """
    movies = client().list_my_movies()
    return [
        {
            "movie_id": m["movie"]["id"],
            "title": m["movie"]["title"],
            "watched": m.get("completed") == 1,
            "notes": m.get("notes"),
            "completed_at": m.get("completed_at"),
            "rank": m.get("rank"),
        }
        for m in movies
    ]


@mcp.tool()
def movie_detail(movie_id: str) -> dict:
    """
    Get full detail for a movie (plot, director, cast, genre, year, runtime,
    rating). `movie_id` is the id from `list_my_movies`.
    """
    return client().get_movie_detail(movie_id)


@mcp.tool()
def add_movie(tmdb_id: int, title: str, poster_url: Optional[str] = None) -> str:
    """
    Add a movie to the user's list (as a watchlist item). Provide the tmdb id
    and title, e.g. from `search_movies`.
    """
    client().add_movie(tmdb_id, title, poster_url)
    return f'Added "{title}" to your watchlist.'


@mcp.tool()
def mark_watched(movie_id: str, watched: bool = True) -> str:
    """
    Mark a tracked movie as watched (or not). `movie_id` is the id from
    `list_my_movies`.
    """
    client().update_tracker(movie_id, completed=1 if watched else 0)
    return f'Marked movie {movie_id} as {"watched" if watched else "unwatched"}.'


@mcp.tool()
def set_note(movie_id: str, note: str) -> str:
    """
    Set (or replace) your personal note on a tracked movie. `movie_id` is the id
    from `list_my_movies`.
    """
    client().update_tracker(movie_id, notes=note)
    return f"Updated notes for movie {movie_id}."


@mcp.tool()
def search_tv_shows(query: str) -> list[dict]:
    """
    Search for TV shows by title. Returns candidates with their TVMaze id,
    imdb id, title, year, status, and network. Use the TVMaze id + title with
    `add_tv_show`.
    """
    return client().search_tv_shows(query)


@mcp.tool()
def list_my_tv_shows() -> list[dict]:
    """
    List the TV shows the user is tracking, with list membership (watchlist /
    rankings), rank, and notes.
    """
    shows = client().list_my_tv_shows()
    return [
        {
            "show_id": s["tv_show"]["id"],
            "title": s["tv_show"]["title"],
            "status": s["tv_show"].get("status"),
            "on_watchlist": s.get("on_watchlist"),
            "on_rankings": s.get("on_rankings"),
            "rank": s.get("rank"),
            "notes": s.get("notes"),
            "completed_at": s.get("completed_at"),
        }
        for s in shows
    ]


@mcp.tool()
def tv_show_detail(show_id: str) -> dict:
    """
    Get full detail for a TV show (summary, genres, network, premiere year,
    status, rating). `show_id` is the id from `list_my_tv_shows`.
    """
    return client().get_tv_show_detail(show_id)


@mcp.tool()
def add_tv_show(
    tvmaze_id: int,
    title: str,
    imdb_id: Optional[str] = None,
    poster_url: Optional[str] = None,
) -> str:
    """
    Add a TV show to the user's watchlist. Provide the TVMaze id and title,
    e.g. from `search_tv_shows`.
    """
    client().add_tv_show(tvmaze_id, title, imdb_id, poster_url)
    return f'Added "{title}" to your TV watchlist.'


@mcp.tool()
def set_tv_note(show_id: str, note: str) -> str:
    """
    Set (or replace) your personal note on a tracked TV show. `show_id` is the
    id from `list_my_tv_shows`.
    """
    client().update_tv_tracker(show_id, notes=note)
    return f"Updated notes for TV show {show_id}."


@mcp.tool()
def show_episodes(show_id: str, season: Optional[int] = None) -> list[dict]:
    """
    List a tracked show's episodes (optionally one season) with the user's
    watched flag on each. `show_id` is the id from `list_my_tv_shows`.
    """
    episodes = client().list_show_episodes(show_id)
    watched_ids = {
        m["episode"]["id"]
        for m in client().list_my_episode_marks(show_id)
        if m.get("watched")
    }
    return [
        {
            "episode_id": e["id"],
            "season": e.get("season"),
            "episode": e.get("season_number"),
            "title": e["title"],
            "airdate": e.get("airdate"),
            "watched": e["id"] in watched_ids,
        }
        for e in episodes
        if season is None or e.get("season") == season
    ]


@mcp.tool()
def mark_episode_watched(episode_id: str, watched: bool = True) -> str:
    """
    Mark a TV episode watched (or clear the mark). `episode_id` is the id from
    `show_episodes`.
    """
    if watched:
        client().mark_episode(episode_id)
    else:
        client().unmark_episode(episode_id)
    return f'Marked episode {episode_id} as {"watched" if watched else "unwatched"}.'


@mcp.tool()
def search_books(query: str) -> list[dict]:
    """
    Search for books by title/author. Returns candidates with their isbn,
    title, authors, year, and cover. Use the isbn + title with `add_book`.
    """
    return client().search_books(query)


@mcp.tool()
def list_my_books() -> list[dict]:
    """
    List the books the user is tracking, with list membership (to-read
    watchlist / read rankings), rank, and notes.
    """
    books = client().list_my_books()
    return [
        {
            "book_id": b["book"]["id"],
            "title": b["book"]["title"],
            "authors": b["book"].get("authors"),
            "on_watchlist": b.get("on_watchlist"),
            "on_rankings": b.get("on_rankings"),
            "rank": b.get("rank"),
            "notes": b.get("notes"),
            "completed_at": b.get("completed_at"),
        }
        for b in books
    ]


@mcp.tool()
def book_detail(book_id: str) -> dict:
    """
    Get full detail for a book (description, authors, subjects, publish
    year, pages, rating). `book_id` is the id from `list_my_books`.
    """
    return client().get_book_detail(book_id)


@mcp.tool()
def add_book(isbn: str, title: str, poster_url: Optional[str] = None) -> str:
    """
    Add a book to the user's to-read list. Provide the isbn and title,
    e.g. from `search_books`.
    """
    client().add_book(isbn, title, poster_url)
    return f'Added "{title}" to your to-read list.'


@mcp.tool()
def set_book_note(book_id: str, note: str) -> str:
    """
    Set (or replace) your personal note on a tracked book. `book_id` is the
    id from `list_my_books`.
    """
    client().update_book_tracker(book_id, notes=note)
    return f"Updated notes for book {book_id}."


@mcp.tool()
def search_games(query: str) -> list[dict]:
    """
    Search for video games by title. Returns candidates with their IGDB id,
    title, year, platforms, and cover. Use the IGDB id + title with `add_game`.
    """
    try:
        return client().search_games(query)
    except ApiError as err:
        if err.status == 503:
            return [{"error": "Game search is not configured on the server."}]
        raise


@mcp.tool()
def list_my_games() -> list[dict]:
    """
    List the games the user is tracking, with list membership (backlog
    watchlist / played rankings), rank, 100%-completion flag, and notes.
    """
    games = client().list_my_games()
    return [
        {
            "game_id": g["game"]["id"],
            "title": g["game"]["title"],
            "on_watchlist": g.get("on_watchlist"),
            "on_rankings": g.get("on_rankings"),
            "rank": g.get("rank"),
            "is_100_percent": g.get("is_100_percent"),
            "notes": g.get("notes"),
            "completed_at": g.get("completed_at"),
        }
        for g in games
    ]


@mcp.tool()
def game_detail(game_id: str) -> dict:
    """
    Get full detail for a game (summary, genres, platforms, release year,
    rating, time to beat). `game_id` is the id from `list_my_games`.
    """
    return client().get_game_detail(game_id)


@mcp.tool()
def add_game(igdb_id: int, title: str, poster_url: Optional[str] = None) -> str:
    """
    Add a game to the user's backlog. Provide the IGDB id and title,
    e.g. from `search_games`.
    """
    client().add_game(igdb_id, title, poster_url)
    return f'Added "{title}" to your game backlog.'


@mcp.tool()
def set_game_note(game_id: str, note: str) -> str:
    """
    Set (or replace) your personal note on a tracked game. `game_id` is the
    id from `list_my_games`.
    """
    client().update_game_tracker(game_id, notes=note)
    return f"Updated notes for game {game_id}."


@mcp.tool()
def mark_game_100_percent(game_id: str, is_100_percent: bool = True) -> str:
    """
    Set (or clear) the 100%-completion flag on a tracked game. `game_id` is
    the id from `list_my_games`.
    """
    client().update_game_tracker(game_id, is_100_percent=is_100_percent)
    state = "100% completed" if is_100_percent else "not 100% completed"
    return f"Marked game {game_id} as {state}."


def _format_comparison_domain(d: dict) -> dict | str:
    if not d.get("rankings_visible"):
        return "Visibility limit: Rankings are private. Cannot compare lists."

    summary = {}
    status = d.get("alignment_status")
    if status == "ready":
        summary["alignment"] = (
            f"Score: {d.get('alignment_score')}%. "
            f"Based on {d.get('shared_ranked_count')} shared ranked items."
        )
    elif status == "not_enough_overlap":
        summary["alignment"] = (
            "Not enough overlap to calculate score "
            f"(only {d.get('shared_ranked_count')} shared ranked items)."
        )
    else:
        summary["alignment"] = "Rankings are hidden."

    if d.get("most_aligned"):
        summary["closest_agreements"] = [
            f"{i['title']} (You: {i['your_rank']}, Them: {i['their_rank']}, Gap: {i['gap']})"
            for i in d.get("most_aligned")
        ]
    if d.get("biggest_gaps"):
        summary["biggest_gaps"] = [
            f"{i['title']} (You: {i['your_rank']}, Them: {i['their_rank']}, Gap: {i['gap']})"
            for i in d.get("biggest_gaps")
        ]

    if d.get("watchlist_visible"):
        common = d.get("common_watchlist", [])
        if common:
            summary["common_watchlist"] = [i["title"] for i in common]
        else:
            summary["common_watchlist"] = "No common items on watchlist."
    else:
        summary["common_watchlist"] = "Visibility limit: Their watchlist is private."

    return summary


@mcp.tool()
def compare_users(handle: str, domain: Optional[str] = None) -> dict:
    """
    Compare your lists against another user by handle.
    Optionally restrict to one domain ('movies', 'tv-shows', 'books', 'games').
    Returns common watchlist items, biggest ranking gaps, and closest agreements.
    Only data you are permitted to see based on the other user's visibility settings is returned.
    """
    try:
        data = client().compare_with_user(handle)
    except ApiError as err:
        if err.status == 404:
            return {"error": f"User @{handle} not found or not visible to you."}
        raise

    domains = data.get("domains", [])
    if domain:
        domains = [d for d in domains if d.get("category") == domain]
        if not domains:
            return {"error": f"Domain '{domain}' not found or invalid."}

    result = {
        "target_user": f"{data.get('display_name')} (@{data.get('handle')})",
        "relationship": data.get("relationship"),
        "domains": {},
    }

    for d in domains:
        result["domains"][d.get("category")] = _format_comparison_domain(d)

    return result


# The nine visibility settings an assistant can read or change, keyed by the
# short names used in the tool args and responses (mcp#36). The values are
# the DbUser tier columns the API accepts, so a new domain shows up here by
# hand — mirroring the shelf registry on the API side.
_VISIBILITY_TARGETS = {
    "profile": "visibility_profile",
    "movies": "visibility_movies",
    "tv": "visibility_tv",
    "books": "visibility_books",
    "games": "visibility_games",
    "movies_watchlist": "visibility_watchlist_movies",
    "tv_watchlist": "visibility_watchlist_tv",
    "books_watchlist": "visibility_watchlist_books",
    "games_watchlist": "visibility_watchlist_games",
}

_VISIBILITY_TIERS = ("private", "friends", "public")


def _shape_visibility(data: dict) -> dict:
    """Rename the API's tier field names onto the tool's short targets."""
    shaped = {
        "handle": data.get("handle"),
        "default_privacy": data.get("default_privacy"),
    }
    for target, field in _VISIBILITY_TARGETS.items():
        shaped[target] = data.get(field)
    return shaped


@mcp.tool()
def get_visibility() -> dict:
    """
    Read the user's current list-sharing visibility.

    Returns the claimed profile handle and the current tier of all nine
    visibility settings: the profile, the four shelves (movies, tv, books,
    games), and each shelf's watchlist. Each setting is one of 'private'
    (only you can see it), 'friends' (your accepted friends can see it), or
    'public' (anyone on the internet can see it). A null shelf tier inherits
    'default_privacy'. Do not treat 'public' as a casual setting — it exposes
    the list on your public profile page to anyone, logged in or not.
    """
    return _shape_visibility(client().get_visibility())


def _validate_visibility_input(
    target: Optional[str], tier: Optional[str], handle: Optional[str]
) -> Optional[str]:
    """Return a user-facing error string, or None when the input is valid."""
    if target is None and tier is not None:
        return "target is required when tier is given."
    if target is None and handle is None:
        return "Pass a target (which setting) and tier, or a handle."
    if target is not None and target not in _VISIBILITY_TARGETS:
        return f"Unknown target '{target}'. Target must be one of: " + ", ".join(
            _VISIBILITY_TARGETS
        )
    if target is not None and tier is None:
        return f"tier is required when target='{target}' is given."
    if tier is not None and tier not in _VISIBILITY_TIERS:
        return f"Unknown tier '{tier}'. Tier must be one of: " + ", ".join(
            _VISIBILITY_TIERS
        )
    return None


@mcp.tool()
def set_visibility(
    target: Optional[str] = None,
    tier: Optional[str] = None,
    handle: Optional[str] = None,
) -> dict:
    """
    Change one visibility setting, or claim or clear the profile handle.

    `target` is the setting to change: 'profile', 'movies', 'tv', 'books',
    'games', 'movies_watchlist', 'tv_watchlist', 'books_watchlist', or
    'games_watchlist'. `tier` is its new value: 'private' (only you can see
    it), 'friends' (your accepted friends can see it), or 'public' (anyone
    on the internet can see it). Confirm with the user before setting
    anything to 'public'.

    `handle` is optional: pass it to claim a handle, or '' to clear it. A
    handle is required before any setting leaves 'private'.

    The API rejects any change that breaks the sharing rules (for example a
    'public' shelf under a 'private' profile) and this tool returns the
    API's explanation of why. Returns the resulting visibility settings.
    """
    error = _validate_visibility_input(target, tier, handle)
    if error is not None:
        return {"error": error}

    body = {}
    if target is not None:
        body[_VISIBILITY_TARGETS[target]] = tier
    if handle is not None:
        body["handle"] = handle
    try:
        data = client().update_visibility(**body)
    except ApiError as err:
        if err.status == 422 and err.message.startswith("Pick a handle"):
            return {
                "error": (
                    f"{err.message} Claim one by calling set_visibility again "
                    "with the handle argument, e.g. handle='your-handle'."
                )
            }
        return {"error": err.message}
    return _shape_visibility(data)


def main() -> None:
    """Run the MCP server over stdio."""
    logger.info("Starting Druthers MCP server (stdio)")
    mcp.run()


@mcp.tool()
def set_completed_date(movie_id: str, completed_date: Optional[str] = None) -> str:
    """
    Set the date you finished a tracked movie (YYYY-MM-DD), or omit the date
    to clear it. Defaults to the day it entered Rankings if never set.
    `movie_id` is the id from `list_my_movies`.
    """
    client().update_tracker(movie_id, completed_at=completed_date)
    return f'Set movie {movie_id} completed date to {completed_date or "none"}.'


@mcp.tool()
def set_tv_completed_date(show_id: str, completed_date: Optional[str] = None) -> str:
    """
    Set the date you finished a tracked TV show (YYYY-MM-DD), or omit the
    date to clear it. `show_id` is the id from `list_my_tv_shows`.
    """
    client().update_tv_tracker(show_id, completed_at=completed_date)
    return f'Set show {show_id} completed date to {completed_date or "none"}.'


@mcp.tool()
def set_book_completed_date(book_id: str, completed_date: Optional[str] = None) -> str:
    """
    Set the date you finished a tracked book (YYYY-MM-DD), or omit the date
    to clear it. `book_id` is the id from `list_my_books`.
    """
    client().update_book_tracker(book_id, completed_at=completed_date)
    return f'Set book {book_id} completed date to {completed_date or "none"}.'


@mcp.tool()
def set_game_completed_date(game_id: str, completed_date: Optional[str] = None) -> str:
    """
    Set the date you finished a tracked game (YYYY-MM-DD), or omit the date
    to clear it. `game_id` is the id from `list_my_games`.
    """
    client().update_game_tracker(game_id, completed_at=completed_date)
    return f'Set game {game_id} completed date to {completed_date or "none"}.'


if __name__ == "__main__":
    main()
