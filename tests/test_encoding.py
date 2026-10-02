"""
Inference must feed the net exactly what it saw in training.

tests/fixtures/leela_sample.pkl holds 2000 raw records (1000 from the start of the
training range, 1000 from the validation range) in the format of
data_leela/chess_data_list.pkl. For each record we rebuild the real position as a
python-chess board, encode its FEN with TensorProcessor.fen_to_tensor and compare
against train.decode_records.

Leela layout, worked out from the data: bit i of a bitboard is square i ^ 7 (files
mirrored) seen from the side to move, so for black it is i ^ 63. Flag 4 is 1 when
black is to move. Record 0 is the start position with flag 0.
"""

import os

import chess
import joblib
import numpy as np
import pytest

from chess2.bot import TensorProcessor
from chess2.bot.train import decode_records

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "leela_sample.pkl")
PIECES = "PNBRKQ"  # model plane order, own pieces 0-5, opponent 6-11


def record_to_board(bitboards, flags):
    black = bool(flags[4] == 1)
    board = chess.Board(None)
    for plane in range(12):
        bits = int(bitboards[plane])
        own = plane < 6
        color = chess.BLACK if own == black else chess.WHITE
        piece_type = chess.Piece.from_symbol(PIECES[plane % 6]).piece_type
        for i in range(64):
            if bits >> i & 1:
                board.set_piece_at(i ^ (63 if black else 7), chess.Piece(piece_type, color))
    board.turn = chess.BLACK if black else chess.WHITE

    us_ooo, us_oo, them_ooo, them_oo = (bool(f) for f in flags[:4])
    if black:
        rights = ("K" if them_oo else "") + ("Q" if them_ooo else "") + ("k" if us_oo else "") + ("q" if us_ooo else "")
    else:
        rights = ("K" if us_oo else "") + ("Q" if us_ooo else "") + ("k" if them_oo else "") + ("q" if them_ooo else "")
    board.set_castling_fen(rights or "-")
    return board


@pytest.fixture(scope="module")
def records():
    raw = joblib.load(FIXTURE)
    boards, flags, labels, _ = decode_records(raw)
    return raw, boards, flags, labels


def test_sample_has_both_colors(records):
    _, _, flags, _ = records
    assert 0 < flags[:, 4].sum() < len(flags)


def test_start_position_is_record_zero(records):
    raw = records[0]
    board = record_to_board(raw[0][0], raw[0][1])
    assert board.fen() == chess.Board().fen()


@pytest.mark.parametrize("color", ["white", "black"])
def test_fen_to_tensor_matches_training(records, color):
    raw, boards, flags, _ = records
    tp = TensorProcessor()
    want_black = color == "black"
    checked = 0
    for i, (bb, fl, _, _) in enumerate(raw):
        if bool(fl[4] == 1) != want_black:
            continue
        fen = record_to_board(bb, fl).fen()
        tensor, fen_flags, _ = tp.fen_to_tensor(fen)
        assert np.array_equal(tensor[0], boards[i]), f"board mismatch at record {i}: {fen}"
        assert np.array_equal(fen_flags[0], flags[i]), f"flag mismatch at record {i}: {fen}"
        checked += 1
    assert checked > 500


@pytest.mark.parametrize("color", ["white", "black"])
def test_labels_are_legal_moves(records, color):
    """Every training label has to be one of the indices legal_move_indices produces
    for that position (this also covers Leela's king-takes-rook castling)."""
    raw, _, _, labels = records
    tp = TensorProcessor()
    want_black = color == "black"
    missing = []
    for i, (bb, fl, _, _) in enumerate(raw):
        if bool(fl[4] == 1) != want_black:
            continue
        board = record_to_board(bb, fl)
        if int(labels[i]) not in tp.legal_move_indices(board):
            missing.append((i, tp.index_to_uci(int(labels[i]), "b" if want_black else "w"), board.fen()))
    # en passant squares aren't stored in the records, so an en passant capture
    # can't be legal in the rebuilt position; nothing else may be missing
    for i, uci, fen in missing:
        board = chess.Board(fen)
        frm, to = chess.parse_square(uci[:2]), chess.parse_square(uci[2:4])
        assert board.piece_type_at(frm) == chess.PAWN and chess.square_file(frm) != chess.square_file(to) \
            and board.piece_at(to) is None, f"label {uci} not legal at record {i}: {fen}"
