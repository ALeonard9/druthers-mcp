# pylint: disable=missing-module-docstring, missing-function-docstring
from unittest.mock import patch

from aleonard_mcp import server
from aleonard_mcp.api_client import ApiError


@patch("aleonard_mcp.server.client")
def test_list_my_movies_shapes_output(mock_client):
    mock_client.return_value.list_my_movies.return_value = [
        {
            "movie": {"id": "m-1", "title": "The Matrix"},
            "completed": 1,
            "notes": "classic",
            "completed_at": "2024-05-01",
            "rank": 2,
        }
    ]
    out = server.list_my_movies()
    assert out == [
        {
            "movie_id": "m-1",
            "title": "The Matrix",
            "watched": True,
            "notes": "classic",
            "completed_at": "2024-05-01",
            "rank": 2,
        }
    ]


@patch("aleonard_mcp.server.client")
def test_add_movie_returns_confirmation(mock_client):
    mock_client.return_value.add_movie.return_value = {"id": "t-1"}
    msg = server.add_movie(603, "The Matrix")
    assert "The Matrix" in msg
    mock_client.return_value.add_movie.assert_called_once_with(603, "The Matrix", None)


@patch("aleonard_mcp.server.client")
def test_movie_detail_passthrough(mock_client):
    mock_client.return_value.get_movie_detail.return_value = {
        "title": "The Matrix",
        "director": "The Wachowskis",
    }
    out = server.movie_detail("m-1")
    assert out["director"] == "The Wachowskis"
    mock_client.return_value.get_movie_detail.assert_called_once_with("m-1")


@patch("aleonard_mcp.server.client")
def test_mark_watched_updates_tracker(mock_client):
    server.mark_watched("m-1", watched=True)
    mock_client.return_value.update_tracker.assert_called_once_with("m-1", completed=1)


@patch("aleonard_mcp.server.client")
def test_set_note_updates_tracker(mock_client):
    server.set_note("m-1", "great film")
    mock_client.return_value.update_tracker.assert_called_once_with(
        "m-1", notes="great film"
    )


@patch("aleonard_mcp.server.client")
def test_search_movies_handles_unconfigured(mock_client):
    mock_client.return_value.search_movies.side_effect = ApiError(503, "nope")
    out = server.search_movies("matrix")
    assert out[0]["error"]


@patch("aleonard_mcp.server.client")
def test_list_my_tv_shows_shapes_output(mock_client):
    mock_client.return_value.list_my_tv_shows.return_value = [
        {
            "tv_show": {"id": "s-1", "title": "Severance", "status": "Running"},
            "on_watchlist": True,
            "on_rankings": False,
            "rank": None,
            "notes": "innie things",
            "completed_at": "2024-05-01",
        }
    ]
    out = server.list_my_tv_shows()
    assert out == [
        {
            "show_id": "s-1",
            "title": "Severance",
            "status": "Running",
            "on_watchlist": True,
            "on_rankings": False,
            "rank": None,
            "notes": "innie things",
            "completed_at": "2024-05-01",
        }
    ]


@patch("aleonard_mcp.server.client")
def test_add_tv_show_returns_confirmation(mock_client):
    mock_client.return_value.add_tv_show.return_value = {"id": "t-1"}
    msg = server.add_tv_show(44932, "Severance")
    assert "Severance" in msg
    mock_client.return_value.add_tv_show.assert_called_once_with(
        44932, "Severance", None, None
    )


@patch("aleonard_mcp.server.client")
def test_show_episodes_merges_watched_marks(mock_client):
    mock_client.return_value.list_show_episodes.return_value = [
        {
            "id": "e-1",
            "season": 1,
            "season_number": 1,
            "title": "Good News About Hell",
            "airdate": "2022-02-18T00:00:00",
        },
        {
            "id": "e-2",
            "season": 2,
            "season_number": 1,
            "title": "Hello, Ms. Cobel",
            "airdate": "2025-01-17T00:00:00",
        },
    ]
    mock_client.return_value.list_my_episode_marks.return_value = [
        {"episode": {"id": "e-1"}, "watched": 1}
    ]
    out = server.show_episodes("s-1")
    assert out[0]["watched"] is True
    assert out[1]["watched"] is False

    season_two = server.show_episodes("s-1", season=2)
    assert [e["episode_id"] for e in season_two] == ["e-2"]


@patch("aleonard_mcp.server.client")
def test_mark_episode_watched_and_unwatched(mock_client):
    server.mark_episode_watched("e-1")
    mock_client.return_value.mark_episode.assert_called_once_with("e-1")
    server.mark_episode_watched("e-1", watched=False)
    mock_client.return_value.unmark_episode.assert_called_once_with("e-1")


@patch("aleonard_mcp.server.client")
def test_set_tv_note_updates_tracker(mock_client):
    server.set_tv_note("s-1", "rewatch with kids")
    mock_client.return_value.update_tv_tracker.assert_called_once_with(
        "s-1", notes="rewatch with kids"
    )


@patch("aleonard_mcp.server.client")
def test_list_my_books_shapes_output(mock_client):
    mock_client.return_value.list_my_books.return_value = [
        {
            "book": {"id": "b-1", "title": "Dune", "authors": "Frank Herbert"},
            "on_watchlist": False,
            "on_rankings": True,
            "rank": 7,
            "notes": "spice",
            "completed_at": "2024-05-01",
        }
    ]
    out = server.list_my_books()
    assert out == [
        {
            "book_id": "b-1",
            "title": "Dune",
            "authors": "Frank Herbert",
            "on_watchlist": False,
            "on_rankings": True,
            "rank": 7,
            "notes": "spice",
            "completed_at": "2024-05-01",
        }
    ]


