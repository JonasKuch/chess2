from chess2 import Color, PieceType
import copy



class Piece():
    def __init__(self, color, position, board):
        self._color = color
        self._position = position
        self._has_moved = False
        self._captured = False
        self.board = board
    

    def get_pseudo_legal_moves(self):
        pass
    
    
    def clone(self, new_board):
        new_piece = self.__class__(None, None, None)
        for attr, value in self.__dict__.items():
            if attr == "board": 
                setattr(new_piece, "board", new_board)
                continue
            setattr(new_piece, attr, copy.deepcopy(value))
        return new_piece

    
    def move(self, end_position):
        if self._move_is_legal(end_position):
            if not self.board.is_empty(end_position): 
                x, y = end_position
                self.board.grid[y][x]._captured = True
                self.board.halfmove_clock = 0
            self._position = end_position
            self._has_moved = True
            self.reset_en_passant_vulnerabiity()
            self.board.manage_castelling_squares_under_attack()
            if self._color == Color.BLACK:
                self.board.fullmove_clock += 1


    def get_legal_moves(self):
        legal_moves = []
        for move in self.get_pseudo_legal_moves():
            x_old, y_old = self._position
            simulated_board = self.board.clone()
            simulated_board.grid[y_old][x_old]._position = move
            if not simulated_board.is_empty(move): 
                x, y = move
                simulated_board.grid[y][x]._captured = True
            simulated_board.update_grid()

            if not simulated_board.is_under_attack(self._color):
                legal_moves.append(move)
        return legal_moves
    

    def _move_is_legal(self, end_position):
        return end_position in self.get_legal_moves()
    

    def reset_en_passant_vulnerabiity(self):
        for piece in self.board.pieces_on_board:
            if piece.type == PieceType.PAWN and piece._color == self._color and self._captured == False:
                piece._en_passant_vulnerability = False
