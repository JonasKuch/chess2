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
        offset = self.square_width/2
        radius = self.square_width * 0.2
        alpha = 100  # 75% transparent

        # color.a = 128
        legal_moves = piece.get_legal_moves()
        for move in legal_moves:
            x, y = move
            pos = ( x*self.square_width+offset, (7-y)*self.square_width+offset) if side == Color.WHITE else ( (7-x)*self.square_width+offset, y*self.square_width+offset ) 

            # Create a temporary surface for the transparent circle
            circle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            circle_color = (205, 0, 0, alpha)  # RGBA

            # Draw the transparent circle onto the temporary surface
            pygame.draw.circle(circle_surf, circle_color, (radius, radius), radius)

            # Blit it to the main surface
            self.surface.blit(circle_surf, (pos[0] - radius, pos[1] - radius))


