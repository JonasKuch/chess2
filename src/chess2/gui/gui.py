import pygame
from chess2.board import Board
from chess2 import Color



class Window():
    def __init__(self, width, height, title = "Chess Game"):
        pygame.init()
        pygame.display.set_caption(title)
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))

    
    def draw(self, color="darkolivegreen3"):
        self.screen.fill(color)


    def update(self):
        pygame.display.flip()



class BoardRenderer():
    def __init__(self, window, colors:list=["darkolivegreen2", "darkolivegreen4"]):
        self.surface = window.screen
        self.colors = colors
        self.square_width = 0.8*window.width / 8

    def draw(self):
        for x in range(1, 9):
            for y in range(1, 9):
                rect = pygame.Rect(x*self.square_width, y*self.square_width, self.square_width, self.square_width)
                color = self.colors[(x+y)%2]
                pygame.draw.rect(self.surface, color, rect)



class PiecesRenderer():
    def __init__(self, window, board:Board, pieces_dir = "src/chess2/gui/pieces_img"):
        self.square_width = 0.8*window.width / 8
        self.surface = window.screen
        self.board = board
        self.pieces_dir = pieces_dir
    

    def draw(self, side = Color.WHITE):
        for piece in self.board.pieces_on_board:
            x, y = piece._position
            color_prefix = "w" if piece._color == Color.WHITE else "b"
            img_path = f"{self.pieces_dir}/{color_prefix}{piece.str}.png"
            img = pygame.transform.scale(pygame.image.load(img_path), (self.square_width, self.square_width))
            pos = ( (x+1)*self.square_width, (y+1)*self.square_width ) if side == Color.WHITE else ( (8-x)*self.square_width, (8-x)*self.square_width )
            self.surface.blit(img, pos)



        


class GameLoop():
    def __init__(self, width, height, board):
        self.window = Window(width, height)
        self.board_renderer = BoardRenderer(self.window)
        self.pieces_renderer = PiecesRenderer(self.window, board)
        self.clock = pygame.time.Clock()
    def gameloop(self):
        while True:
            self.window.draw()
            self.board_renderer.draw()
            self.pieces_renderer.draw()
            self.window.update()
            self.clock.tick()


if __name__ == "__main__":
    board = Board()
    board.initialize()
    game = GameLoop(700, 800, board)
    game.gameloop()
