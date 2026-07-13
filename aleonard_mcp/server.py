"""
aleonard.us MCP server.

Exposes the personal Movies and TV trackers as MCP tools backed by the
aleonard.us API, so an LLM (e.g. Claude) can search, list, add, and annotate
movies and TV shows (including episode watch marks) on the user's behalf.
Runs over stdio.
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
def movie_detail(movie_id: str) -> dict:
    """
    Get full detail for a movie (plot, director, cast, genre, year, runtime,
    rating). `movie_id` is the id from `list_my_movies`.
    """
    return client().get_movie_detail(movie_id)


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
            'show_id': s['tv_show']['id'],
            'title': s['tv_show']['title'],
            'status': s['tv_show'].get('status'),
            'on_watchlist': s.get('on_watchlist'),
            'on_rankings': s.get('on_rankings'),
            'rank': s.get('rank'),
            'notes': s.get('notes'),
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
    return f'Updated notes for TV show {show_id}.'


@mcp.tool()
def show_episodes(show_id: str, season: Optional[int] = None) -> list[dict]:
    """
    List a tracked show's episodes (optionally one season) with the user's
    watched flag on each. `show_id` is the id from `list_my_tv_shows`.
    """
    episodes = client().list_show_episodes(show_id)
    watched_ids = {
        m['episode']['id']
        for m in client().list_my_episode_marks(show_id)
        if m.get('watched')
    }
    return [
        {
            'episode_id': e['id'],
            'season': e.get('season'),
            'episode': e.get('season_number'),
            'title': e['title'],
            'airdate': e.get('airdate'),
            'watched': e['id'] in watched_ids,
        }
        for e in episodes
        if season is None or e.get('season') == season
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


def main() -> None:
    """Run the MCP server over stdio."""
    logger.info('Starting aleonard.us MCP server (stdio)')
    mcp.run()


if __name__ == '__main__':
    main()
