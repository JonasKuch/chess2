from collections import defaultdict


class Move():
    def __init__(self):
        self.move_num = -1
        self.max_move = -1
        self.move_cache = {}
        self.repetition_counter = defaultdict(int)


    def cache_board_state(self, board):
        self.move_num += 1
        self.max_move += 1
        cached_board = board.clone()
        self.move_cache[self.move_num] = cached_board

        state_key = board.get_repetition_key()  # You define this method in your board class
        self.repetition_counter[state_key] += 1

        if self.move_num < self.max_move:
            self.empty_cache(self.move_num+1)


    def load_board_state(self, move:int):
        if move > self.max_move:
            return None
        return self.move_cache[move]
    

    def empty_cache(self, move):
        for entry in range(move, self.max_move):
            board = self.move_cache[entry]
            state_key = board.get_repetition_key()
            self.repetition_counter[state_key] -= 1
            if self.repetition_counter[state_key] == 0:
                del self.repetition_counter[state_key]
            del self.move_cache[entry]
        self.max_move = self.move_num