# pylint: disable=missing-module-docstring, missing-function-docstring, protected-access
from unittest.mock import patch

from druthers_mcp import server
from druthers_mcp.api_client import ApiError


@patch("druthers_mcp.server.client")
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


@patch("druthers_mcp.server.client")
def test_add_movie_returns_confirmation(mock_client):
    mock_client.return_value.add_movie.return_value = {"id": "t-1"}
    msg = server.add_movie(603, "The Matrix")
    assert "The Matrix" in msg
    mock_client.return_value.add_movie.assert_called_once_with(603, "The Matrix", None)


@patch("druthers_mcp.server.client")
def test_movie_detail_passthrough(mock_client):
    mock_client.return_value.get_movie_detail.return_value = {
        "title": "The Matrix",
        "director": "The Wachowskis",
    }
    out = server.movie_detail("m-1")
    assert out["director"] == "The Wachowskis"
    mock_client.return_value.get_movie_detail.assert_called_once_with("m-1")


@patch("druthers_mcp.server.client")
def test_mark_watched_updates_tracker(mock_client):
    server.mark_watched("m-1", watched=True)
    mock_client.return_value.update_tracker.assert_called_once_with("m-1", completed=1)


@patch("druthers_mcp.server.client")
def test_set_note_updates_tracker(mock_client):
    server.set_note("m-1", "great film")
    mock_client.return_value.update_tracker.assert_called_once_with(
        "m-1", notes="great film"
    )


@patch("druthers_mcp.server.client")
def test_search_movies_handles_unconfigured(mock_client):
    mock_client.return_value.search_movies.side_effect = ApiError(503, "nope")
    out = server.search_movies("matrix")
    assert out[0]["error"]


@patch("druthers_mcp.server.client")
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


@patch("druthers_mcp.server.client")
def test_add_tv_show_returns_confirmation(mock_client):
    mock_client.return_value.add_tv_show.return_value = {"id": "t-1"}
    msg = server.add_tv_show(44932, "Severance")
    assert "Severance" in msg
    mock_client.return_value.add_tv_show.assert_called_once_with(
        44932, "Severance", None, None
    )


@patch("druthers_mcp.server.client")
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


@patch("druthers_mcp.server.client")
def test_mark_episode_watched_and_unwatched(mock_client):
    server.mark_episode_watched("e-1")
    mock_client.return_value.mark_episode.assert_called_once_with("e-1")
    server.mark_episode_watched("e-1", watched=False)
    mock_client.return_value.unmark_episode.assert_called_once_with("e-1")


@patch("druthers_mcp.server.client")
def test_set_tv_note_updates_tracker(mock_client):
    server.set_tv_note("s-1", "rewatch with kids")
    mock_client.return_value.update_tv_tracker.assert_called_once_with(
        "s-1", notes="rewatch with kids"
    )


@patch("druthers_mcp.server.client")
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


@patch("druthers_mcp.server.client")
def test_add_book_returns_confirmation(mock_client):
    mock_client.return_value.add_book.return_value = {"id": "t-1"}
    msg = server.add_book("9780441172719", "Dune")
    assert "Dune" in msg
    mock_client.return_value.add_book.assert_called_once_with(
        "9780441172719", "Dune", None
    )


@patch("druthers_mcp.server.client")
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


@patch("druthers_mcp.server.client")
def test_add_game_returns_confirmation(mock_client):
    mock_client.return_value.add_game.return_value = {"id": "t-1"}
    msg = server.add_game(1234, "Breath of the Wild")
    assert "Breath of the Wild" in msg
    mock_client.return_value.add_game.assert_called_once_with(
        1234, "Breath of the Wild", None
    )


@patch("druthers_mcp.server.client")
def test_search_games_handles_unconfigured(mock_client):
    mock_client.return_value.search_games.side_effect = ApiError(503, "nope")
    out = server.search_games("zelda")
    assert out[0]["error"]


