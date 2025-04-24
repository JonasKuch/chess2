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
        for x in range(8):
            for y in range(8):
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
            pos = ( x*self.square_width, (7-y)*self.square_width ) if side == Color.WHITE else ( (7-x)*self.square_width, y*self.square_width ) 
            if not piece._captured: self.surface.blit(img, pos)




class EventHandler():
    def __init__(self, window:Window, board:Board):
        self.selected_pos = None
        self.valid_moves = None
        self.square_width = 0.8*window.width / 8
        self.board = board
    

    def quit_game(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
    

    def _reset_attributes(self):
        self.selected_pos = None
        self.valid_moves = None


    def _convert_mouse_position(self, position):
        x, y = position
        x_board = int(x / self.square_width)
        y_board = 7 - int(y / self.square_width)

        if not self.board.in_bounds((x_board, y_board)):
            return None
        
        return x_board, y_board
        

    def handle(self, event, turn_color):
        # 1) Only handle clicks
        if event.type != pygame.MOUSEBUTTONDOWN:
            return "ignored"
        
        # 2) Convert mouse → board coords (and reset if off-board)
        board_pos = self._convert_mouse_position(event.pos)
        if board_pos is None:
            self._reset_attributes()
            return "ignored"
        
        x_board, y_board = board_pos
        selected_square = self.board.grid[y_board][x_board]

        # 3) No piece selected yet → try to select
        if self.selected_pos is None:
            if selected_square is None or selected_square._color != turn_color:
                return "ignored"
            self.selected_pos = x_board, y_board
            self.valid_moves = selected_square.get_legal_moves()
            return "selected"
        
        # 4) A piece is already selected → attempt move
        x_selected, y_selected = self.selected_pos
        if (x_board, y_board) in self.valid_moves:
            self.board.grid[y_selected][x_selected].move((x_board, y_board))
            self._reset_attributes()
            return "moved"
        
        # 5) Click wasn’t a legal move → maybe re-select another of yours
        if selected_square and selected_square._color == turn_color:
            self.selected_pos = x_board, y_board
            self.valid_moves = selected_square.get_legal_moves()
            return "selected"
        
        # 6) Otherwise, clear selection
        self._reset_attributes()
        return "ignored"



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
