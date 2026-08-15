# pylint: disable=missing-module-docstring, missing-function-docstring
from datetime import date
import json
from unittest.mock import patch

import httpx
import pytest

from druthers_mcp import server
from druthers_mcp.api_client import ApiClient, ApiError
from druthers_mcp.config import Settings


def make_client(handler) -> ApiClient:
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="http://api", transport=transport)
    settings = Settings(
        api_base_url="http://api", api_token="seed-token", request_timeout=5
    )
    return ApiClient(settings=settings, client=http)


def test_search_movies_passes_query():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/movies/search"
        assert request.url.params["q"] == "matrix"
        assert request.headers["Authorization"] == "Bearer seed-token"
        return httpx.Response(200, json=[{"tmdb": 603, "title": "The Matrix"}])

    client = make_client(handler)
    results = client.search_movies("matrix")
    assert results[0]["tmdb"] == 603


def test_add_movie_creates_catalog_then_marks():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "POST" and request.url.path == "/v1/movies":
            return httpx.Response(201, json={"id": "m-1", "tmdb": 603})
        if request.url.path == "/v1/users/me/movies/m-1":
            assert json.loads(request.read()) == {"on_watchlist": True}
            return httpx.Response(201, json={"id": "t-1", "completed": 0})
        return httpx.Response(404, json={"detail": "nope"})

    client = make_client(handler)
    tracker = client.add_movie(603, "The Matrix")
    assert tracker["id"] == "t-1"
    assert ("POST", "/v1/movies") in calls
    assert ("POST", "/v1/users/me/movies/m-1") in calls


def test_add_movie_reuses_existing_catalog_on_400():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/v1/movies":
            return httpx.Response(400, json={"detail": "Movie already exists"})
        if request.method == "GET" and request.url.path == "/v1/movies":
            return httpx.Response(200, json=[{"id": "m-9", "tmdb": 603}])
        if request.url.path == "/v1/users/me/movies/m-9":
            assert json.loads(request.read()) == {"on_watchlist": True}
            return httpx.Response(201, json={"id": "t-9", "completed": 0})
        return httpx.Response(404, json={"detail": "nope"})

    client = make_client(handler)
    tracker = client.add_movie(603, "The Matrix")
    assert tracker["id"] == "t-9"


def test_add_list_mark_watched_round_trip_preserves_unranked_tracker():
    tracker = None

    class FixedDate:
        """Stable date provider for the completion payload."""

        @classmethod
        def today(cls):
            return date(2025, 1, 15)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal tracker
        path = request.url.path
        if request.method == "POST" and path == "/v1/movies":
            return httpx.Response(
                201, json={"id": "m-1", "tmdb": 603, "title": "The Matrix"}
            )
        if request.method == "POST" and path == "/v1/users/me/movies/m-1":
            body = json.loads(request.read())
            assert body == {"on_watchlist": True}
            tracker = {
                "id": "t-1",
                "movie": {"id": "m-1", "title": "The Matrix"},
                "on_watchlist": body["on_watchlist"],
                "on_rankings": False,
                "rank": None,
                "completed": 0,
                "completed_at": None,
                "notes": None,
            }
            return httpx.Response(201, json=tracker)
        if request.method == "GET" and path == "/v1/users/me/movies":
            return httpx.Response(200, json=[tracker] if tracker else [])
        if request.method == "PUT" and path == "/v1/users/me/movies/m-1":
            body = json.loads(request.read())
            assert body == {
                "on_watchlist": False,
                "completed_at": "2025-01-15",
            }
            assert "on_rankings" not in body
            assert "rank" not in body
            tracker.update(body)
            return httpx.Response(200, json=tracker)
        return httpx.Response(404, json={"detail": "nope"})

    client = make_client(handler)
    with patch.object(server, "client", return_value=client), patch.object(
        server, "date", FixedDate
    ):
        server.add_movie(603, "The Matrix")
        before = server.list_my_movies()
        server.mark_watched("m-1")
        after = server.list_my_movies()

    api_rows = client.list_my_movies()
    assert before["items"][0]["watched"] is False
    assert after["items"][0] == {
        "movie_id": "m-1",
        "title": "The Matrix",
        "watched": True,
        "notes": None,
        "completed_at": "2025-01-15",
        "rank": None,
    }
    assert len(api_rows) == 1
    assert api_rows[0]["on_watchlist"] is False
    assert api_rows[0]["on_rankings"] is False
    assert api_rows[0]["rank"] is None


def test_reauth_on_401():
    state = {"first": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/auth/token":
            return httpx.Response(200, json={"access_token": "fresh-token"})
        if request.url.path == "/v1/users/me/movies":
            if state["first"]:
                state["first"] = False
                return httpx.Response(401, json={"detail": "expired"})
            assert request.headers["Authorization"] == "Bearer fresh-token"
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="http://api", transport=transport)
    settings = Settings(
        api_base_url="http://api",
        api_token="stale-token",
        api_email="a@b.c",
        api_password="pw",
        request_timeout=5,
    )
    client = ApiClient(settings=settings, client=http)
    assert client.list_my_movies() == []


def test_error_raises_apierror():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "boom"})

    client = make_client(handler)
    with pytest.raises(ApiError) as exc:
        client.list_my_movies()
    assert exc.value.status == 500


def test_reauth_on_401_fails_loudly_with_env():
    state = {"first": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/users/me/movies":
            if state["first"]:
                state["first"] = False
                return httpx.Response(401, json={"detail": "expired"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="http://api", transport=transport)
    settings = Settings(
        api_base_url="http://api",
        api_token="stale-token",
        api_email=None,
        api_password=None,
        env="qa",
        request_timeout=5,
    )
    client = ApiClient(settings=settings, client=http)

    with pytest.raises(ApiError) as exc:
        client.list_my_movies()

    assert exc.value.status == 401
    assert "env: qa" in exc.value.message


def test_get_visibility_requests_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/users/me/visibility"
        assert request.headers["Authorization"] == "Bearer seed-token"
        return httpx.Response(200, json={"handle": "adam-prime"})

    client = make_client(handler)
    assert client.get_visibility()["handle"] == "adam-prime"


def test_update_visibility_puts_only_sent_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == "/v1/users/me/visibility"
        assert json.loads(request.read()) == {"visibility_movies": "public"}
        return httpx.Response(200, json={"visibility_movies": "public"})

    client = make_client(handler)
    out = client.update_visibility(visibility_movies="public")
    assert out["visibility_movies"] == "public"


def test_update_visibility_propagates_rejection_detail():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={
                "detail": "Movies is set to public, so your profile must be "
                "at least public - it is currently friends"
            },
        )

    client = make_client(handler)
    with pytest.raises(ApiError) as exc:
        client.update_visibility(visibility_movies="public")
    assert exc.value.status == 422
    assert "it is currently friends" in exc.value.message
