from enum import Enum



class Color(Enum):
    WHITE = "White"
    BLACK = "Black"



class PieceType(Enum):
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"


class Action(Enum):
    MOVED = "moved"
    IGNORED = "ignored"
    SELECTED = "selected"
    BACKBUTTONDOWN = "back button was pushed"
    FORWARDBUTTONDOWN = "forward button was pushed"