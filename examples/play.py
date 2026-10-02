"""
Play a game against the trained neural-net bot (GUI).

Launches the pygame interface: choose your color / options on the start screen,
then click to move. The bot replies with the latest trained checkpoint.

    python examples/play.py
"""

from chess2.game import Game

# None = the weights shipped with the package (or $CHESS2_MODEL if set).
# A checkpoint with a different tower/head size also needs the matching
# architecture in MoveGenerator (see MoveGenerator.__init__).
CKPT = None

# MCTS makes the bot stronger than the raw policy by looking ahead -- BUT only
# with enough simulations. Too few (~100) and the shallow search hangs pieces it
# can't yet see captured, playing WORSE than the raw policy. ~400+ is a decent
# floor; higher = stronger but slower (each move is num_simulations net evals on
# CPU, ~2-4s at 400). Set USE_MCTS=False to play the raw policy instead.
USE_MCTS = True
NUM_SIMULATIONS = 1000


if __name__ == "__main__":
    Game(bot_pth=CKPT, use_mcts=USE_MCTS, num_simulations=NUM_SIMULATIONS).play()
