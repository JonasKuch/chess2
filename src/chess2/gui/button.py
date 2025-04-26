import pygame

class Button():
    def __init__(self, position:tuple, width, height, color, text, text_color, text_size, callback):
        self.x, self.y = position
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color = color
        self.text = text
        self.text_color = text_color
        self.font = pygame.font.Font("src/chess2/gui/fonts/Roboto-Regular.ttf", text_size)
        self.callback = callback

        self._rendered_text = self.font.render(text, True, self.text_color)
        self._text_rect = self._rendered_text.get_rect(center=self.rect.center)


    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())


    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius = int(0.1*self.width))
        surface.blit(self._rendered_text, self._text_rect)


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()