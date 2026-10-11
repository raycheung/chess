import pytest
from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient

from chess_app import main
from chess_app.game import Game


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "game", Game(tmp_path / "results.jsonl"))
    with TestClient(main.app) as client:
        yield client


def connect(client, user):
    return client.websocket_connect("/ws", headers={"x-user": user})


def test_rejects_anonymous(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()


def test_move_is_broadcast_to_both_players(client):
    with connect(client, "ann") as ann, connect(client, "bob") as bob:
        ann.receive_json(), bob.receive_json()
        ann.send_json({"type": "start", "colour": "white"})
        ann.receive_json(), bob.receive_json()
        bob.send_json({"type": "join"})
        ann.receive_json(), bob.receive_json()
        ann.send_json({"type": "move", "uci": "e2e4"})
        assert ann.receive_json()["lastMove"] == ["e2", "e4"]
        state = bob.receive_json()
        assert state["you"] == "bob" and "e7e5" in state["legalMoves"]


def test_illegal_move_returns_error_to_sender(client):
    with connect(client, "ann") as ann:
        ann.receive_json()
        ann.send_json({"type": "move", "uci": "e2e4"})
        assert ann.receive_json() == {"type": "error", "message": "No game in progress"}
