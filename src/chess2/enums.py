from enum import Enum



class Color(Enum):
    WHITE = "White"
    BLACK = "Black"
    DRAW = "Draw"
    STALEMATE = "Stalemate"



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
    PROMOTE = "promote"