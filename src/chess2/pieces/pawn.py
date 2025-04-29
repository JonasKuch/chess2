from chess2.pieces import Piece
from chess2 import Color, PieceType



class Pawn(Piece):
    def __init__(self, color, position, board):
        super().__init__(color, position, board)
        self._en_passant_vulnerability = False
        self.str = 'P' if self._color == Color.WHITE else 'p'
        self.type = PieceType.PAWN
        self.value = 1


    def get_pseudo_legal_moves(self):
        possible_moves = []

        direction = 1 if self._color == Color.WHITE else -1
        start_row = 1 if self._color == Color.WHITE else 6
        x, y = self._position

        # One step ahead
        if self.board.in_bounds((x, y+direction)):
            if self.board.is_empty((x, y+direction)):
                possible_moves.append((x, y+direction))
        
        # Two steps ahead
        if y == start_row and self.board.is_empty((x, y+direction)) and self.board.is_empty((x, y+2*direction)):
            possible_moves.append((x, y+2*direction))
        
        # Take piece
        if self.board.in_bounds((x+1, y+direction)):
            if not self.board.is_empty((x+1, y+direction)) and not self.board.grid[y+direction][x+1]._color == self._color:
                possible_moves.append((x+1, y+direction))
        if self.board.in_bounds((x-1, y+direction)):
            if not self.board.is_empty((x-1, y+direction)) and not self.board.grid[y+direction][x-1]._color == self._color:
                possible_moves.append((x-1, y+direction))
        
        # En passant
        if self.board.in_bounds((x+1, y+direction)):
            if self.board.is_empty((x+1, y+direction)) and not self.board.is_empty((x+1, y)):
                if self.board.grid[y][x+1].type == PieceType.PAWN and not (self.board.grid[y][x+1]._color == self._color):
                    if self.board.grid[y][x+1]._en_passant_vulnerability:
                        possible_moves.append((x+1, y+direction))
        if self.board.in_bounds((x-1, y+direction)):
            if self.board.is_empty((x-1, y+direction)) and not self.board.is_empty((x-1, y)):
                if self.board.grid[y][x-1].type == PieceType.PAWN and not (self.board.grid[y][x-1]._color == self._color):
                    if self.board.grid[y][x-1]._en_passant_vulnerability:
                        possible_moves.append((x-1, y+direction))

        return possible_moves
    
    
    def move(self, end_position):
        if self._move_is_legal(end_position):
            x_old, y_old = self._position
            x_new, y_new = end_position
            direction = 1 if self._color == Color.WHITE else -1
            # Take piece
            if not self.board.is_empty(end_position): self.board.grid[y_new][x_new]._captured = True
            # Take via en passant
            if self.board.is_empty(end_position) and not (x_new - x_old) == 0: self.board.grid[y_new-direction][x_new]._captured = True
            # Adjust properties
            self.reset_en_passant_vulnerabiity()
            self._en_passant_vulnerability = True if (y_new-y_old) == 2*direction else False
            self._position = end_position
            self._has_moved = True
            self.board.manage_castelling_squares_under_attack()
            self.board.halfmove_clock = 0
            if self._color == Color.BLACK:
                self.board.fullmove_clock += 1
