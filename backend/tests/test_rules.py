from chess_app.board import START_FEN, parse_fen, to_fen
from chess_app.rules import Move, apply, legal_moves, outcome


def ucis(fen):
    return {m.uci for m in legal_moves(parse_fen(fen))}


def play(fen, *moves):
    pos = parse_fen(fen)
    for uci in moves:
        assert uci in {m.uci for m in legal_moves(pos)}, uci
        pos = apply(pos, Move.from_uci(uci))
    return pos


def test_fen_round_trip():
    for fen in (START_FEN, "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b Kq e3 3 17"):
        assert to_fen(parse_fen(fen)) == fen


def test_double_push_sets_en_passant_square():
    assert to_fen(play(START_FEN, "e2e4")) == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"


def test_en_passant_capture_removes_pawn():
    pos = play("4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 1", "d7d5", "e5d6")
    assert pos.board[35] == ""


def test_castling_both_sides():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    assert {"e1g1", "e1c1"} <= ucis(fen)
    assert to_fen(play(fen, "e1g1")).startswith("r3k2r/8/8/8/8/8/8/R4RK1 b kq")


def test_cannot_castle_through_check():
    assert "e1g1" not in ucis("4kr2/8/8/8/8/8/8/4K2R w K - 0 1")


def test_cannot_castle_out_of_check():
    assert "e1g1" not in ucis("4r1k1/8/8/8/8/8/8/4K2R w K - 0 1")


def test_rook_move_loses_castling_right():
    assert play("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "h1h2").castling == "Qkq"


def test_pinned_piece_cannot_move():
    assert not any(u.startswith("e2") for u in ucis("4r1k1/8/8/8/8/8/4N3/4K3 w - - 0 1"))


def test_promotion_offers_four_pieces():
    assert {"a7a8q", "a7a8r", "a7a8b", "a7a8n"} <= ucis("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")


def test_scholars_mate_is_checkmate():
    pos = play(START_FEN, "e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7")
    assert outcome(pos) == "checkmate"


def test_stalemate():
    assert outcome(parse_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")) == "stalemate"


def test_fifty_move_rule():
    assert outcome(parse_fen("4k3/8/8/8/8/8/8/R3K3 w - - 100 80")) == "fifty-move rule"


def test_insufficient_material():
    assert outcome(parse_fen("4k3/8/8/8/8/8/8/2B1K3 w - - 0 1")) == "insufficient material"
    assert outcome(parse_fen("4kb2/8/8/8/8/8/8/2B1K3 w - - 0 1")) == "insufficient material"
    assert outcome(parse_fen("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")) is None
