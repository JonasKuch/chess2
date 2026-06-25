"""
Headless self-play debug driver.

The GUI game loop (Game.play) blocks on interactive mouse input, so this drives
the engine directly -- board logic + the neural net's MCTS search -- to surface
bugs without a display. Plays the engine against itself and prints each move +
FEN, with end-condition detection mirroring Game.check_for_end.

Set USE_MCTS = False to fall back to the raw policy (faster, weaker).
"""

import os
import traceback
from collections import Counter

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from chess2.board import Board
from chess2 import Color
from chess2.bot import MoveGenerator

CKPT = "/Users/jonas/coding/python/chess2/src/chess2/bot/saved_models/model_adamw_b256_e12_lr0.001_rb6_c96_value_best.pth"
MAX_PLIES = 60
USE_MCTS = True
NUM_SIMULATIONS = 200


def main():
    board = Board()
    board.initialize()
    board.update_grid()
    board.update_checks()

    bot = MoveGenerator(CKPT, use_mcts=USE_MCTS, num_simulations=NUM_SIMULATIONS)
    seen = Counter()
    print("start:", board.to_fen())

    for ply in range(1, MAX_PLIES + 1):
        side = board.turn

        # --- end-condition checks (mirror Game.check_for_end) ---
        if board.check_if_mate():
            winner = Color.BLACK if side == Color.WHITE else Color.WHITE
            print(f"CHECKMATE after {ply-1} plies -- {winner.name} wins")
            return
        if board.get_possible_moves_of_all_pieces(side) == []:
            print(f"STALEMATE after {ply-1} plies")
            return
        if board.halfmove_clock >= 100:
            print("50-move-rule DRAW")
            return
        key = " ".join(board.to_fen().split()[:4])
        seen[key] += 1
        if seen[key] >= 3:
            print("THREEFOLD-REPETITION DRAW")
            return

        # --- ask the engine for a move (MCTS if enabled, else raw policy) ---
        new_board = bot.bot_move(side, board)
        board.load_state(new_board)
        board.turn = Color.BLACK if side == Color.WHITE else Color.WHITE
        board.update_grid()
        board.update_checks()

        chk = " +check" if (board.white_king.in_check or board.black_king.in_check) else ""
        print(f"ply {ply:>2} {side.name:<5} -> {board.to_fen()}{chk}")

    print(f"reached MAX_PLIES ({MAX_PLIES}) with no terminal result")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n=== EXCEPTION ===")
        traceback.print_exc()
