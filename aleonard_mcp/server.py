"""
aleonard.us MCP server.

Exposes the personal Movies tracker as MCP tools backed by the aleonard.us API,
so an LLM (e.g. Claude) can search, list, add, and annotate movies on the user's
behalf. Runs over stdio.
"""

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error

from aleonard_mcp.api_client import ApiClient, ApiError
from aleonard_mcp.config import get_settings

logging.basicConfig(level=get_settings().log_level.upper())
logger = logging.getLogger('aleonard_mcp')

mcp = FastMCP('aleonard-us')

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
    Search for movies by title. Returns catalog candidates with their imdb id,
    title, year and poster. Use the imdb id + title with `add_movie`.
    """
    try:
        return client().search_movies(query)
    except ApiError as err:
        if err.status == 503:
            return [{'error': 'Movie search is not configured on the server.'}]
        raise


@mcp.tool()
def list_my_movies() -> list[dict]:
    """
    List the movies the user is tracking, with watched status and notes.
    """
    movies = client().list_my_movies()
    return [
        {
            'movie_id': m['movie']['id'],
            'title': m['movie']['title'],
            'watched': m.get('completed') == 1,
            'notes': m.get('notes'),
            'rank': m.get('rank'),
        }
        for m in movies
    ]


@mcp.tool()
def add_movie(imdb_id: str, title: str, poster_url: Optional[str] = None) -> str:
    """
    Add a movie to the user's list (as a watchlist item). Provide the imdb id
    and title, e.g. from `search_movies`.
    """
    client().add_movie(imdb_id, title, poster_url)
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
    return f'Updated notes for movie {movie_id}.'


def main() -> None:
    """Run the MCP server over stdio."""
    logger.info('Starting aleonard.us MCP server (stdio)')
    mcp.run()


if __name__ == '__main__':
    main()
