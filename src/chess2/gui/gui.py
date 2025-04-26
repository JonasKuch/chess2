'''
this module handles drawing the gui right after every event
'''


from chess2.gui import Window
from chess2.gui import BoardRenderer
from chess2.gui import PiecesRenderer
from chess2.gui import EventHandler
from chess2 import Color, Action
from chess2.board import Board
import pygame

class GameLoop():
    def __init__(self, width, height, board):
        self.window = Window(width, height)
        self.board_renderer = BoardRenderer(self.window)
        self.pieces_renderer = PiecesRenderer(self.window, board)
        self.event_handler = EventHandler(self.window, board)
        self.clock = pygame.time.Clock()
        self.board = board
        self.action = None


    def draw_all_game(self, side):
        self.window.draw()
        self.board_renderer.draw()
        self.pieces_renderer.draw(side)

    
    def update_window(self):
        self.window.update()


    def gameloop(self, turn, side, show_legal_moves = True):

        self.draw_all_game(side)

        event = pygame.event.wait()
        self.action = self.event_handler.handle(event, turn, side)

        selected_piece = self.event_handler.selected_piece
        if selected_piece and show_legal_moves:
            self.pieces_renderer.draw_legal_moves(selected_piece, side)

        if self.action == Action.MOVED:
            self.board.update_grid()
            self.board.update_checks()
            self.draw_all_game(side)
            self.update_window()
            return self.action
        
        self.update_window()
        return None
    

    def tick(self, framerate):
        self.clock.tick(framerate)
