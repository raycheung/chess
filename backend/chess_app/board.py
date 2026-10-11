from dataclasses import dataclass

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FILES = "abcdefgh"


def square(name: str) -> int:
    return FILES.index(name[0]) + 8 * (int(name[1]) - 1)


def square_name(sq: int) -> str:
    return f"{FILES[sq % 8]}{sq // 8 + 1}"


@dataclass(frozen=True)
class Position:
    board: tuple[str, ...]  # 64 squares, a1=0 … h8=63; "" empty, uppercase white, lowercase black
    turn: str
    castling: str
    en_passant: int | None
    halfmove: int
    fullmove: int


def parse_fen(fen: str) -> Position:
    placement, turn, castling, en_passant, halfmove, fullmove = fen.split()
    board = [""] * 64
    for row, rank_text in enumerate(placement.split("/")):
        file = 0
        for char in rank_text:
            if char.isdigit():
                file += int(char)
            else:
                board[(7 - row) * 8 + file] = char
                file += 1
    return Position(
        board=tuple(board),
        turn=turn,
        castling="" if castling == "-" else castling,
        en_passant=None if en_passant == "-" else square(en_passant),
        halfmove=int(halfmove),
        fullmove=int(fullmove),
    )


def to_fen(pos: Position) -> str:
    rows = []
    for rank in range(7, -1, -1):
        row, empty = "", 0
        for piece in pos.board[rank * 8 : rank * 8 + 8]:
            if not piece:
                empty += 1
                continue
            row += (str(empty) if empty else "") + piece
            empty = 0
        rows.append(row + (str(empty) if empty else ""))
    en_passant = "-" if pos.en_passant is None else square_name(pos.en_passant)
    return f"{'/'.join(rows)} {pos.turn} {pos.castling or '-'} {en_passant} {pos.halfmove} {pos.fullmove}"
