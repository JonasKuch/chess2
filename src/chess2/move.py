class Move():
    def __init__(self):
        self.move_number = 0
        self.move_cache = {}


    def cache_board_state(self, board):
        cached_board = board.clone()
        self.move_cache[self.move_number] = cached_board
        self.move_number += 1

    def load_board_state(self, move:int):
        if move > len(self.move_cache):
            return None
        return self.move_cache[move]