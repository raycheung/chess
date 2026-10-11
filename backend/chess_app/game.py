import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .board import START_FEN, Position, parse_fen, square_name, to_fen
from .rules import Move, apply, in_check, legal_moves, outcome, repetition_key

SIDES = {"white": "w", "black": "b"}


class GameError(Exception):
    pass


@dataclass
class Game:
    results_path: Path
    phase: str = "idle"  # idle → waiting → playing → finished
    white: str | None = None
    black: str | None = None
    positions: list[Position] = field(default_factory=lambda: [parse_fen(START_FEN)])
    moves: list[Move] = field(default_factory=list)
    request: tuple[str, str] | None = None  # (kind "undo" | "draw", requesting user)
    winner: str | None = None
    reason: str | None = None

    @property
    def position(self) -> Position:
        return self.positions[-1]

    def side_of(self, user: str) -> str | None:
        return {self.white: "w", self.black: "b"}.get(user)

    def start(self, user: str, colour: str) -> None:
        if self.phase == "playing":
            raise GameError("A game is in progress — finish it first")
        if self.phase == "waiting" and self.side_of(user) is None:
            raise GameError("A game is waiting for you — join it")
        if colour not in SIDES:
            raise GameError("Pick white or black")
        self.phase = "waiting"
        self.white = user if colour == "white" else None
        self.black = user if colour == "black" else None
        self.positions = [parse_fen(START_FEN)]
        self.moves = []
        self.request = self.winner = self.reason = None

    def join(self, user: str) -> None:
        if self.phase != "waiting":
            raise GameError("There is no game waiting for a player")
        if self.side_of(user):
            raise GameError("You can't play both sides")
        if self.white is None:
            self.white = user
        else:
            self.black = user
        self.phase = "playing"

    def require_turn(self, user: str) -> str:
        if self.phase != "playing":
            raise GameError("No game in progress")
        side = self.side_of(user)
        if side is None:
            raise GameError("You're not playing in this game")
        return side

    def move(self, user: str, uci: str) -> None:
        if self.require_turn(user) != self.position.turn:
            raise GameError("Not your turn")
        move = next((m for m in legal_moves(self.position) if m.uci == uci), None)
        if move is None:
            raise GameError("Illegal move")
        self.positions.append(apply(self.position, move))
        self.moves.append(move)
        self.request = None
        if reason := outcome(self.position) or self.threefold_repetition():
            mover = "white" if self.position.turn == "b" else "black"
            self.finish(mover if reason == "checkmate" else None, reason)

    def threefold_repetition(self) -> str | None:
        key = repetition_key(self.position)
        seen = sum(repetition_key(p) == key for p in self.positions)
        return "threefold repetition" if seen >= 3 else None

    def resign(self, user: str) -> None:
        side = self.require_turn(user)
        self.finish("black" if side == "w" else "white", "resignation")

    def undo_plies(self, user: str) -> int:
        return 1 if self.position.turn != self.side_of(user) else 2

    def make_request(self, user: str, kind: str) -> None:
        self.require_turn(user)
        if kind not in ("undo", "draw"):
            raise GameError("Unknown request")
        if self.request:
            raise GameError("Still waiting for an answer")
        if kind == "undo" and len(self.moves) < self.undo_plies(user):
            raise GameError("Nothing to undo yet")
        self.request = (kind, user)

    def reply(self, user: str, accept: bool) -> None:
        self.require_turn(user)
        if self.request is None or self.request[1] == user:
            raise GameError("Nothing to answer")
        kind, requester = self.request
        self.request = None
        if not accept:
            return
        if kind == "draw":
            return self.finish(None, "agreement")
        plies = self.undo_plies(requester)
        del self.positions[-plies:]
        del self.moves[-plies:]

    def finish(self, winner: str | None, reason: str) -> None:
        self.phase, self.winner, self.reason = "finished", winner, reason
        self.request = None
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "date": datetime.now(UTC).isoformat(timespec="seconds"),
            "white": self.white,
            "black": self.black,
            "winner": winner,
            "reason": reason,
        }
        with self.results_path.open("a") as f:
            f.write(json.dumps(record) + "\n")

    def score(self) -> dict:
        wins: dict[str, int] = {}
        draws = 0
        if self.results_path.exists():
            for line in self.results_path.read_text().splitlines():
                result = json.loads(line)
                if result["winner"]:
                    winner = result[result["winner"]]
                    wins[winner] = wins.get(winner, 0) + 1
                else:
                    draws += 1
        return {"wins": wins, "draws": draws}

    def state(self, user: str) -> dict:
        playing = self.phase == "playing"
        last = self.moves[-1] if self.moves else None
        return {
            "type": "state",
            "you": user,
            "phase": self.phase,
            "fen": to_fen(self.position),
            "white": self.white,
            "black": self.black,
            "legalMoves": [m.uci for m in legal_moves(self.position)] if playing else [],
            "check": in_check(self.position),
            "lastMove": [square_name(last.start), square_name(last.end)] if last else None,
            "request": {"kind": self.request[0], "by": self.request[1]} if self.request else None,
            "winner": self.winner,
            "reason": self.reason,
            "score": self.score(),
        }
