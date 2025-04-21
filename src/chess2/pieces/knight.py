from chess2.pieces import Piece
from chess2 import Color, PieceType



class Knight(Piece):
    def __init__(self, color, position, board):
        super().__init__(color, position, board)
        self.str = 'N' if self._color == Color.WHITE else 'n'
        self.type = PieceType.KNIGHT


    def get_pseudo_legal_moves(self):
        possible_moves = []
        directions = [(1, 2), (2, 1), (1, -2), (-2, 1), (-2, -1), (-1, -2), (-2, 1), (-1, 2)]

        for direction in directions:
            x_pos, y_pos = self._position
            x_dir, y_dir = direction
            new_pos = (x_pos+x_dir, y_pos+y_dir)
            # Check if new position on board
            if not self.board.in_bounds(new_pos): continue
            # Check if new position is empty or opposing piece
            if self.board.is_empty(new_pos) or not self.board.grid[y_pos+y_dir][x_pos+x_dir]._color == self._color: possible_moves.append(new_pos)
        
        return possible_moves