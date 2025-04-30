import pygame
from chess2 import Color

class BoardRenderer():
    def __init__(self, window, board, event_handler, colors:list=["darkolivegreen2", "darkolivegreen4"]): # überall wo boardrenderer importiert wurde müssen die neuen arguments noch gepasst werden
        self.surface = window.screen
        self.board = board
        self.event_handler = event_handler
        self.colors = colors
        self.square_width = 0.8*window.width / 8
        self.offset_x = (window.width - self.square_width*8)/2
        self.offset_y = (window.height - self.square_width*8)/2


    def draw_additional_square(self, side, piece, color, width):
        x, y = piece._position
        x_transformed, y_transformed = ( x*self.square_width+self.offset_x, (7-y)*self.square_width+self.offset_y) if side == Color.WHITE else ( (7-x)*self.square_width+self.offset_x, y*self.square_width+self.offset_y)
        rect = pygame.Rect(x_transformed, y_transformed, self.square_width, self.square_width)
        pygame.draw.rect(self.surface, color, rect, width)


    def draw(self, side):
        for x in range(8):
            for y in range(8):
                rect = pygame.Rect(x*self.square_width + self.offset_x, y*self.square_width + self.offset_y, self.square_width, self.square_width)
                color = self.colors[(x+y)%2]
                pygame.draw.rect(self.surface, color, rect)

        selected_piece = self.event_handler.selected_piece
        if selected_piece:
            self.draw_additional_square(side, selected_piece, "yellow2", 0)

        white_king = self.board.white_king
        black_king = self.board.black_king
        if white_king.in_check:
            self.draw_additional_square(side, white_king, "tomato2", 3)
        if black_king.in_check:
            self.draw_additional_square(side, black_king, "tomato2", 3)
        
