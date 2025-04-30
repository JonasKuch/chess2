from chess2.board import Board
from chess2 import Color
import numpy as np



class MoveGenerator():
    def get_all_possible_next_boards(self, side, board): # side = self.board.turn
        next_boards = []

        for i, piece in enumerate(board.pieces_on_board):
            if piece._color != side or piece._captured:
                continue
            
            legal_moves = piece.get_legal_moves()
            for move in legal_moves:
                cloned_board = board.clone()
                cloned_board.update_grid()
                cloned_board.pieces_on_board[i].move(move)
                cloned_board.update_grid()
                cloned_board.update_checks()
                next_boards.append(cloned_board)

        return next_boards
    

    def make_random_move(self, side, board):
        possible_moves = self.get_all_possible_next_boards(side, board)
        # for b in possible_moves:
        #     b.print(Color.BLACK)
        next_board = np.random.choice(possible_moves)
        return next_board


if __name__ == "__main__":
    board = Board()
    board.initialize()
    mg = MoveGenerator()
    next_boards = mg.get_all_possible_next_boards(board.turn, board)
    for b in next_boards:
        b.print(board.turn)
    mg.make_random_move(board.turn, board).print(board.turn)