from chess2.gui import Button, EventHandler, BoardRenderer, PiecesRenderer
from chess2.board import Board
from chess2 import Color
import pygame



class EndScreen():
    def __init__(self, window):
        self.window = window
        self.surface = window.screen
        self.board = None
        self.board_renderer = BoardRenderer(self.window)
        self.event_handler = EventHandler(self.window, self.board)
        self.end_window_width = self.window.width*0.7
        self.end_window_height = self.window.height*0.5
        self.end_window_color = "darkolivegreen3"
        self.end_window_left = (self.window.width-self.end_window_width)/2
        self.end_window_top = (self.window.height-self.end_window_height)/2
        self.running = True

        self.button_width = self.window.width/1.5
        self.button_height = 0.8*self.window.width/8
        self.button_color = "burlywood3"
        self.buttons = [
            Button(position=(self.end_window_left + (self.end_window_width - self.button_width)/2, self.end_window_top + self.end_window_height - 100), width=self.button_width, height=self.button_height, color = self.button_color, text="RESTART", text_color="black", text_size=int(self.button_height/2), callback=self.on_restart)
            ] 


    def draw_background(self):
        alpha = 150  # 75% transparent

        background_surf  = pygame.Surface((self.window.width, self.window.height), pygame.SRCALPHA)
        background_color = (0, 0, 0, alpha)
        rect = pygame.Rect(0, 0, self.window.width, self.window.height)
        pygame.draw.rect(background_surf, background_color, rect)
        self.surface.blit(background_surf, (0, 0))


    def draw_buttons(self):
        for button in self.buttons:
            button.draw(self.surface)


    def draw_end_window(self, winner):
        rect = pygame.Rect(self.end_window_left, self.end_window_top, self.end_window_width, self.end_window_height)
        pygame.draw.rect(self.surface, self.end_window_color, rect)

        # Draw the "CHECK MATE!" text
        font_size = int(self.button_height / 2)
        font = pygame.font.Font("src/chess2/gui/fonts/Roboto-Regular.ttf", font_size)
        text = font.render(f"CHECK MATE! {winner.name} WON!", True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.end_window_left + self.end_window_width/2, self.end_window_top + self.end_window_height/2 - 30))
        self.surface.blit(text, text_rect)

    
    def on_restart(self):
        self.running = False

    
    def end_screen_loop(self, winner, board):
        pieces_renderer = PiecesRenderer(self.window, board)
        clock = pygame.time.Clock()
        while self.running:
            event = pygame.event.wait()
            self.event_handler.quit_game(event)
            for button in self.buttons:
                button.handle_event(event)
            self.window.draw()
            self.board_renderer.draw()
            pieces_renderer.draw(winner)
            self.draw_background()
            self.draw_end_window(winner)
            self.draw_buttons()

            self.window.update()
            clock.tick(60)