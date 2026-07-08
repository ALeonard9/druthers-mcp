# pylint: disable=missing-module-docstring, missing-function-docstring
from unittest.mock import patch

from aleonard_mcp import server
from aleonard_mcp.api_client import ApiError


@patch('aleonard_mcp.server.client')
def test_list_my_movies_shapes_output(mock_client):
    mock_client.return_value.list_my_movies.return_value = [
        {
            'movie': {'id': 'm-1', 'title': 'The Matrix'},
            'completed': 1,
            'notes': 'classic',
            'rank': 2,
        }
    ]
    out = server.list_my_movies()
    assert out == [
        {
            'movie_id': 'm-1',
            'title': 'The Matrix',
            'watched': True,
            'notes': 'classic',
            'rank': 2,
        }
    ]


@patch('aleonard_mcp.server.client')
def test_add_movie_returns_confirmation(mock_client):
    mock_client.return_value.add_movie.return_value = {'id': 't-1'}
    msg = server.add_movie('tt1', 'The Matrix')
    assert 'The Matrix' in msg
    mock_client.return_value.add_movie.assert_called_once_with(
        'tt1', 'The Matrix', None
    )


@patch('aleonard_mcp.server.client')
def test_movie_detail_passthrough(mock_client):
    mock_client.return_value.get_movie_detail.return_value = {
        'title': 'The Matrix',
        'director': 'The Wachowskis',
    }
    out = server.movie_detail('m-1')
    assert out['director'] == 'The Wachowskis'
    mock_client.return_value.get_movie_detail.assert_called_once_with('m-1')


@patch('aleonard_mcp.server.client')
def test_mark_watched_updates_tracker(mock_client):
    server.mark_watched('m-1', watched=True)
    mock_client.return_value.update_tracker.assert_called_once_with('m-1', completed=1)


@patch('aleonard_mcp.server.client')
def test_set_note_updates_tracker(mock_client):
    server.set_note('m-1', 'great film')
    mock_client.return_value.update_tracker.assert_called_once_with(
        'm-1', notes='great film'
    )


@patch('aleonard_mcp.server.client')
def test_search_movies_handles_unconfigured(mock_client):
    mock_client.return_value.search_movies.side_effect = ApiError(503, 'nope')
    out = server.search_movies('matrix')
    assert out[0]['error']
