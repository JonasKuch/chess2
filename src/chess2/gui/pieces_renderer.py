from chess2.board import Board
from chess2 import Color
import pygame


class PiecesRenderer():
    def __init__(self, window, board:Board, pieces_dir = "src/chess2/gui/pieces_img"):
        self.square_width = 0.8*window.width / 8
        self.surface = window.screen
        self.board = board
        self.pieces_dir = pieces_dir
    

    def draw(self, side):
        for piece in self.board.pieces_on_board:
            x, y = piece._position
            color_prefix = "w" if piece._color == Color.WHITE else "b"
            img_path = f"{self.pieces_dir}/{color_prefix}{piece.str}.png"
            img = pygame.transform.scale(pygame.image.load(img_path), (self.square_width, self.square_width))
            pos = ( x*self.square_width, (7-y)*self.square_width ) if side == Color.WHITE else ( (7-x)*self.square_width, y*self.square_width ) 
            if not piece._captured: self.surface.blit(img, pos)
    

    def pawn_promotion(self, side):
        pass


    def draw_legal_moves(self, piece, side):
        img_path = f"{self.pieces_dir}/dot.png"
        img = pygame.transform.scale(pygame.image.load(img_path), (self.square_width, self.square_width))
        legal_moves = piece.get_legal_moves()
        for move in legal_moves:
            x, y = move
            pos = ( x*self.square_width, (7-y)*self.square_width ) if side == Color.WHITE else ( (7-x)*self.square_width, y*self.square_width ) 
            self.surface.blit(img, pos)
