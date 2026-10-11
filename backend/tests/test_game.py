import json

import pytest

from chess_app.game import Game, GameError


@pytest.fixture
def game(tmp_path):
    return Game(tmp_path / "results.jsonl")


@pytest.fixture
def playing(game):
    game.start("ann", "white")
    game.join("bob")
    return game


def test_starter_picks_black_and_joiner_gets_white(game):
    game.start("ann", "black")
    game.join("bob")
    assert (game.white, game.black, game.phase) == ("bob", "ann", "playing")


def test_starter_can_restart_while_waiting(game):
    game.start("ann", "white")
    game.start("ann", "black")
    assert (game.white, game.black) == (None, "ann")


def test_other_player_must_join_not_restart(game):
    game.start("ann", "white")
    with pytest.raises(GameError):
        game.start("bob", "white")


def test_cannot_play_both_sides(game):
    game.start("ann", "white")
    with pytest.raises(GameError):
        game.join("ann")


def test_game_locked_once_both_joined(playing):
    for user in ("ann", "bob"):
        with pytest.raises(GameError):
            playing.start(user, "white")


def test_rejoin_keeps_seat(playing):
    assert playing.state("ann")["white"] == "ann"
    assert playing.side_of("bob") == "b"


def test_moves_only_on_own_turn(playing):
    with pytest.raises(GameError):
        playing.move("bob", "e7e5")
    with pytest.raises(GameError):
        playing.move("ann", "e2e5")
    playing.move("ann", "e2e4")
    assert playing.state("bob")["lastMove"] == ["e2", "e4"]


def test_undo_before_reply_takes_back_one_move(playing):
    playing.move("ann", "e2e4")
    playing.request_undo("ann")
    playing.reply_undo("bob", True)
    assert len(playing.moves) == 0


def test_undo_after_reply_takes_back_two_moves(playing):
    playing.move("ann", "e2e4")
    playing.move("bob", "e7e5")
    playing.request_undo("ann")
    playing.reply_undo("bob", True)
    assert len(playing.moves) == 0 and playing.position.turn == "w"


def test_declined_undo_changes_nothing(playing):
    playing.move("ann", "e2e4")
    playing.request_undo("ann")
    playing.reply_undo("bob", False)
    assert len(playing.moves) == 1 and playing.undo_requested_by is None


def test_move_cancels_undo_request(playing):
    playing.move("ann", "e2e4")
    playing.request_undo("ann")
    playing.move("bob", "e7e5")
    assert playing.undo_requested_by is None


def test_cannot_answer_own_undo_request(playing):
    playing.move("ann", "e2e4")
    playing.request_undo("ann")
    with pytest.raises(GameError):
        playing.reply_undo("ann", True)


def test_nothing_to_undo_at_start(playing):
    with pytest.raises(GameError):
        playing.request_undo("ann")


def test_checkmate_finishes_and_records(playing):
    for user, uci in [("ann", "e2e4"), ("bob", "e7e5"), ("ann", "f1c4"), ("bob", "b8c6"),
                      ("ann", "d1h5"), ("bob", "g8f6"), ("ann", "h5f7")]:
        playing.move(user, uci)
    assert (playing.phase, playing.winner, playing.reason) == ("finished", "white", "checkmate")
    with pytest.raises(GameError):
        playing.request_undo("bob")
    assert playing.score() == {"wins": {"ann": 1}, "draws": 0}


def test_resign_and_next_game(playing):
    playing.resign("ann")
    record = json.loads(playing.results_path.read_text())
    assert (record["winner"], record["reason"]) == ("black", "resignation")
    playing.start("ann", "black")
    assert playing.phase == "waiting" and playing.moves == []


def test_threefold_repetition_is_a_draw(playing):
    shuffle = [("ann", "g1f3"), ("bob", "g8f6"), ("ann", "f3g1"), ("bob", "f6g8")]
    for user, uci in shuffle:
        playing.move(user, uci)
    assert playing.phase == "playing"
    for user, uci in shuffle:
        playing.move(user, uci)
    assert (playing.phase, playing.winner, playing.reason) == ("finished", None, "threefold repetition")
