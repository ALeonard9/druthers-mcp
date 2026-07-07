# pylint: disable=missing-module-docstring, missing-function-docstring
import httpx
import pytest

from aleonard_mcp.api_client import ApiClient, ApiError
from aleonard_mcp.config import Settings


def make_client(handler) -> ApiClient:
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url='http://api', transport=transport)
    settings = Settings(
        api_base_url='http://api', api_token='seed-token', request_timeout=5
    )
    return ApiClient(settings=settings, client=http)


def test_search_movies_passes_query():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == '/v1/movies/search'
        assert request.url.params['q'] == 'matrix'
        assert request.headers['Authorization'] == 'Bearer seed-token'
        return httpx.Response(200, json=[{'imdb': 'tt1', 'title': 'The Matrix'}])

    client = make_client(handler)
    results = client.search_movies('matrix')
    assert results[0]['imdb'] == 'tt1'


def test_add_movie_creates_catalog_then_marks():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == 'POST' and request.url.path == '/v1/movies':
            return httpx.Response(201, json={'id': 'm-1', 'imdb': 'tt1'})
        if request.url.path == '/v1/users/me/movies/m-1':
            return httpx.Response(201, json={'id': 't-1', 'completed': 0})
        return httpx.Response(404, json={'detail': 'nope'})

    client = make_client(handler)
    tracker = client.add_movie('tt1', 'The Matrix')
    assert tracker['id'] == 't-1'
    assert ('POST', '/v1/movies') in calls
    assert ('POST', '/v1/users/me/movies/m-1') in calls


def test_add_movie_reuses_existing_catalog_on_400():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'POST' and request.url.path == '/v1/movies':
            return httpx.Response(400, json={'detail': 'Movie imdb already exists'})
        if request.method == 'GET' and request.url.path == '/v1/movies':
            return httpx.Response(200, json=[{'id': 'm-9', 'imdb': 'tt1'}])
        if request.url.path == '/v1/users/me/movies/m-9':
            return httpx.Response(201, json={'id': 't-9', 'completed': 0})
        return httpx.Response(404, json={'detail': 'nope'})

    client = make_client(handler)
    tracker = client.add_movie('tt1', 'The Matrix')
    assert tracker['id'] == 't-9'


def test_reauth_on_401():
    state = {'first': True}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == '/v1/auth/token':
            return httpx.Response(200, json={'access_token': 'fresh-token'})
        if request.url.path == '/v1/users/me/movies':
            if state['first']:
                state['first'] = False
                return httpx.Response(401, json={'detail': 'expired'})
            assert request.headers['Authorization'] == 'Bearer fresh-token'
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url='http://api', transport=transport)
    settings = Settings(
        api_base_url='http://api',
        api_token='stale-token',
        api_email='a@b.c',
        api_password='pw',
        request_timeout=5,
    )
    client = ApiClient(settings=settings, client=http)
    assert client.list_my_movies() == []


def test_error_raises_apierror():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={'detail': 'boom'})

    client = make_client(handler)
    with pytest.raises(ApiError) as exc:
        client.list_my_movies()
    assert exc.value.status == 500
