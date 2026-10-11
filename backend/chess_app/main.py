import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .game import Game, GameError

DEV = os.environ.get("CHESS_DEV") == "1"

app = FastAPI()
game = Game(Path(os.environ.get("CHESS_DATA", "data")) / "results.jsonl")
connections: dict[WebSocket, str] = {}


def handle(user: str, message: dict) -> None:
    match message:
        case {"type": "start", "colour": colour}:
            game.start(user, colour)
        case {"type": "join"}:
            game.join(user)
        case {"type": "move", "uci": str(uci)}:
            game.move(user, uci)
        case {"type": "resign"}:
            game.resign(user)
        case {"type": "request", "kind": str(kind)}:
            game.make_request(user, kind)
        case {"type": "reply", "accept": bool(accept)}:
            game.reply(user, accept)
        case _:
            raise GameError("Unknown message")


async def broadcast() -> None:
    for ws, user in list(connections.items()):
        try:
            await ws.send_json(game.state(user))
        except Exception:
            connections.pop(ws, None)


@app.websocket("/ws")
async def play(ws: WebSocket, name: str | None = None) -> None:
    user = ws.headers.get("x-user") or (name if DEV else None)
    if not user:
        await ws.close(code=1008, reason="Not signed in")
        return
    await ws.accept()
    connections[ws] = user
    try:
        await ws.send_json(game.state(user))
        while True:
            try:
                handle(user, await ws.receive_json())
            except GameError as e:
                await ws.send_json({"type": "error", "message": str(e)})
                continue
            await broadcast()
    except WebSocketDisconnect:
        pass
    finally:
        connections.pop(ws, None)


app.mount("/", StaticFiles(directory=os.environ.get("CHESS_STATIC", "static"), html=True, check_dir=False))
