class Move():
    def __init__(self):
        self.move_number = 0
        self.move_cache = {}


    def cache_board_state(self, board):
        cached_board = board.clone()
        self.move_number += 1
        self.move_cache[self.move_number] = cached_board