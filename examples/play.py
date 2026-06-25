"""
Play a game against the trained neural-net bot (GUI).

Launches the pygame interface: choose your color / options on the start screen,
then click to move. The bot replies with the latest trained checkpoint.

    python examples/play.py
"""

from chess2.game import Game

# Latest trained model. Swap this path to try a different checkpoint -- if it was
# trained with a different tower/head size, also pass the matching architecture
# to MoveGenerator (see MoveGenerator.__init__).
CKPT = "/Users/jonas/coding/python/chess2/src/chess2/bot/saved_models/model_adamw_b256_e20_lr0.001_rb6_c96_best.pth"


if __name__ == "__main__":
    Game(bot_pth=CKPT).play()
