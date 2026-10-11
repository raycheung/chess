import pytest

from chess_app.board import START_FEN, parse_fen
from chess_app.rules import apply, legal_moves

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def perft(pos, depth):
    moves = legal_moves(pos)
    if depth == 1:
        return len(moves)
    return sum(perft(apply(pos, m), depth - 1) for m in moves)


@pytest.mark.parametrize("depth, nodes", [(1, 20), (2, 400), (3, 8902), (4, 197281)])
def test_start_position(depth, nodes):
    assert perft(parse_fen(START_FEN), depth) == nodes


@pytest.mark.parametrize("depth, nodes", [(1, 48), (2, 2039), (3, 97862)])
def test_kiwipete(depth, nodes):
    assert perft(parse_fen(KIWIPETE), depth) == nodes
