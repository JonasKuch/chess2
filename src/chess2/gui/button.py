import pygame

class Button():
    def __init__(self, window, position:tuple, size:tuple, color, symbol):
        self.window = window
        self.position = position
        self.size = size
        self.color = color
        self.symbol = symbol


    def draw_button(self):
        x, y = self.position
        width, height = self.size
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect()