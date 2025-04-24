import pygame



class GUI:
    def __init__(self, board, width = 10, height = 10):
        self.board = board
        self.width = width
        self.height = height
        self.square_side = (self.width - 0.05 * self.width) / 8