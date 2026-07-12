"""
HTTP client for the aleonard.us API.

Thin wrapper over the ``/v1`` endpoints the MCP tools need. Handles token
acquisition (either a pre-issued ``API_TOKEN`` or an email/password exchange)
and transparent re-authentication on a 401.
"""

from typing import Any, Optional

import httpx

from aleonard_mcp.config import Settings, get_settings


class ApiError(Exception):
    """Raised when the API returns an error response."""

    def __init__(self, status: int, message: str):
        super().__init__(f'API {status}: {message}')
        self.status = status
        self.message = message


class ApiClient:  # pylint: disable=too-many-public-methods
    """
    Authenticated client for the aleonard.us API.

    A deliberately flat wrapper — one method per endpoint, grouped by domain
    (movies/tv/books/countries/games), so it grows past pylint's method
    ceiling by design.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        client: Optional[httpx.Client] = None,
    ):
        self._settings = settings or get_settings()
        self._token: Optional[str] = self._settings.api_token
        self._client = client or httpx.Client(
            base_url=self._settings.api_base_url,
            timeout=self._settings.request_timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    # --- auth ---
    def _login(self) -> str:
        """Exchange email/password for a bearer token."""
        s = self._settings
        if not (s.api_email and s.api_password):
            raise ApiError(
                401, 'No API_TOKEN and no API_EMAIL/API_PASSWORD to log in with'
            )
        resp = self._client.post(
            '/v1/auth/token',
            data={'username': s.api_email, 'password': s.api_password},
        )
        if resp.status_code != 200:
            raise ApiError(resp.status_code, 'Login failed')
        self._token = resp.json()['access_token']
        return self._token

    def _auth_header(self) -> dict:
        token = self._token or self._login()
        return {'Authorization': f'Bearer {token}'}

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make an authenticated request, retrying once after a fresh login."""
        resp = self._client.request(method, path, headers=self._auth_header(), **kwargs)
        if resp.status_code == 401:
            self._token = None
            resp = self._client.request(
                method, path, headers=self._auth_header(), **kwargs
            )
        if resp.status_code >= 400:
            detail = _detail(resp)
            raise ApiError(resp.status_code, detail)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # --- movies ---
    def search_movies(self, query: str) -> list[dict]:
        """Search the catalog (OMDB proxy) for movies matching ``query``."""
        return self._request('GET', '/v1/movies/search', params={'q': query})

    def list_my_movies(self) -> list[dict]:
        """Return the authenticated user's tracked movies."""
        return self._request('GET', '/v1/users/me/movies')

    def get_movie_detail(self, movie_id: str) -> dict:
        """Return full detail (plot, director, cast, genre, ...) for a movie."""
        return self._request('GET', f'/v1/movies/{movie_id}')

    def _ensure_catalog_movie(
        self, imdb: str, title: str, poster_url: Optional[str]
    ) -> dict:
        """Create the catalog movie if needed (admin), else find it by imdb."""
        try:
            return self._request(
                'POST',
                '/v1/movies',
                json={'imdb': imdb, 'title': title, 'poster_url': poster_url},
            )
        except ApiError as err:
            if err.status != 400:
                raise
            for movie in self._request('GET', '/v1/movies'):
                if movie['imdb'] == imdb:
                    return movie
            raise

    def add_movie(
        self, imdb: str, title: str, poster_url: Optional[str] = None
    ) -> dict:
        """Add a movie (by imdb id) to the user's list as a watchlist item."""
        movie = self._ensure_catalog_movie(imdb, title, poster_url)
        return self._request(
            'POST',
            f'/v1/users/me/movies/{movie["id"]}',
            json={'completed': 0},
        )

    def update_tracker(self, movie_id: str, **fields) -> dict:
        """Update the user's tracker for a catalog movie id."""
        return self._request('PUT', f'/v1/users/me/movies/{movie_id}', json=fields)

    # --- tv ---
    def search_tv_shows(self, query: str) -> list[dict]:
        """Search the catalog (TVMaze proxy) for TV shows matching ``query``."""
        return self._request('GET', '/v1/tv-shows/search', params={'q': query})

    def list_my_tv_shows(self) -> list[dict]:
        """Return the authenticated user's tracked TV shows."""
        return self._request('GET', '/v1/users/me/tv-shows')

    def get_tv_show_detail(self, show_id: str) -> dict:
        """Return full detail (summary, genres, network, ...) for a show."""
        return self._request('GET', f'/v1/tv-shows/{show_id}')

    def _ensure_catalog_show(
        self,
        tvmaze: int,
        title: str,
        imdb: Optional[str],
        poster_url: Optional[str],
    ) -> dict:
        """Create the catalog show if needed (admin), else find it by tvmaze id."""
        try:
            return self._request(
                'POST',
                '/v1/tv-shows',
                json={
                    'tvmaze': tvmaze,
                    'title': title,
                    'imdb': imdb,
                    'poster_url': poster_url,
                },
            )
        except ApiError as err:
            if err.status != 400:
                raise
            # Create dedups on tvmaze OR imdb, so re-find on either key.
            for show in self._request('GET', '/v1/tv-shows'):
                if show['tvmaze'] == tvmaze or (imdb and show.get('imdb') == imdb):
                    return show
            raise

    def add_tv_show(
        self,
        tvmaze: int,
        title: str,
        imdb: Optional[str] = None,
        poster_url: Optional[str] = None,
    ) -> dict:
        """Add a show (by TVMaze id) to the user's list as a watchlist item."""
        show = self._ensure_catalog_show(tvmaze, title, imdb, poster_url)
        return self._request(
            'POST',
            f'/v1/users/me/tv-shows/{show["id"]}',
            json={'on_watchlist': True},
        )

    def update_tv_tracker(self, show_id: str, **fields) -> dict:
        """Update the user's tracker for a catalog show id."""
        return self._request('PUT', f'/v1/users/me/tv-shows/{show_id}', json=fields)

    def list_show_episodes(self, show_id: str) -> list[dict]:
        """Return the catalog episode list for a show."""
        return self._request('GET', f'/v1/tv-shows/{show_id}/episodes')

    def list_my_episode_marks(self, show_id: str) -> list[dict]:
        """Return the user's watched marks for a show's episodes."""
        return self._request('GET', f'/v1/users/me/tv-shows/{show_id}/episodes')

    def mark_episode(self, episode_id: str) -> dict:
        """Mark an episode watched (idempotent)."""
        return self._request('POST', f'/v1/users/me/episodes/{episode_id}')

    def unmark_episode(self, episode_id: str) -> None:
        """Remove the watched mark from an episode."""
        return self._request('DELETE', f'/v1/users/me/episodes/{episode_id}')

    # --- books ---
    def search_books(self, query: str) -> list[dict]:
        """Search the catalog (Open Library proxy) for books matching ``query``."""
        return self._request('GET', '/v1/books/search', params={'q': query})

    def list_my_books(self) -> list[dict]:
        """Return the authenticated user's tracked books."""
        return self._request('GET', '/v1/users/me/books')

    def get_book_detail(self, book_id: str) -> dict:
        """Return full detail (description, authors, subjects, ...) for a book."""
        return self._request('GET', f'/v1/books/{book_id}')

    def _ensure_catalog_book(
        self, isbn: str, title: str, poster_url: Optional[str]
    ) -> dict:
        """Create the catalog book if needed (admin), else find it by isbn."""
        try:
            return self._request(
                'POST',
                '/v1/books',
                json={'isbn': isbn, 'title': title, 'poster_url': poster_url},
            )
        except ApiError as err:
            if err.status != 400:
                raise
            for book in self._request('GET', '/v1/books'):
                if book['isbn'] == isbn:
                    return book
            raise

    def add_book(self, isbn: str, title: str, poster_url: Optional[str] = None) -> dict:
        """Add a book (by isbn) to the user's list as a to-read item."""
        book = self._ensure_catalog_book(isbn, title, poster_url)
        return self._request(
            'POST',
            f'/v1/users/me/books/{book["id"]}',
            json={'on_watchlist': True},
        )

    def update_book_tracker(self, book_id: str, **fields) -> dict:
        """Update the user's tracker for a catalog book id."""
        return self._request('PUT', f'/v1/users/me/books/{book_id}', json=fields)

    # --- countries ---
    def list_countries(self) -> list[dict]:
        """Return the full country catalog (seeded world list)."""
        return self._request('GET', '/v1/countries')

    def list_my_countries(self) -> list[dict]:
        """Return the authenticated user's tracked countries."""
        return self._request('GET', '/v1/users/me/countries')

    def mark_country(self, country_id: str, **fields) -> dict:
        """Add/merge a country onto the user's lists (bucket list / visited)."""
        return self._request(
            'POST', f'/v1/users/me/countries/{country_id}', json=fields
        )

    def update_country_tracker(self, country_id: str, **fields) -> dict:
        """Update the user's tracker for a catalog country id."""
        return self._request('PUT', f'/v1/users/me/countries/{country_id}', json=fields)

    # --- games ---
    def search_games(self, query: str) -> list[dict]:
        """Search the catalog (IGDB proxy) for games matching ``query``."""
        return self._request('GET', '/v1/games/search', params={'q': query})

    def list_my_games(self) -> list[dict]:
        """Return the authenticated user's tracked games."""
        return self._request('GET', '/v1/users/me/games')

    def get_game_detail(self, game_id: str) -> dict:
        """Return full detail (summary, genres, platforms, ...) for a game."""
        return self._request('GET', f'/v1/games/{game_id}')

    def _ensure_catalog_game(
        self, igdb: int, title: str, poster_url: Optional[str]
    ) -> dict:
        """Create the catalog game if needed (admin), else find it by igdb id."""
        try:
            return self._request(
                'POST',
                '/v1/games',
                json={'igdb': igdb, 'title': title, 'poster_url': poster_url},
            )
        except ApiError as err:
            if err.status != 400:
                raise
            for game in self._request('GET', '/v1/games'):
                if game['igdb'] == igdb:
                    return game
            raise

    def add_game(self, igdb: int, title: str, poster_url: Optional[str] = None) -> dict:
        """Add a game (by IGDB id) to the user's list as a backlog item."""
        game = self._ensure_catalog_game(igdb, title, poster_url)
        return self._request(
            'POST',
            f'/v1/users/me/games/{game["id"]}',
            json={'on_watchlist': True},
        )

    def update_game_tracker(self, game_id: str, **fields) -> dict:
        """Update the user's tracker for a catalog game id."""
        return self._request('PUT', f'/v1/users/me/games/{game_id}', json=fields)


def _detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        return data.get('detail') or data.get('message') or resp.reason_phrase
    except (ValueError, KeyError):
        return resp.reason_phrase