@patch("druthers_mcp.server.client")
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
@patch("druthers_mcp.server.client")
def test_set_completed_date(mock_client):
    msg = server.set_completed_date("m-1", "2025-01-15")
    mock_client.return_value.update_tracker.assert_called_once_with(
        "m-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


@patch("druthers_mcp.server.client")
def test_set_tv_completed_date(mock_client):
    msg = server.set_tv_completed_date("s-1", "2025-01-15")
    mock_client.return_value.update_tv_tracker.assert_called_once_with(
        "s-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


@patch("druthers_mcp.server.client")
def test_set_book_completed_date(mock_client):
    msg = server.set_book_completed_date("b-1", "2025-01-15")
    mock_client.return_value.update_book_tracker.assert_called_once_with(
        "b-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


@patch("druthers_mcp.server.client")
def test_set_game_completed_date(mock_client):
    msg = server.set_game_completed_date("g-1", "2025-01-15")
    mock_client.return_value.update_game_tracker.assert_called_once_with(
        "g-1", completed_at="2025-01-15"
    )
    assert "2025-01-15" in msg


# Tests for remaining MCP tools test gaps (mcp#40)
@patch("druthers_mcp.server.client")
def test_search_tv_shows(mock_client):
    mock_client.return_value.search_tv_shows.return_value = [{"title": "Severance"}]
    out = server.search_tv_shows("severance")
    assert out == [{"title": "Severance"}]
    mock_client.return_value.search_tv_shows.assert_called_once_with("severance")


@patch("druthers_mcp.server.client")
def test_search_books(mock_client):
    mock_client.return_value.search_books.return_value = [{"title": "Dune"}]
    out = server.search_books("dune")
    assert out == [{"title": "Dune"}]
    mock_client.return_value.search_books.assert_called_once_with("dune")


@patch("druthers_mcp.server.client")
def test_tv_show_detail(mock_client):
    mock_client.return_value.get_tv_show_detail.return_value = {"title": "Severance"}
    out = server.tv_show_detail("s-1")
    assert out["title"] == "Severance"
    mock_client.return_value.get_tv_show_detail.assert_called_once_with("s-1")


@patch("druthers_mcp.server.client")
def test_book_detail(mock_client):
    mock_client.return_value.get_book_detail.return_value = {"title": "Dune"}
    out = server.book_detail("b-1")
    assert out["title"] == "Dune"
    mock_client.return_value.get_book_detail.assert_called_once_with("b-1")


@patch("druthers_mcp.server.client")
def test_game_detail(mock_client):
    mock_client.return_value.get_game_detail.return_value = {"title": "Zelda"}
    out = server.game_detail("g-1")
    assert out["title"] == "Zelda"
    mock_client.return_value.get_game_detail.assert_called_once_with("g-1")


@patch("druthers_mcp.server.client")
def test_set_book_note(mock_client):
    server.set_book_note("b-1", "favorite sci-fi")
    mock_client.return_value.update_book_tracker.assert_called_once_with(
        "b-1", notes="favorite sci-fi"
    )


@patch("druthers_mcp.server.client")
def test_set_game_note(mock_client):
    server.set_game_note("g-1", "played on switch")
    mock_client.return_value.update_game_tracker.assert_called_once_with(
        "g-1", notes="played on switch"
    )


# Tests for compare_users
@patch("druthers_mcp.server.client")
def test_compare_users_full_visibility(mock_client):
    mock_client.return_value.compare_with_user.return_value = {
        "handle": "bob",
        "display_name": "Bob",
        "relationship": "friend",
        "domains": [
            {
                "category": "movies",
                "rankings_visible": True,
                "watchlist_visible": True,
                "alignment_status": "ready",
                "alignment_score": 85,
                "shared_ranked_count": 10,
                "most_aligned": [
                    {"title": "Inception", "your_rank": 1, "their_rank": 2, "gap": 1}
                ],
                "biggest_gaps": [
                    {"title": "Matrix", "your_rank": 1, "their_rank": 10, "gap": 9}
                ],
                "common_watchlist": [{"title": "Dune"}],
            }
        ],
    }

    out = server.compare_users("bob")
    assert out["target_user"] == "Bob (@bob)"

    movies = out["domains"]["movies"]
    assert "85%" in movies["alignment"]
    assert len(movies["closest_agreements"]) == 1
    assert "Inception" in movies["closest_agreements"][0]
    assert len(movies["biggest_gaps"]) == 1
    assert "Matrix" in movies["biggest_gaps"][0]
    assert movies["common_watchlist"] == ["Dune"]


@patch("druthers_mcp.server.client")
def test_compare_users_visibility_limits(mock_client):
    mock_client.return_value.compare_with_user.return_value = {
        "handle": "secret_bob",
        "display_name": "Bob",
        "relationship": "stranger",
        "domains": [
            {
                "category": "movies",
                "rankings_visible": False,
                "watchlist_visible": False,
            },
            {
                "category": "tv-shows",
                "rankings_visible": True,
                "watchlist_visible": False,
                "alignment_status": "not_enough_overlap",
                "shared_ranked_count": 2,
                "most_aligned": [],
                "biggest_gaps": [],
                "common_watchlist": [],
            },
        ],
    }

    out = server.compare_users("secret_bob")

    movies = out["domains"]["movies"]
    assert "Visibility limit: Rankings are private" in movies

    tv = out["domains"]["tv-shows"]
    assert "Not enough overlap" in tv["alignment"]
    assert "watchlist is private" in tv["common_watchlist"]


@patch("druthers_mcp.server.client")
def test_compare_users_domain_filter(mock_client):
    mock_client.return_value.compare_with_user.return_value = {
        "handle": "bob",
        "display_name": "Bob",
        "relationship": "friend",
        "domains": [
            {"category": "movies", "rankings_visible": False},
            {"category": "books", "rankings_visible": False},
        ],
    }

    out = server.compare_users("bob", domain="books")
    assert "movies" not in out["domains"]
    assert "books" in out["domains"]


@patch("druthers_mcp.server.client")
def test_compare_users_not_found(mock_client):
    mock_client.return_value.compare_with_user.side_effect = ApiError(404, "Not found")
    out = server.compare_users("nobody")
    assert "error" in out
    assert "nobody" in out["error"]


# Tests for visibility tools (mcp#36)
NINE_VISIBILITY_TARGETS = [
    "profile",
    "movies",
    "tv",
    "books",
    "games",
    "movies_watchlist",
    "tv_watchlist",
    "books_watchlist",
    "games_watchlist",
]


@patch("druthers_mcp.server.client")
def test_get_visibility_reports_all_nine_tiers_and_handle(mock_client):
    api = {
        "handle": "adam-prime",
        "default_privacy": "friends",
        "visibility_profile": "public",
        "visibility_movies": "private",
        "visibility_tv": "friends",
        "visibility_books": "public",
        "visibility_games": "private",
        "visibility_watchlist_movies": "friends",
        "visibility_watchlist_tv": "public",
        "visibility_watchlist_books": "private",
        "visibility_watchlist_games": "friends",
    }
    mock_client.return_value.get_visibility.return_value = api

    out = server.get_visibility()

    assert out["handle"] == "adam-prime"
    assert out["default_privacy"] == "friends"
    assert out["profile"] == api["visibility_profile"]
    assert out["movies"] == api["visibility_movies"]
    assert out["tv"] == api["visibility_tv"]
    assert out["books"] == api["visibility_books"]
    assert out["games"] == api["visibility_games"]
    assert out["movies_watchlist"] == api["visibility_watchlist_movies"]
    assert out["tv_watchlist"] == api["visibility_watchlist_tv"]
    assert out["books_watchlist"] == api["visibility_watchlist_books"]
    assert out["games_watchlist"] == api["visibility_watchlist_games"]
    assert sorted(set(NINE_VISIBILITY_TARGETS)) == sorted(
        set(NINE_VISIBILITY_TARGETS) & set(out)
    )


@patch("druthers_mcp.server.client")
def test_set_visibility_sends_shelf_tier(mock_client):
    mock_client.return_value.update_visibility.return_value = {
        "handle": "adam-prime",
        "default_privacy": "friends",
        "visibility_profile": "private",
        "visibility_movies": "public",
        "visibility_tv": None,
        "visibility_books": None,
        "visibility_games": None,
        "visibility_watchlist_movies": None,
        "visibility_watchlist_tv": None,
        "visibility_watchlist_books": None,
        "visibility_watchlist_games": None,
    }

    out = server.set_visibility("movies", "public")

    mock_client.return_value.update_visibility.assert_called_once_with(
        visibility_movies="public"
    )
    assert out["movies"] == "public"


@patch("druthers_mcp.server.client")
def test_set_visibility_sends_watchlist_tier(mock_client):
    mock_client.return_value.update_visibility.return_value = {
        "handle": "adam-prime",
        "default_privacy": "friends",
        "visibility_profile": "private",
        "visibility_movies": None,
        "visibility_tv": None,
        "visibility_books": None,
        "visibility_games": None,
        "visibility_watchlist_movies": None,
        "visibility_watchlist_tv": None,
        "visibility_watchlist_books": None,
        "visibility_watchlist_games": "friends",
    }

    server.set_visibility("games_watchlist", "friends")

    mock_client.return_value.update_visibility.assert_called_once_with(
        visibility_watchlist_games="friends"
    )


@patch("druthers_mcp.server.client")
def test_set_visibility_claims_handle_alongside_tier(mock_client):
    mock_client.return_value.update_visibility.return_value = {
        "handle": "adam-prime",
        "default_privacy": "friends",
        "visibility_profile": "friends",
        "visibility_movies": None,
        "visibility_tv": None,
        "visibility_books": None,
        "visibility_games": None,
        "visibility_watchlist_movies": None,
        "visibility_watchlist_tv": None,
        "visibility_watchlist_books": None,
        "visibility_watchlist_games": None,
    }

    out = server.set_visibility("profile", "friends", handle="adam-prime")

    mock_client.return_value.update_visibility.assert_called_once_with(
        visibility_profile="friends", handle="adam-prime"
    )
    assert out["handle"] == "adam-prime"


@patch("druthers_mcp.server.client")
def test_set_visibility_claims_handle_alone(mock_client):
    mock_client.return_value.update_visibility.return_value = {
        "handle": "adam-prime",
        "default_privacy": "friends",
        "visibility_profile": "private",
        "visibility_movies": None,
        "visibility_tv": None,
        "visibility_books": None,
        "visibility_games": None,
        "visibility_watchlist_movies": None,
        "visibility_watchlist_tv": None,
        "visibility_watchlist_books": None,
        "visibility_watchlist_games": None,
    }

    out = server.set_visibility(handle="adam-prime")

    mock_client.return_value.update_visibility.assert_called_once_with(
        handle="adam-prime"
    )
    assert out["handle"] == "adam-prime"


@patch("druthers_mcp.server.client")
def test_set_visibility_invariant_violation_returns_api_explanation(mock_client):
    mock_client.return_value.update_visibility.side_effect = ApiError(
        422,
        "Movies is set to public, so your profile must be at least public "
        "- it is currently friends",
    )

    out = server.set_visibility("movies", "public")

    assert out["error"] == (
        "Movies is set to public, so your profile must be at least public "
        "- it is currently friends"
    )


@patch("druthers_mcp.server.client")
def test_set_visibility_without_handle_returns_actionable_guidance(mock_client):
    mock_client.return_value.update_visibility.side_effect = ApiError(
        422, "Pick a handle before sharing anything - it becomes your profile URL"
    )

    out = server.set_visibility("movies", "public")

    assert "Pick a handle before sharing anything" in out["error"]
    assert "set_visibility" in out["error"]
    assert "handle" in out["error"]


@patch("druthers_mcp.server.client")
def test_set_visibility_rejects_unknown_target(mock_client):
    out = server.set_visibility("audiobooks", "public")

    assert "Unknown target 'audiobooks'" in out["error"]
    mock_client.return_value.update_visibility.assert_not_called()


@patch("druthers_mcp.server.client")
def test_set_visibility_rejects_unknown_tier(mock_client):
    out = server.set_visibility("movies", "everyone")

    assert "Unknown tier 'everyone'" in out["error"]
    mock_client.return_value.update_visibility.assert_not_called()


@patch("druthers_mcp.server.client")
def test_set_visibility_requires_tier_with_target(mock_client):
    out = server.set_visibility("movies")

    assert "tier is required" in out["error"]
    mock_client.return_value.update_visibility.assert_not_called()


@patch("druthers_mcp.server.client")
def test_set_visibility_requires_target_with_tier(mock_client):
    out = server.set_visibility(tier="public")

    assert "target is required" in out["error"]
    mock_client.return_value.update_visibility.assert_not_called()


@patch("druthers_mcp.server.client")
def test_set_visibility_requires_something_to_do(mock_client):
    out = server.set_visibility()

    assert "Pass a target" in out["error"]
    mock_client.return_value.update_visibility.assert_not_called()


def _registered_tool_names() -> set:
    return {t.name for t in server.mcp._tool_manager.list_tools()}


def test_visibility_tools_are_registered():
    names = _registered_tool_names()
    assert "get_visibility" in names
    assert "set_visibility" in names


def test_no_tool_accepts_or_declines_friend_requests():
    names = _registered_tool_names()
    assert not names & {
        "accept_friend_request",
        "decline_friend_request",
        "reject_friend_request",
        "respond_friend_request",
    }


def test_visibility_tool_descriptions_state_what_each_tier_exposes():
    by_name = {t.name: t.description for t in server.mcp._tool_manager.list_tools()}
    for name in ("get_visibility", "set_visibility"):
        desc = by_name[name]
        assert "private" in desc
        assert "friends" in desc
        assert "public" in desc
        assert "internet" in desc
    assert "watchlist" in by_name["set_visibility"]
