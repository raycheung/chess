from dataclasses import dataclass

from .board import Position, square, square_name

KNIGHT = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
ROOK = [(1, 0), (0, 1), (-1, 0), (0, -1)]
BISHOP = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
KING = ROOK + BISHOP
SLIDERS = {"r": ROOK, "b": BISHOP, "q": ROOK + BISHOP}

# castling right: (king from, king to, rook from, rook to, squares between that must be empty)
CASTLES = {
    "K": (4, 6, 7, 5, (5, 6)),
    "Q": (4, 2, 0, 3, (1, 2, 3)),
    "k": (60, 62, 63, 61, (61, 62)),
    "q": (60, 58, 56, 59, (57, 58, 59)),
}


@dataclass(frozen=True)
class Move:
    start: int
    end: int
    promotion: str = ""

    @property
    def uci(self) -> str:
        return square_name(self.start) + square_name(self.end) + self.promotion

    @staticmethod
    def from_uci(text: str) -> "Move":
        return Move(square(text[0:2]), square(text[2:4]), text[4:])


def colour(piece: str) -> str:
    return "w" if piece.isupper() else "b"


def opponent(side: str) -> str:
    return "b" if side == "w" else "w"


def piece_of(kind: str, side: str) -> str:
    return kind.upper() if side == "w" else kind


def step(sq: int, df: int, dr: int) -> int | None:
    file, rank = sq % 8 + df, sq // 8 + dr
    return rank * 8 + file if 0 <= file < 8 and 0 <= rank < 8 else None


def is_attacked(board: tuple[str, ...], sq: int, by: str) -> bool:
    for kind, vectors in (("n", KNIGHT), ("k", KING)):
        for df, dr in vectors:
            target = step(sq, df, dr)
            if target is not None and board[target] == piece_of(kind, by):
                return True
    pawn_rank = -1 if by == "w" else 1
    for df in (-1, 1):
        target = step(sq, df, pawn_rank)
        if target is not None and board[target] == piece_of("p", by):
            return True
    for kind, vectors in (("r", ROOK), ("b", BISHOP)):
        for df, dr in vectors:
            target = step(sq, df, dr)
            while target is not None and not board[target]:
                target = step(target, df, dr)
            if target is not None and board[target] in (piece_of(kind, by), piece_of("q", by)):
                return True
    return False


def pawn_moves(pos: Position, sq: int):
    board, forward = pos.board, 1 if pos.turn == "w" else -1
    targets = []
    one = step(sq, 0, forward)
    if one is not None and not board[one]:
        targets.append(one)
        if sq // 8 == (1 if pos.turn == "w" else 6) and not board[sq + 16 * forward]:
            targets.append(sq + 16 * forward)
    for df in (-1, 1):
        target = step(sq, df, forward)
        if target is not None and (
            target == pos.en_passant or (board[target] and colour(board[target]) != pos.turn)
        ):
            targets.append(target)
    for target in targets:
        if target // 8 in (0, 7):
            yield from (Move(sq, target, kind) for kind in "qrbn")
        else:
            yield Move(sq, target)


def castling_moves(pos: Position):
    for right in pos.castling:
        if colour(right) != pos.turn:
            continue
        king, king_to, _, rook_to, between = CASTLES[right]
        if any(pos.board[s] for s in between):
            continue
        if not any(is_attacked(pos.board, s, opponent(pos.turn)) for s in (king, rook_to, king_to)):
            yield Move(king, king_to)


def pseudo_moves(pos: Position):
    board = pos.board
    for sq, piece in enumerate(board):
        if not piece or colour(piece) != pos.turn:
            continue
        kind = piece.lower()
        if kind == "p":
            yield from pawn_moves(pos, sq)
            continue
        for df, dr in SLIDERS.get(kind) or (KNIGHT if kind == "n" else KING):
            target = step(sq, df, dr)
            while target is not None and not board[target]:
                yield Move(sq, target)
                target = step(target, df, dr) if kind in SLIDERS else None
            if target is not None and board[target] and colour(board[target]) != pos.turn:
                yield Move(sq, target)
    yield from castling_moves(pos)


def apply(pos: Position, move: Move) -> Position:
    board = list(pos.board)
    piece, captured = board[move.start], board[move.end]
    kind = piece.lower()
    board[move.end], board[move.start] = piece, ""
    if kind == "p" and move.end == pos.en_passant:
        captured = board[move.end - (8 if pos.turn == "w" else -8)]
        board[move.end - (8 if pos.turn == "w" else -8)] = ""
    if move.promotion:
        board[move.end] = piece_of(move.promotion, pos.turn)
    if kind == "k" and abs(move.end - move.start) == 2:
        _, _, rook_from, rook_to, _ = next(c for c in CASTLES.values() if c[1] == move.end)
        board[rook_to], board[rook_from] = board[rook_from], ""
    touched = {move.start, move.end}
    return Position(
        board=tuple(board),
        turn=opponent(pos.turn),
        castling="".join(r for r in pos.castling if not touched & {CASTLES[r][0], CASTLES[r][2]}),
        en_passant=(move.start + move.end) // 2 if kind == "p" and abs(move.end - move.start) == 16 else None,
        halfmove=0 if kind == "p" or captured else pos.halfmove + 1,
        fullmove=pos.fullmove + (pos.turn == "b"),
    )


def king_square(board: tuple[str, ...], side: str) -> int:
    return board.index(piece_of("k", side))


def in_check(pos: Position) -> bool:
    return is_attacked(pos.board, king_square(pos.board, pos.turn), opponent(pos.turn))


def legal_moves(pos: Position) -> list[Move]:
    def keeps_king_safe(move: Move) -> bool:
        after = apply(pos, move)
        return not is_attacked(after.board, king_square(after.board, pos.turn), after.turn)

    return [m for m in pseudo_moves(pos) if keeps_king_safe(m)]


def insufficient_material(board: tuple[str, ...]) -> bool:
    others = [(sq, p.lower()) for sq, p in enumerate(board) if p and p.lower() != "k"]
    if len(others) <= 1 and all(kind in "nb" for _, kind in others):
        return True
    return all(kind == "b" for _, kind in others) and len({(sq % 8 + sq // 8) % 2 for sq, _ in others}) == 1


def outcome(pos: Position) -> str | None:
    if not legal_moves(pos):
        return "checkmate" if in_check(pos) else "stalemate"
    if pos.halfmove >= 100:
        return "fifty-move rule"
    if insufficient_material(pos.board):
        return "insufficient material"
    return None


def repetition_key(pos: Position) -> tuple:
    en_passant_possible = any(
        m.end == pos.en_passant and pos.board[m.start].lower() == "p" for m in legal_moves(pos)
    )
    return pos.board, pos.turn, pos.castling, pos.en_passant if en_passant_possible else None
