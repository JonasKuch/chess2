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
        self.turn = Color.WHITE
        self.pieces_on_board = []
        self.halfmove_clock = 0
        self.fullmove_clock = 1
    
    
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
        new_board = self.__class__()
        new_board.turn = copy.deepcopy(self.turn)
        new_board.halfmove_clock = copy.deepcopy(self.halfmove_clock)
        new_board.fullmove_clock = copy.deepcopy(self.fullmove_clock)
        for old_piece in self.pieces_on_board:
            new_piece = old_piece.clone(new_board)
            new_board.pieces_on_board.append(new_piece)
            if new_piece.str == "K": new_board.white_king = new_piece
            if new_piece.str == "k": new_board.black_king = new_piece
        new_board.update_grid()
        return new_board
    

    def load_state(self, other_board):
        self.__init__()
        self.turn = copy.deepcopy(other_board.turn)
        for other_piece in other_board.pieces_on_board:
            new_piece = other_piece.clone(self)
            self.pieces_on_board.append(new_piece)
            if new_piece.str == "K": self.white_king = new_piece
            if new_piece.str == "k": self.black_king = new_piece
        self.update_grid()
    

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
        # must be called after update_grid
        self.white_king.in_check = True if self.is_under_attack(Color.WHITE) else False
        self.black_king.in_check = True if self.is_under_attack(Color.BLACK) else False
    

    def check_if_mate(self, color=None):
        # must be called after update_checks and after update_grid
        if not color: color = self.turn

        has_moves = False
        in_check = self.white_king.in_check if color == Color.WHITE else self.black_king.in_check
        for piece in self.pieces_on_board:
            if not piece._captured and piece._color == self.turn:
                if not piece.get_legal_moves() == []:
                    has_moves = True
                    break
        return in_check and not has_moves
    

    def to_fen(self): # except the half move and full move thing so far
        fen_rows = []

        for y in range(7, -1, -1):
            empty_count = 0
            fen_row = ''
            for x in range(8):
                piece = self.grid[y][x]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece.str
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_rows.append(fen_row)

        piece_placement = '/'.join(fen_rows)
        active_color = 'w' if self.turn == Color.WHITE else 'b'

        # Castling rights
        castling = ''
        if not self.white_king.castelling_square_under_attack_kingside and self.white_king.can_castle_kingside:
            castling += 'K'
        if not self.white_king.castelling_square_under_attack_queenside and self.white_king.can_castle_queenside:
            castling += 'Q'
        if not self.black_king.castelling_square_under_attack_kingside and self.black_king.can_castle_kingside:
            castling += 'k'
        if not self.black_king.castelling_square_under_attack_queenside and self.black_king.can_castle_queenside:
            castling += 'q'
        if not castling:
            castling = '-'

        # En passant square
        en_passant = '-'
        for piece in self.pieces_on_board:
            if isinstance(piece, Pawn) and piece._en_passant_vulnerability and not piece._captured:
                x, y = piece._position
                # Determine the square behind the pawn (from the opponent's perspective)
                target_y = y - 1 if piece._color == Color.WHITE else y + 1
                if 0 <= target_y <= 7:
                    file = chr(ord('a') + x)
                    rank = str(target_y + 1)
                    en_passant = file + rank
                break  # Only one pawn can be vulnerable to en passant at a time


        fen = f"{piece_placement} {active_color} {castling} {en_passant} {self.halfmove_clock} {self.fullmove_clock}"
        return fen


    def get_repetition_key(self):
        fen = self.to_fen()
        key = ' '.join(fen.split(' ')[:4])
        return key


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
