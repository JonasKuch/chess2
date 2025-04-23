import copy
from chess2 import Color
from chess2.pieces import *



class Board():
    def __init__(self):
        self.grid = [
        [None for _ in range(8)] for _ in range(8)
        ]
        self.black_king = None
        self.white_king = None
        self.pieces_on_board = []
    
    
    def setup_pieces(self, color):
        
        row_pawns = 1 if color == Color.WHITE else 6
        row_others = 0 if color == Color.WHITE else 7

        for col in range (8):
            self.pieces_on_board.append(Pawn(color, position=(col, row_pawns),board=self))
            
        
        self.pieces_on_board.append(Rook(color, position=(0, row_others),board=self))
        self.pieces_on_board.append(Rook(color, position=(7, row_others),board=self))
        self.pieces_on_board.append(Knight(color, position=(1, row_others),board=self))
        self.pieces_on_board.append(Knight(color, position=(6, row_others),board=self))
        self.pieces_on_board.append(Bishop(color, position=(2, row_others),board=self))
        self.pieces_on_board.append(Bishop(color, position=(5, row_others),board=self))
        self.pieces_on_board.append(Queen(color, position=(3, row_others),board=self))

        king = King(color, position=(4, row_others),board=self)
        self.pieces_on_board.append(king)
        if color == Color.WHITE: 
            self.white_king = king
        else:
            self.black_king = king

            

    def reset_grid(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]

    
    def update_grid(self):
        self.reset_grid()
        for piece in self.pieces_on_board:
            if not piece._captured:
                x, y = piece._position
                self.grid[y][x] = piece


    def initialize(self):
        self.setup_pieces(Color.WHITE)
        self.setup_pieces(Color.BLACK)
        self.update_grid()
    
        
    def is_empty(self, square_coords):
        x, y = square_coords
        square = self.grid[y][x]
        return square == None
    

    def in_bounds(self, square_coords):
        x, y = square_coords
        return (0 <= x <= 7 and 0 <= y <= 7)
    

    def clone(self):
        return copy.deepcopy(self)
    

    def get_squares_under_attack(self, color):
        squares_under_attack = []
        for piece in self.pieces_on_board:
            if not piece._color == color and not piece._captured:
                for square in piece.get_pseudo_legal_moves():
                    squares_under_attack.append(square)
        return squares_under_attack
        
    
    def is_under_attack(self, color):
        squares_under_attack = self.get_squares_under_attack(color)
        king_pos = self.white_king._position if color == Color.WHITE else self.black_king._position
        return king_pos in squares_under_attack
    
    
    def print(self, side):
        print("\n")

        if side == Color.WHITE:
            for row_number in range(1, 9):
                row_list = []
                for square in self.grid[-row_number]:
                    if square == None:
                        row_list.append('_') 
                    else:
                        row_list.append(square.str)
                print(f"{9-row_number}   {row_list}")
            print(f"\n      a    b    c    d    e    f    g    h \n")
        
        if side == Color.BLACK:
            for row_number in range(8):
                row_list = []
                for square in self.grid[row_number]:
                    if square == None:
                        row_list.append('_') 
                    else:
                        row_list.append(square.str)
                print(f"{row_number+1}   {row_list}")
            print(f"\n      a    b    c    d    e    f    g    h \n")
                
    
    def get_possible_moves_of_all_pieces(self, color):
        squares_under_attack = []
        for piece in self.pieces_on_board:
            if piece._color == color and not piece._captured:
                for square in piece.get_legal_moves():
                    squares_under_attack.append(square)
        return squares_under_attack
    

    def update_checks(self):
        # must be called after 
        self.white_king.in_check = True if self.is_under_attack(Color.WHITE) else False
        self.black_king.in_check = True if self.is_under_attack(Color.BLACK) else False
    

    def check_if_mate(self, color):
        # must be called after update_checks and after update_grid
        has_moves = False
        in_check = self.white_king.in_check if color == Color.WHITE else self.black_king.in_check
        for piece in self.pieces_on_board:
            if not piece._captured and piece._color == color:
                if not piece.get_legal_moves() == []:
                    has_moves = True
                    break
        return in_check and not has_moves
    

    def manage_castelling_squares_under_attack(self):
        castelling_squares_white_kingside = [(4, 0), (5, 0), (6, 0)]
        castelling_squares_white_queenside = [(4, 0), (3, 0), (2, 0)]
        castelling_squares_black_kingside = [(4, 7), (5, 7), (6, 7)]
        castelling_squares_black_queenside = [(4, 7), (3, 7), (2, 7)]
        squares_under_attack_white = self.get_squares_under_attack(Color.WHITE)
        squares_under_attack_black = self.get_squares_under_attack(Color.BLACK)

        for square in castelling_squares_white_kingside:
            if square in squares_under_attack_white:
                self.white_king.castelling_square_under_attack_kingside = True
                break
            else:
                self.white_king.castelling_square_under_attack_kingside = False
        
        for square in castelling_squares_white_queenside:
            if square in squares_under_attack_white:
                self.white_king.castelling_square_under_attack_queenside = True
                break
            else:
                self.white_king.castelling_square_under_attack_queenside = False
        
        for square in castelling_squares_black_kingside:
            if square in squares_under_attack_black:
                self.black_king.castelling_square_under_attack_kingside = True
                break
            else:
                self.black_king.castelling_square_under_attack_kingside = False
        
        for square in castelling_squares_black_queenside:
            if square in squares_under_attack_black:
                self.black_king.castelling_square_under_attack_queenside = True
                break
            else:
                self.black_king.castelling_square_under_attack_queenside = False
