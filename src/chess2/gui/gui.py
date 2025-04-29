'''
this module handles drawing the gui right after every event
'''


from chess2.gui import Window
from chess2.gui import BoardRenderer
from chess2.gui import PiecesRenderer
from chess2.gui import EventHandler
from chess2.gui import Button
from chess2 import Color, Action
from chess2.board import Board
from chess2.pieces import *
import pygame

class GameLoop():
    def __init__(self, width, height, board, on_undo, on_redo, on_give_up):
        self.window = Window(width, height)
        self.square_width = 0.8*self.window.width / 8   ###################
        self.board_renderer = BoardRenderer(self.window)
        self.pieces_renderer = PiecesRenderer(self.window, board)
        self.button_size = int(0.8*self.square_width)        ###################
        self.button_color = "burlywood3"                ###################
        self.offset_x = (self.window.width - self.square_width*8)/2
        self.offset_y = (self.window.height - self.square_width*8)/2
        self.buttons_game = [
            Button((self.square_width / 2 + self.offset_x, self.square_width * 8.25 + self.offset_y), self.button_size, self.button_size, self.button_color, "<", "black", self.button_size, on_undo),
            Button((self.square_width * 1.5 + self.offset_x, self.square_width * 8.25 + self.offset_y), self.button_size, self.button_size, self.button_color, ">", "black", self.button_size, on_redo),
            Button((self.square_width * 6 + self.offset_x, self.square_width * 8.25 + self.offset_y), 2*self.button_size, self.button_size, self.button_color, "GIVE UP", "black", int(self.button_size*0.5), on_give_up)
        ]
        self.promotion_buttons = []
        self.event_handler = EventHandler(self.window, board)
        self.clock = pygame.time.Clock()
        self.board = board
        self.action = None
        self.promotion_loop = False


    def draw_buttons_game(self):
        for button in self.buttons_game:
            button.draw(self.window.screen)
    

    def draw_all_game(self, side):
        self.window.draw()
        self.board_renderer.draw()
        self.pieces_renderer.draw(side)
        self.draw_buttons_game()


    def draw_promotion(self, turn, side, pawn_position):
        # clear any old buttons
        self.promotion_buttons = []

        # draw dimmed background + board
        self.draw_all_game(side)
        self.draw_background()

        # pick the four pieces
        if turn == Color.WHITE:
            pieces_list = ["wB", "wN", "wR", "wQ"]
        else:
            pieces_list = ["bB", "bN", "bR", "bQ"]

        # load and scale images
        img_list = [
            pygame.transform.scale(
                pygame.image.load(f"src/chess2/gui/pieces_img/{piece}.png"),
                (self.square_width, self.square_width)
            )
            for piece in pieces_list
        ]

        # draw a 2×2 panel centered on the board
        left = 3*self.square_width + self.offset_x
        top  = 3*self.square_width + self.offset_y
        panel = pygame.Rect(left, top, 2*self.square_width, 2*self.square_width)
        pygame.draw.rect(self.window.screen, "darkolivegreen3", panel)

        # place each of the 4 options
        for idx, piece_code in enumerate(pieces_list):
            x = idx % 2
            y = idx // 2
            pos = (left + x*self.square_width, top + y*self.square_width)

            # draw square background
            color = ["darkolivegreen2","darkolivegreen4"][(x+y)%2]
            pygame.draw.rect(
                self.window.screen,
                color,
                pygame.Rect(pos, (self.square_width, self.square_width))
            )

            # blit the piece image
            self.window.screen.blit(img_list[idx], pos)

            # create button callback
            btn = Button(
                position=pos,
                width = self.square_width,
                height= self.square_width,
                color = color,
                text = "",
                text_color="black",
                text_size=int(self.square_width/2),
                callback=self.on_promotion(piece_code, pawn_position, side)
            )
            self.promotion_buttons.append(btn)

        self.window.update()


    def on_promotion(self, piece_code, pawn_position, side):
        # build the new piece instance
        def callback():
            # map the second character of piece_code to the right class+color
            mapping = {
                'B': Bishop,
                'N': Knight,
                'R': Rook,
                'Q': Queen,
            }
            color = Color.WHITE if piece_code[0] == 'w' else Color.BLACK
            cls   = mapping[piece_code[1]]
            new_piece = cls(color, pawn_position, self.board)

            # add promoted piece
            self.board.pieces_on_board.append(new_piece)
            self.board.update_grid()
            self.board.update_checks()
            self.draw_all_game(side)
            self.window.update()
            self.promotion_loop = False

        return callback

    
    def draw_background(self):
        alpha = 150  # 75% transparent
        background_surf  = pygame.Surface((self.window.width, self.window.height), pygame.SRCALPHA)
        background_color = (0, 0, 0, alpha)
        rect = pygame.Rect(0, 0, self.window.width, self.window.height)
        pygame.draw.rect(background_surf, background_color, rect)
        self.window.screen.blit(background_surf, (0, 0))

    
    def update_window(self):
        self.window.update()


    def gameloop(self, turn, side, show_legal_moves = True):

        self.draw_all_game(side)

        event = pygame.event.wait()
        self.action = self.event_handler.handle(event, turn, side, self.buttons_game)

        selected_piece = self.event_handler.selected_piece
        if selected_piece and show_legal_moves:
            self.pieces_renderer.draw_legal_moves(selected_piece, side)

        if self.action == Action.PROMOTE:
            self.promotion_loop = True
            while self.promotion_loop:
                self.draw_promotion(turn, side, self.event_handler.pawn_position)
                event = pygame.event.wait()
                self.event_handler.quit_game(event)
                for button in self.promotion_buttons:
                    button.handle_event(event)
                self.tick(60)
            return self.action

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
