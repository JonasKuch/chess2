from chess2.pieces import Piece
from chess2 import Color, PieceType



class King(Piece):
    def __init__(self, color, position, board):
        super().__init__(color, position, board)
        self.str = 'K' if self._color == Color.WHITE else 'k'
        self.type = PieceType.KING
        self.in_check = False
        self.can_castle_kingside = True
        self.can_castle_queenside = True
        self.castelling_square_under_attack_kingside = False
        self.castelling_square_under_attack_queenside = False


    def get_pseudo_legal_moves(self):
        possible_moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        ground_line = 0 if self._color == Color.WHITE else 7

        # Normal moves
        for direction in directions:
            x_pos, y_pos = self._position
            x_dir, y_dir = direction
            new_pos = (x_pos+x_dir, y_pos+y_dir)
            # Check if new position on board
            if not self.board.in_bounds(new_pos): continue
            # Check if new position is empty or opposing piece
            if self.board.is_empty(new_pos) or not self.board.grid[y_pos+y_dir][x_pos+x_dir]._color == self._color: possible_moves.append(new_pos)
        
        # Casteling
        if self.can_castle_queenside and not self.castelling_square_under_attack_queenside and self.board.is_empty((1, ground_line)) and self.board.is_empty((2, ground_line)) and self.board.is_empty((3, ground_line)):
            new_pos = (x_pos-2, y_pos)
            possible_moves.append(new_pos)
        if self.can_castle_kingside and not self.castelling_square_under_attack_kingside and self.board.is_empty((5, ground_line)) and self.board.is_empty((6, ground_line)):
            new_pos = (x_pos+2, y_pos)
            possible_moves.append(new_pos)
        
        return possible_moves
    
    def move(self, end_position):
        x_pos, _ = self._position
        x_new, y_new = end_position
        ground_line = 0 if self._color == Color.WHITE else 7

        if self._move_is_legal(end_position):
            if not self.board.is_empty(end_position): 
                self.board.grid[y_new][x_new]._captured = True
            self.reset_en_passant_vulnerabiity()
            self._position = end_position
            self._has_moved = True
            self.board.manage_castelling_squares_under_attack()

            # Manage Castelling
            self.can_castle_kingside = False
            self.can_castle_queenside = False

            # Castelling Rooks
            if x_new-x_pos == -2: 
                self.board.grid[ground_line][0]._has_moved = True
                self.board.grid[ground_line][0]._position = (3, ground_line)
            if x_new-x_pos == 2:
                self.board.grid[ground_line][7]._has_moved = True 
                self.board.grid[ground_line][7]._position = (5, ground_line)
