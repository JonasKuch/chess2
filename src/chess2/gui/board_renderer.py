import pygame


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