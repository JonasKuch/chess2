from chess2.board import Board
from chess2.pieces import Pawn, Queen, Bishop, Rook, Knight
from chess2 import Color
import numpy as np
import copy
from stockfish import Stockfish
stockfish = Stockfish(path="/opt/homebrew/bin/stockfish", depth=5)



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
    
    
    def stockfish_move(self, side, in_board):
        board = in_board.clone()
        coord_dict = {
            'a':0,
            'b':1,
            'c':2,
            'd':3,
            'e':4,
            'f':5,
            'g':6,
            'h':7
                      }

        fen = board.to_fen()
        stockfish.set_fen_position(fen)
        raw_move = stockfish.get_best_move()
        start_raw = raw_move[:2]
        end_raw = raw_move[2:4]
        start_x, start_y = coord_dict[start_raw[0]], int(start_raw[1])-1
        move = coord_dict[end_raw[0]], int(end_raw[1])-1
        piece = board.grid[start_y][start_x]

        if isinstance(piece, Pawn) and move[1] in [0, 7]:
            possible_promotions = self.pawn_promotion(piece, board, move)
            evals = []
            for pos in possible_promotions:
                fen = stockfish.set_fen_position(fen)
                cp = stockfish.get_evaluation()
                evals.append(cp["value"])
            max_ind = np.argmax(evals)
            min_ind = np.argmin(evals)
            if side == Color.WHITE:
                return possible_promotions[max_ind]
            if side == Color.BLACK:
                return possible_promotions[min_ind]
        
        piece.move(move)
        board.update_grid()
        board.update_checks()
        return board


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