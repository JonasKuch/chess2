"""
Let the bot play one game against Stockfish and record it.

Every position is drawn with the normal GUI renderer (headless, no window opens)
and the frames are written as an animated GIF.

    uv run python examples/record_game.py
    uv run python examples/record_game.py --color black --elo 1500 --out docs/demo.gif

Needs Stockfish (on PATH or via STOCKFISH_PATH).
"""

import argparse
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image

from chess2 import Color
from chess2.game import Game
from chess2.bot.move_generation import get_stockfish


def frame(game, view):
    """Draw the current position and return the board area as a PIL image."""
    game.gui.draw_all_game(view)
    r = game.gui.board_renderer
    size = int(r.square_width * 8)
    area = pygame.Rect(int(r.offset_x), int(r.offset_y), size, size)
    surface = game.gui.window.screen.subsurface(area)
    return Image.frombytes("RGB", surface.get_size(), pygame.image.tobytes(surface, "RGB"))


def square(position):
    x, y = position
    return "abcdefgh"[x] + str(y + 1)


def main():
    parser = argparse.ArgumentParser(description="Record the bot playing Stockfish as a GIF.")
    parser.add_argument("--color", choices=["white", "black"], default="white", help="the bot's color")
    parser.add_argument("--elo", type=int, default=1350, help="Stockfish strength (UCI_Elo, min ~1320)")
    parser.add_argument("--simulations", type=int, default=400, help="MCTS simulations per bot move")
    parser.add_argument("--max-plies", type=int, default=200, help="stop the game after this many half-moves")
    parser.add_argument("--delay", type=int, default=600, help="milliseconds per move in the GIF")
    parser.add_argument("--size", type=int, default=480, help="GIF width/height in pixels")
    parser.add_argument("--out", default="games/game.gif", help="where to save the GIF")
    args = parser.parse_args()

    bot_color = Color.WHITE if args.color == "white" else Color.BLACK
    get_stockfish().set_elo_rating(args.elo)

    game = Game(use_mcts=True, num_simulations=args.simulations)
    game.start_game()
    game.move.cache_board_state(game.board)
    board = game.board

    frames = [frame(game, bot_color)]

    for ply in range(args.max_plies):
        side = board.turn
        if side == bot_color:
            new_board = game.bot.bot_move(side, board)
        else:
            new_board = game.bot.stockfish_move(side, board)

        start, end = new_board.last_move
        print(f"{ply + 1:>3}. {'bot' if side == bot_color else 'sf '}  {square(start)}{square(end)}", flush=True)

        board.load_state(new_board)
        game.swap_turns(False)
        game.move.cache_board_state(board)
        frames.append(frame(game, bot_color))
        if game.check_for_end():
            break

    print(f"\nresult: {game.message or 'stopped at --max-plies'}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    frames = [f.resize((args.size, args.size), Image.LANCZOS) for f in frames]
    durations = [args.delay] * (len(frames) - 1) + [3000]   # hold the final position
    frames[0].save(args.out, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"saved {args.out} ({os.path.getsize(args.out) / 1e6:.1f} MB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
