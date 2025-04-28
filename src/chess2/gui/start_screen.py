from chess2.gui import Window, BoardRenderer, PiecesRenderer, Button, EventHandler
from chess2 import Color
from chess2.board import Board
import pygame



class StartScreen():
    def __init__(self, window:Window):
        self.window = window
        self.surface = window.screen
        self.board_renderer = BoardRenderer(self.window)
        self.board = Board()
        self.board.initialize()
        self.pieces_renderer = PiecesRenderer(self.window, self.board)
        self.event_handler = EventHandler(self.window, self.board)

        self.start_window_width = self.window.width*0.7
        self.start_window_height = self.window.height*0.7
        self.start_window_color = "darkolivegreen3"
        self.start_window_left = self.window.width*0.15
        self.start_window_top = self.window.height*0.15

        self.button_color = "burlywood3"
        self.button_width = self.window.width/4
        self.button_height = 0.8*self.window.width/8
        self.play_bot = False
        self.chosen_color = Color.WHITE
        self.show_moves = True
        self.flip_board = True
        self.with_takeback = True
        self.buttons = [
            Button(position=..., width=self.button_width, height=self.button_height, color=self.button_color, text=f"PLAY BOT:    {"ON" if self.play_bot else "OFF"}", text_color="black", text_size=..., callback=...),
            Button(position=..., width=self.button_width, height=self.button_height, color=self.button_color, text=f"SIDE:    {"ON" if self.chosen_color.name else "OFF"}", text_color="black", text_size=..., callback=...),
            Button(position=..., width=self.button_width, height=self.button_height, color=self.button_color, text=f"FLIP BOARD:    {"ON" if self.flip_board else "OFF"}", text_color="black", text_size=..., callback=...),
            Button(position=..., width=self.button_width, height=self.button_height, color=self.button_color, text=f"SHOW MOVES:    {"ON" if self.show_moves else "OFF"}", text_color="black", text_size=..., callback=...),
            Button(position=..., width=self.button_width, height=self.button_height, color=self.button_color, text=f"TAKEBACKS:    {"ON" if self.with_takeback else "OFF"}", text_color="black", text_size=..., callback=...),
            Button(position=..., width=self.button_width, height=self.button_height, color=self.button_color, text=f"START", text_color="black", text_size=..., callback=...),
        ]
    

    def draw_background(self):
        alpha = 150  # 75% transparent

        backgrond_surf  = pygame.Surface((self.window.width, self.window.height), pygame.SRCALPHA)
        background_color = (0, 0, 0, alpha)
        rect = pygame.Rect(0, 0, self.window.width, self.window.height)
        pygame.draw.rect(backgrond_surf, background_color, rect)
        self.surface.blit(backgrond_surf, (0, 0))
    

    # def draw_buttons(self):
    #     for button in self.buttons:
    #         button.draw()


    def draw_start_window(self):
        rect = pygame.Rect(self.start_window_left, self.start_window_top, self.start_window_width, self.start_window_height)
        pygame.draw.rect(self.surface, self.start_window_color, rect)
    

    def start_screen_loop(self):
        clock = pygame.time.Clock()
        while True:
            event = pygame.event.wait()
            self.event_handler.quit_game(event)

            self.window.draw()
            self.board_renderer.draw()
            self.pieces_renderer.draw(Color.WHITE)
            self.draw_background()
            self.draw_start_window()

            self.window.update()
            clock.tick(60)
