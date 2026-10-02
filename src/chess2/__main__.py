"""
Start the GUI. Installed as the `chess2` command, so `uv run chess2` works,
and `python -m chess2` does the same.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(prog="chess2", description="Play chess against the neural-net bot.")
    parser.add_argument("--simulations", type=int, default=1000,
                        help="MCTS simulations per bot move (default 1000; below ~400 the bot hangs pieces)")
    parser.add_argument("--no-mcts", action="store_true",
                        help="play the raw policy instead of searching (fast, much weaker)")
    parser.add_argument("--model", default=None,
                        help="path to other weights (default: the ones shipped with the package)")
    args = parser.parse_args()

    # imported here so --help doesn't have to load pygame and torch
    from chess2.game import Game

    Game(bot_pth=args.model, use_mcts=not args.no_mcts, num_simulations=args.simulations).play()


if __name__ == "__main__":
    main()
