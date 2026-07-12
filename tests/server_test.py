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


@patch('aleonard_mcp.server.client')
def test_list_my_tv_shows_shapes_output(mock_client):
    mock_client.return_value.list_my_tv_shows.return_value = [
        {
            'tv_show': {'id': 's-1', 'title': 'Severance', 'status': 'Running'},
            'on_watchlist': True,
            'on_rankings': False,
            'rank': None,
            'notes': 'innie things',
        }
    ]
    out = server.list_my_tv_shows()
    assert out == [
        {
            'show_id': 's-1',
            'title': 'Severance',
            'status': 'Running',
            'on_watchlist': True,
            'on_rankings': False,
            'rank': None,
            'notes': 'innie things',
        }
    ]


@patch('aleonard_mcp.server.client')
def test_add_tv_show_returns_confirmation(mock_client):
    mock_client.return_value.add_tv_show.return_value = {'id': 't-1'}
    msg = server.add_tv_show(44932, 'Severance')
    assert 'Severance' in msg
    mock_client.return_value.add_tv_show.assert_called_once_with(
        44932, 'Severance', None, None
    )


@patch('aleonard_mcp.server.client')
def test_show_episodes_merges_watched_marks(mock_client):
    mock_client.return_value.list_show_episodes.return_value = [
        {
            'id': 'e-1',
            'season': 1,
            'season_number': 1,
            'title': 'Good News About Hell',
            'airdate': '2022-02-18T00:00:00',
        },
        {
            'id': 'e-2',
            'season': 2,
            'season_number': 1,
            'title': 'Hello, Ms. Cobel',
            'airdate': '2025-01-17T00:00:00',
        },
    ]
    mock_client.return_value.list_my_episode_marks.return_value = [
        {'episode': {'id': 'e-1'}, 'watched': 1}
    ]
    out = server.show_episodes('s-1')
    assert out[0]['watched'] is True
    assert out[1]['watched'] is False

    season_two = server.show_episodes('s-1', season=2)
    assert [e['episode_id'] for e in season_two] == ['e-2']


@patch('aleonard_mcp.server.client')
def test_mark_episode_watched_and_unwatched(mock_client):
    server.mark_episode_watched('e-1')
    mock_client.return_value.mark_episode.assert_called_once_with('e-1')
    server.mark_episode_watched('e-1', watched=False)
    mock_client.return_value.unmark_episode.assert_called_once_with('e-1')


@patch('aleonard_mcp.server.client')
def test_set_tv_note_updates_tracker(mock_client):
    server.set_tv_note('s-1', 'rewatch with kids')
    mock_client.return_value.update_tv_tracker.assert_called_once_with(
        's-1', notes='rewatch with kids'
    )


@patch('aleonard_mcp.server.client')
def test_list_my_books_shapes_output(mock_client):
    mock_client.return_value.list_my_books.return_value = [
        {
            'book': {'id': 'b-1', 'title': 'Dune', 'authors': 'Frank Herbert'},
            'on_watchlist': False,
            'on_rankings': True,
            'rank': 7,
            'notes': 'spice',
        }
    ]
    out = server.list_my_books()
    assert out == [
        {
            'book_id': 'b-1',
            'title': 'Dune',
            'authors': 'Frank Herbert',
            'on_watchlist': False,
            'on_rankings': True,
            'rank': 7,
            'notes': 'spice',
        }
    ]


@patch('aleonard_mcp.server.client')
def test_add_book_returns_confirmation(mock_client):
    mock_client.return_value.add_book.return_value = {'id': 't-1'}
    msg = server.add_book('9780441172719', 'Dune')
    assert 'Dune' in msg
    mock_client.return_value.add_book.assert_called_once_with(
        '9780441172719', 'Dune', None
    )


@patch('aleonard_mcp.server.client')
def test_mark_country_by_code(mock_client):
    mock_client.return_value.list_countries.return_value = [
        {'id': 'c-1', 'title': 'Japan', 'country_code': 'jp'},
        {'id': 'c-2', 'title': 'Iceland', 'country_code': 'is'},
    ]
    msg = server.mark_country('JP', visited=True, first_visited='2019-04-02')
    assert 'Japan' in msg and 'visited' in msg
    mock_client.return_value.mark_country.assert_called_once_with(
        'c-1',
        on_rankings=True,
        on_watchlist=False,
        first_visited='2019-04-02T00:00:00',
    )


@patch('aleonard_mcp.server.client')
def test_mark_country_unknown_code(mock_client):
    mock_client.return_value.list_countries.return_value = []
    msg = server.mark_country('zz', bucket_list=True)
    assert 'No country' in msg
    mock_client.return_value.mark_country.assert_not_called()


@patch('aleonard_mcp.server.client')
def test_list_my_countries_shapes_output(mock_client):
    mock_client.return_value.list_my_countries.return_value = [
        {
            'country': {'id': 'c-1', 'title': 'Japan', 'flag_emoji': '🇯🇵'},
            'on_rankings': True,
            'on_watchlist': False,
            'rank': 3,
            'first_visited': '2019-04-02T00:00:00',
            'notes': None,
        }
    ]
    out = server.list_my_countries()
    assert out[0]['title'] == 'Japan'
    assert out[0]['visited'] is True
    assert out[0]['on_bucket_list'] is False
    assert out[0]['flag'] == '🇯🇵'
    assert out[0]['rank'] == 3
