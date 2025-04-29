from chess2.board import Board
from chess2 import Color
import numpy as np



class MoveGenerator():
    def __init__(self, board:Board):
        self.board = board
        

    def get_all_possible_next_boards(self, side): # side = self.board.turn
        next_boards = []
        enemie = Color.BLACK if side == Color.WHITE else Color.WHITE

        for i, piece in enumerate(self.board.pieces_on_board):
            if piece._color != side:
                continue

            legal_moves = piece.get_legal_moves()
            for move in legal_moves:
                cloned_board = self.board.clone()
                cloned_board.pieces_on_board[i].move(move)
                cloned_board.update_grid()
                cloned_board.update_checks()
                mate = self.board.check_if_mate(enemie)
                next_boards.append(cloned_board)

        return next_boards
    

    def make_random_move(self, side):
        possible_moves = self.get_all_possible_next_boards(side)
        next_board = np.random.choice(possible_moves)
        return next_board


if __name__ == "__main__":
    board = Board()
    board.initialize()
    mg = MoveGenerator(board)
    next_boards = mg.get_all_possible_next_boards(board.turn)
    for b in next_boards:
        b.print(board.turn)
    mg.make_random_move(board.turn).print(board.turn)