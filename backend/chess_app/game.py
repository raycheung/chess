import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .board import START_FEN, Position, parse_fen, square_name, to_fen
from .rules import Move, apply, in_check, legal_moves, outcome

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
    undo_requested_by: str | None = None
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
        self.undo_requested_by = self.winner = self.reason = None

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
        self.undo_requested_by = None
        if reason := outcome(self.position):
            mover = "white" if self.position.turn == "b" else "black"
            self.finish(mover if reason == "checkmate" else None, reason)

    def resign(self, user: str) -> None:
        side = self.require_turn(user)
        self.finish("black" if side == "w" else "white", "resignation")

    def undo_plies(self, user: str) -> int:
        return 1 if self.position.turn != self.side_of(user) else 2

    def request_undo(self, user: str) -> None:
        self.require_turn(user)
        if len(self.moves) < self.undo_plies(user):
            raise GameError("Nothing to undo yet")
        self.undo_requested_by = user

    def reply_undo(self, user: str, accept: bool) -> None:
        self.require_turn(user)
        requester = self.undo_requested_by
        if requester is None or requester == user:
            raise GameError("No undo request to answer")
        if accept:
            plies = self.undo_plies(requester)
            del self.positions[-plies:]
            del self.moves[-plies:]
        self.undo_requested_by = None

    def finish(self, winner: str | None, reason: str) -> None:
        self.phase, self.winner, self.reason = "finished", winner, reason
        self.undo_requested_by = None
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
            "undoRequestedBy": self.undo_requested_by,
            "winner": self.winner,
            "reason": self.reason,
            "score": self.score(),
        }
