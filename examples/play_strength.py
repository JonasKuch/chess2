"""
Estimate the engine's playing strength by matching it against a ladder of
Stockfish opponents at fixed UCI_Elo settings.

For each rung it plays GAMES_PER_LEVEL games (colors alternated), scores them
(win=1, draw=0.5, loss=0), and reports a per-opponent table plus an aggregate
performance-rating estimate of the model's Elo.

Notes / caveats:
- Stockfish's UCI_LimitStrength has a floor around ~1320 Elo on modern builds;
  values below that are clamped, so don't put sub-1320 rungs in ELO mode. If the
  model loses every game even at the lowest rung, it is simply weaker than that
  rung (the estimate becomes a loose lower bound).
- Games that don't end naturally within MAX_PLIES are adjudicated by material
  (a lead of >= ADJUDICATE_MATERIAL points = win), which is a proxy, not truth.
- MCTS is slow on CPU; this is a deliberate benchmark. Lower NUM_SIMULATIONS /
  GAMES_PER_LEVEL for a quick read, raise them for a tighter estimate.

    python examples/play_strength.py
"""

import math
from collections import Counter

from chess2.board import Board
from chess2 import Color
from chess2.bot.move_generation import MoveGenerator
from stockfish import Stockfish

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
MODEL_CKPT = "/Users/jonas/coding/python/chess2/src/chess2/bot/saved_models/model_adamw_b256_e12_lr0.001_rb6_c96_value_best.pth"
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"

USE_MCTS = True
NUM_SIMULATIONS = 200          # MCTS sims per move (lower = faster benchmark)

OPPONENT_ELOS = [1320, 1500, 1700, 1900]   # Stockfish UCI_Elo rungs
GAMES_PER_LEVEL = 2            # colors alternate; keep even for balance
STOCKFISH_DEPTH = 10           # SF search depth cap (kept low for speed)

MAX_PLIES = 120
ADJUDICATE_MATERIAL = 4        # material lead that counts as a win at ply cap

PIECE_VALUE = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9}


# --------------------------------------------------------------------------- #
# HELPERS
# --------------------------------------------------------------------------- #
def material_diff(board):
    """White material minus black material."""
    w = b = 0
    for p in board.pieces_on_board:
        if p._captured:
            continue
        v = PIECE_VALUE.get(p.str.upper(), 0)
        if p.str.isupper():
            w += v
        else:
            b += v
    return w - b


def stockfish_move(mg, sf, side, board):
    """Get Stockfish's move for `board` and return the resulting board."""
    nb = board.clone()
    sf.set_fen_position(nb.to_fen())
    raw = sf.get_best_move()
    if raw is None:
        return None
    return mg.apply_uci(nb, raw, side)


def play_game(mg, sf, model_white, max_plies=MAX_PLIES):
    """Play one game; return the model's score (1.0 win / 0.5 draw / 0.0 loss)."""
    model_color = Color.WHITE if model_white else Color.BLACK
    board = Board()
    board.initialize()
    board.update_grid()
    board.update_checks()
    seen = Counter()

    for _ in range(max_plies):
        side = board.turn

        # --- terminal checks for the side about to move ---
        if board.check_if_mate():
            return 0.0 if side == model_color else 1.0          # side-to-move is mated
        if board.get_possible_moves_of_all_pieces(side) == []:
            return 0.5                                          # stalemate
        if board.halfmove_clock >= 100:
            return 0.5                                          # 50-move rule
        key = " ".join(board.to_fen().split()[:4])
        seen[key] += 1
        if seen[key] >= 3:
            return 0.5                                          # threefold repetition

        # --- make the move ---
        if side == model_color:
            nb = mg.bot_move(side, board)
        else:
            nb = stockfish_move(mg, sf, side, board)
            if nb is None:
                return 0.5
        board.load_state(nb)
        board.turn = Color.BLACK if side == Color.WHITE else Color.WHITE
        board.update_grid()
        board.update_checks()

    # --- no natural result within the cap: adjudicate by material ---
    diff = material_diff(board)                                 # white - black
    model_lead = diff if model_white else -diff
    if model_lead >= ADJUDICATE_MATERIAL:
        return 1.0
    if model_lead <= -ADJUDICATE_MATERIAL:
        return 0.0
    return 0.5


def dp(p):
    """Elo difference implied by a score fraction p (FIDE-style, clamped)."""
    p = min(max(p, 0.01), 0.99)
    return -400 * math.log10(1 / p - 1)


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #
def main():
    mg = MoveGenerator(MODEL_CKPT, use_mcts=USE_MCTS, num_simulations=NUM_SIMULATIONS)
    sf = Stockfish(path=STOCKFISH_PATH, depth=STOCKFISH_DEPTH)

    mode = f"MCTS({NUM_SIMULATIONS})" if USE_MCTS else "raw policy"
    print(f"Benchmarking model [{mode}] vs Stockfish ladder "
          f"({GAMES_PER_LEVEL} games/rung, adjudicate at +{ADJUDICATE_MATERIAL})\n")

    rows = []
    for elo in OPPONENT_ELOS:
        sf.set_elo_rating(elo)
        score = 0.0
        for g in range(GAMES_PER_LEVEL):
            model_white = (g % 2 == 0)
            s = play_game(mg, sf, model_white)
            score += s
            res = {1.0: "win", 0.5: "draw", 0.0: "loss"}[s]
            print(f"  vs SF {elo}  game {g+1}/{GAMES_PER_LEVEL}  "
                  f"model={'W' if model_white else 'B'}  -> {res}", flush=True)
        frac = score / GAMES_PER_LEVEL
        rows.append((elo, score, frac))
        print(f"  => vs SF {elo}: {score}/{GAMES_PER_LEVEL}  ({frac*100:.0f}%)\n", flush=True)

    # --- summary table + performance rating ---
    print("=" * 48)
    print(f"{'Stockfish Elo':>14} | {'score':>10} | {'model%':>7} | {'implied Elo':>11}")
    print("-" * 48)
    for elo, score, frac in rows:
        implied = "" if frac in (0.0, 1.0) else f"{elo - dp(frac):.0f}"
        print(f"{elo:>14} | {score:>4}/{GAMES_PER_LEVEL:<5} | {frac*100:>6.0f}% | {implied:>11}")
    print("=" * 48)

    total = sum(score for _, score, _ in rows)
    games = GAMES_PER_LEVEL * len(rows)
    p = total / games
    avg_opp = sum(elo for elo, _, _ in rows) / len(rows)
    perf = avg_opp + dp(p)
    print(f"overall: {total}/{games} ({p*100:.0f}%) vs avg opponent {avg_opp:.0f}")
    if p <= 0.01:
        print(f"estimated strength: < ~{min(OPPONENT_ELOS)} (lost ~every game; loose lower bound)")
    elif p >= 0.99:
        print(f"estimated strength: > ~{max(OPPONENT_ELOS)} (won ~every game; loose upper bound)")
    else:
        print(f"estimated performance rating: ~{perf:.0f} Elo")
    print("(adjust OPPONENT_ELOS to bracket the ~50% crossover for a tighter estimate)")


if __name__ == "__main__":
    main()
