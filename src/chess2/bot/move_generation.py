from chess2.board import Board
from chess2.pieces import Pawn, Queen, Bishop, Rook, Knight
from chess2 import Color
import numpy as np
import copy



class MoveGenerator():
    def pawn_promotion(self, piece, board, move):
        n_boards = []
        piece._captured = True
        new_pieces = [Queen(copy.deepcopy(piece._color), move, None), 
                      Rook(copy.deepcopy(piece._color), move, None),
                      Bishop(copy.deepcopy(piece._color), move, None),
                      Knight(copy.deepcopy(piece._color), move, None),
                      ]
        for p in new_pieces:
            c_board = board.clone()
            p.board = c_board
            p._has_moved = True
            c_board.pieces_on_board.append(p)
            c_board.update_grid()
            c_board.update_checks()
            n_boards.append(c_board)
        return n_boards


    def get_all_possible_next_boards(self, side, board): # side = self.board.turn
        next_boards = []

        for i, piece in enumerate(board.pieces_on_board):
            if piece._color != side or piece._captured:
                continue
            
            legal_moves = piece.get_legal_moves()
            for move in legal_moves:
                cloned_board = board.clone()
                piece_to_move = cloned_board.pieces_on_board[i]
                piece_to_move.move(move)

                if isinstance(piece_to_move, Pawn) and move[1] in [0, 7]:
                    cloned_boards = self.pawn_promotion(piece_to_move, cloned_board, move)
                    for b in cloned_boards:
                        next_boards.append(b)
                    continue

                cloned_board.update_grid()
                cloned_board.update_checks()
                next_boards.append(cloned_board)

        return next_boards
    

    def make_random_move(self, side, board):
        possible_moves = self.get_all_possible_next_boards(side, board)
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