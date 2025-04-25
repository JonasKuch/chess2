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


    def gameloop(self):
        self.window.draw()
        self.board_renderer.draw()
        self.pieces_renderer.draw()
        for event in pygame.event.get():
            self.event_handler.quit_game(event)
            self.event_handler.handle(event, Color.WHITE)
        self.board.update_grid()
        self.window.update()
        self.clock.tick(5000)


if __name__ == "__main__":
    board = Board()
    board.initialize()
    game = GameLoop(700, 800, board)
    while True:
        game.gameloop()