@patch("aleonard_mcp.server.client")
def test_add_book_returns_confirmation(mock_client):
    mock_client.return_value.add_book.return_value = {"id": "t-1"}
    msg = server.add_book("9780441172719", "Dune")
    assert "Dune" in msg
    mock_client.return_value.add_book.assert_called_once_with(
        "9780441172719", "Dune", None
    )


@patch("aleonard_mcp.server.client")
def test_list_my_games_shapes_output(mock_client):
    mock_client.return_value.list_my_games.return_value = [
        {
            "game": {"id": "g-1", "title": "Breath of the Wild"},
            "on_watchlist": False,
            "on_rankings": True,
            "rank": 4,
            "is_100_percent": True,
            "notes": "korok hell",
            "completed_at": "2024-05-01",
        }
    ]
    out = server.list_my_games()
    assert out == [
        {
            "game_id": "g-1",
            "title": "Breath of the Wild",
            "on_watchlist": False,
            "on_rankings": True,
            "rank": 4,
            "is_100_percent": True,
            "notes": "korok hell",
            "completed_at": "2024-05-01",
        }
    ]


@patch("aleonard_mcp.server.client")
def test_add_game_returns_confirmation(mock_client):
    mock_client.return_value.add_game.return_value = {"id": "t-1"}
    msg = server.add_game(1234, "Breath of the Wild")
    assert "Breath of the Wild" in msg
    mock_client.return_value.add_game.assert_called_once_with(
        1234, "Breath of the Wild", None
    )


@patch("aleonard_mcp.server.client")
def test_search_games_handles_unconfigured(mock_client):
    mock_client.return_value.search_games.side_effect = ApiError(503, "nope")
    out = server.search_games("zelda")
    assert out[0]["error"]


@patch("aleonard_mcp.server.client")
def test_mark_game_100_percent(mock_client):
    server.mark_game_100_percent("g-1")
    mock_client.return_value.update_game_tracker.assert_called_once_with(
        "g-1", is_100_percent=True
    )
    server.mark_game_100_percent("g-1", is_100_percent=False)
    mock_client.return_value.update_game_tracker.assert_called_with(
        "g-1", is_100_percent=False
    )


# Tests for completed-date MCP tools (mcp#39)
@patch("aleonard_mcp.server.client")
def test_set_completed_date(mock_client):
    msg = server.set_completed_date("m-1", "2025-01-15")
    mock_client.return_value.update_tracker.assert_called_once_with(
        "m-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


@patch("aleonard_mcp.server.client")
def test_set_tv_completed_date(mock_client):
    msg = server.set_tv_completed_date("s-1", "2025-01-15")
    mock_client.return_value.update_tv_tracker.assert_called_once_with(
        "s-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


@patch("aleonard_mcp.server.client")
def test_set_book_completed_date(mock_client):
    msg = server.set_book_completed_date("b-1", "2025-01-15")
    mock_client.return_value.update_book_tracker.assert_called_once_with(
        "b-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


@patch("aleonard_mcp.server.client")
def test_set_game_completed_date(mock_client):
    msg = server.set_game_completed_date("g-1", "2025-01-15")
    mock_client.return_value.update_game_tracker.assert_called_once_with(
        "g-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


# Tests for remaining MCP tools test gaps (mcp#40)
@patch("aleonard_mcp.server.client")
def test_search_tv_shows(mock_client):
    mock_client.return_value.search_tv_shows.return_value = [{"title": "Severance"}]
    out = server.search_tv_shows("severance")
    assert out == [{"title": "Severance"}]
    mock_client.return_value.search_tv_shows.assert_called_once_with("severance")


@patch("aleonard_mcp.server.client")
def test_search_books(mock_client):
    mock_client.return_value.search_books.return_value = [{"title": "Dune"}]
    out = server.search_books("dune")
    assert out == [{"title": "Dune"}]
    mock_client.return_value.search_books.assert_called_once_with("dune")


@patch("aleonard_mcp.server.client")
def test_tv_show_detail(mock_client):
    mock_client.return_value.get_tv_show_detail.return_value = {"title": "Severance"}
    out = server.tv_show_detail("s-1")
    assert out["title"] == "Severance"
    mock_client.return_value.get_tv_show_detail.assert_called_once_with("s-1")


@patch("aleonard_mcp.server.client")
def test_book_detail(mock_client):
    mock_client.return_value.get_book_detail.return_value = {"title": "Dune"}
    out = server.book_detail("b-1")
    assert out["title"] == "Dune"
    mock_client.return_value.get_book_detail.assert_called_once_with("b-1")


@patch("aleonard_mcp.server.client")
def test_game_detail(mock_client):
    mock_client.return_value.get_game_detail.return_value = {"title": "Zelda"}
    out = server.game_detail("g-1")
    assert out["title"] == "Zelda"
    mock_client.return_value.get_game_detail.assert_called_once_with("g-1")


@patch("aleonard_mcp.server.client")
def test_set_book_note(mock_client):
    server.set_book_note("b-1", "favorite sci-fi")
    mock_client.return_value.update_book_tracker.assert_called_once_with(
        "b-1", notes="favorite sci-fi"
    )


@patch("aleonard_mcp.server.client")
def test_set_game_note(mock_client):
    server.set_game_note("g-1", "played on switch")
    mock_client.return_value.update_game_tracker.assert_called_once_with(
        "g-1", notes="played on switch"
    )
