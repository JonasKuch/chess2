import os

# resolved relative to this file so the GUI works from any working directory
ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "Roboto-Regular.ttf")
PIECES_DIR = os.path.join(ASSETS_DIR, "pieces_img")