from chess2.pieces import Piece
from chess2 import Color, PieceType



class Bishop(Piece):
    def __init__(self, color, position, board):
        super().__init__(color, position, board)
        self.str = 'B' if self._color == Color.WHITE else 'b'
        self.type = PieceType.BISHOP


    def get_pseudo_legal_moves(self):
        possibel_moves = []
        directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]

        for direction in directions:
            x_dir, y_dir = direction
            x_pos, y_pos = self._position
            while True:
                x_pos += x_dir
                y_pos += y_dir
                new_pos = (x_pos, y_pos)
                if not self.board.in_bounds(new_pos): break
                if not self.board.is_empty(new_pos): 
                    if not self.board.grid[y_pos][x_pos]._color == self._color: possibel_moves.append(new_pos)
                    break
                possibel_moves.append(new_pos)
        
        return possibel_moves
