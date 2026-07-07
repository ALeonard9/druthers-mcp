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


class ApiClient:
    """Authenticated client for the aleonard.us API."""

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


def _detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        return data.get('detail') or data.get('message') or resp.reason_phrase
    except (ValueError, KeyError):
        return resp.reason_phrase
