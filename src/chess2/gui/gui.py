import pygame



class Window():
    def __init__(self, width, height):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode(self.width, self.height)

    
    def fill(self, color):
        self.screen.fill(color)


    def update(self):
        pygame.display.flip()



class DrawBoard():
    def __init__(self, surface, colors=("white", "black")):
        self.surface = surface
        self.color_white, self.color_black = colors
        self.tiles_width = 0.95*self.surface.width / 8

    def draw(self):
        self.surface.fill(self.color_white)
        for x in range(8):
            for y in range(8):
                rect = pygame.Rect()
                pygame.draw.rect(self.surface, self.color_black, rect)

