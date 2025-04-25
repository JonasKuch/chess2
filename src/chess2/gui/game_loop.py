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


    def gameloop(self, turn, side, show_legal_moves = True):
        self.window.draw()
        self.board_renderer.draw()
        self.pieces_renderer.draw(side)
        event = pygame.event.wait() # Pauses Loop until event; mouse movement also counts
        self.event_handler.quit_game(event)
        self.action = self.event_handler.handle(event, turn, side)
        selected_piece = self.event_handler.selected_piece
        if selected_piece:
            self.pieces_renderer.draw_legal_moves(selected_piece, side)
        self.board.update_grid()
        self.window.update()
        if self.action == Action.MOVED:
            return self.action
        return None
    

    def tick(self, framerate):
        self.clock.tick(framerate)


if __name__ == "__main__":
    board = Board()
    board.initialize()
    game_loop = GameLoop(700, 800, board)
    while True:
        action = game_loop.gameloop(Color.BLACK, Color.BLACK)
        if action == Action.MOVED:
            pass # here turn
        game_loop.tick(60)
