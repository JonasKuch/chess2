import pygame


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