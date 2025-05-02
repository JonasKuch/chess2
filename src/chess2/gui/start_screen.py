from chess2.gui import Window, BoardRenderer, PiecesRenderer, Button, EventHandler
from chess2 import Color, Action
from chess2.board import Board
import pygame



class StartScreen():
    def __init__(self, window:Window):
        self.window = window
        self.surface = window.screen

        self.board = Board()
        self.board.initialize()

        self.event_handler = EventHandler(self.window, self.board)
        self.board_renderer = BoardRenderer(self.window, self.board, self.event_handler)
        self.pieces_renderer = PiecesRenderer(self.window, self.board)
        
        self.running = True

        self.start_window_width = self.window.width*0.7
        self.start_window_height = self.window.height*0.8
        self.start_window_color = "darkolivegreen3"
        self.start_window_left = (self.window.width-self.start_window_width)/2
        self.start_window_top = (self.window.height-self.start_window_height)/2

        self.button_width = self.window.width/1.5
        self.button_height = 0.8*self.window.width/8
        self.button_color = "burlywood3"
        self.play_bot = True
        self.chosen_color = Color.WHITE
        self.show_moves = True
        self.flip_board = False
        self.with_takeback = True
        self.buttons = [
            Button(position=(0, 0), width=self.button_width, height=self.button_height, color=self.button_color, text=f"", text_color="black", text_size=int(self.button_height/2), callback=self.on_play_bot),
            Button(position=(0, 0), width=self.button_width, height=self.button_height, color=self.button_color, text=f"", text_color="black", text_size=int(self.button_height/2), callback=self.on_chose_side),
            Button(position=(0, 0), width=self.button_width, height=self.button_height, color=self.button_color, text=f"", text_color="black", text_size=int(self.button_height/2), callback=self.on_flip_board),
            Button(position=(0, 0), width=self.button_width, height=self.button_height, color=self.button_color, text=f"", text_color="black", text_size=int(self.button_height/2), callback=self.on_show_moves),
            Button(position=(0, 0), width=self.button_width, height=self.button_height, color=self.button_color, text=f"", text_color="black", text_size=int(self.button_height/2), callback=self.on_takebacks),
            Button(position=(0, 0), width=self.button_width, height=self.button_height, color="chartreuse4", text=f"START", text_color="black", text_size=int(self.button_height/2), callback=self.on_start),
        ]
    

    def draw_background(self):
        alpha = 150  # 75% transparent

        background_surf  = pygame.Surface((self.window.width, self.window.height), pygame.SRCALPHA)
        background_color = (0, 0, 0, alpha)
        rect = pygame.Rect(0, 0, self.window.width, self.window.height)
        pygame.draw.rect(background_surf, background_color, rect)
        self.surface.blit(background_surf, (0, 0))
    

    def draw_buttons(self):
        space = (self.start_window_height - 6*self.button_height)/7
        top = self.start_window_top + space
        left = self.start_window_left + (self.start_window_width - self.button_width)/2
        for i, button in enumerate(self.buttons):
            button.set_position((left, top + (self.button_height+space)*i))
            self.update_buttons_text()
            button.draw(self.surface)
    

    def update_buttons_text(self):
        self.buttons[0].set_text(f"PLAY BOT: {'ON' if self.play_bot else 'OFF'}")
        self.buttons[1].set_text(f"SIDE: {self.chosen_color.name}")
        self.buttons[2].set_text(f"FLIP BOARD: {'ON' if self.flip_board else 'OFF'}")
        self.buttons[3].set_text(f"SHOW MOVES: {'ON' if self.show_moves else 'OFF'}")
        self.buttons[4].set_text(f"TAKEBACKS: {'ON' if self.with_takeback else 'OFF'}")
        self.buttons[5].set_text(f"START")


    def on_play_bot(self):
        self.play_bot = not self.play_bot
        if self.play_bot:
            self.flip_board = False


    def on_chose_side(self):
        self.chosen_color = Color.BLACK if self.chosen_color == Color.WHITE else Color.WHITE


    def on_flip_board(self):
        if not self.play_bot:
            self.flip_board = not self.flip_board

    
    def on_show_moves(self):
        self.show_moves = not self.show_moves


    def on_takebacks(self):
        self.with_takeback = not self.with_takeback

    
    def on_start(self):
        self.running = False


    def draw_start_window(self):
        rect = pygame.Rect(self.start_window_left, self.start_window_top, self.start_window_width, self.start_window_height)
        pygame.draw.rect(self.surface, self.start_window_color, rect)
    

    def start_screen_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            event = pygame.event.wait()
            self.event_handler.quit_game(event)
            for button in self.buttons:
                button.handle_event(event)

            self.window.draw()
            self.board_renderer.draw(Color.WHITE)
            self.pieces_renderer.draw(Color.WHITE)
            self.draw_background()
            self.draw_start_window()
            self.draw_buttons()

            self.window.update()
            clock.tick(60)
