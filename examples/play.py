"""
Play a game against the trained neural-net bot (GUI).

Launches the pygame interface: choose your color / options on the start screen,
then click to move. The bot replies with the latest trained checkpoint.

    python examples/play.py
"""

from chess2.game import Game

# Latest trained model (policy + value head). Swap this path to try a different
# checkpoint -- if it was trained with a different tower/head size, also pass the
# matching architecture to MoveGenerator (see MoveGenerator.__init__).
CKPT = "/Users/jonas/coding/python/chess2/src/chess2/bot/saved_models/model_adamw_b256_e12_lr0.001_rb6_c96_value_best.pth"

# MCTS makes the bot stronger than the raw policy by looking ahead -- BUT only
# with enough simulations. Too few (~100) and the shallow search hangs pieces it
# can't yet see captured, playing WORSE than the raw policy. ~400+ is a decent
# floor; higher = stronger but slower (each move is num_simulations net evals on
# CPU, ~2-4s at 400). Set USE_MCTS=False to play the raw policy instead.
USE_MCTS = True
NUM_SIMULATIONS = 400


if __name__ == "__main__":
    Game(bot_pth=CKPT, use_mcts=USE_MCTS, num_simulations=NUM_SIMULATIONS).play()
