from chess2.pieces import Piece
from chess2 import Color, PieceType



class Rook(Piece):
    def __init__(self, color, position, board):
        super().__init__(color, position, board)
        self.str = 'R' if self._color == Color.WHITE else 'r'
        self.type = PieceType.ROOK


    def get_pseudo_legal_moves(self):
        possibel_moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

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


    def move(self, end_position):
        start_x, _ = self._position
        if self._move_is_legal(end_position):
            if not self.board.is_empty(end_position): 
                x, y = end_position
                self.board.grid[y][x]._captured = True
            self._position = end_position
            self._has_moved = True
            self.reset_en_passant_vulnerabiity()
            self.board.manage_castelling_squares_under_attack()

            # Manage Castelling
            if start_x == 7:
                if self._color == Color.WHITE: self.board.white_king.can_castle_kingside = False
                if self._color == Color.BLACK: self.board.black_king.can_castle_kingside = False
            if start_x == 0:
                if self._color == Color.WHITE: self.board.white_king.can_castle_queenside = False
                if self._color == Color.BLACK: self.board.black_king.can_castle_queenside = False
