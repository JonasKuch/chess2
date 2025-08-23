from chess2.board import Board
from chess2.pieces import Pawn, Queen, Bishop, Rook, Knight
from chess2 import Color
import numpy as np
import copy
from stockfish import Stockfish
import torch
from chess2.bot import NeuralNetwork, TrainingSetProcessor
stockfish = Stockfish(path="/opt/homebrew/bin/stockfish", depth=20)



class MoveGenerator():
    def __init__(self, model_params_path):
        self.model = NeuralNetwork().to("cpu")
        self.model.load_state_dict(torch.load(model_params_path, weights_only=True))
        self.model.eval()
        self.processor = TrainingSetProcessor()


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
        # map files → 0–7
        file_to_i = {f:i for i,f in enumerate('abcdefgh')}

        # tell Stockfish the position
        fen = board.to_fen()
        stockfish.set_fen_position(fen)

        # get UCI best move, e.g. "e7e8q" or "e2e4"
        raw = stockfish.get_best_move()
        if raw is None:
            raise RuntimeError("Stockfish returned no move")

        # parse it
        from_sq, to_sq = raw[:2], raw[2:4]
        prom = raw[4] if len(raw) == 5 else None

        sx, sy = file_to_i[from_sq[0]], int(from_sq[1]) - 1
        ex, ey = file_to_i[to_sq[0]], int(to_sq[1]) - 1

        piece = board.grid[sy][sx]
        # call your move, passing promotion if any
        if prom:
            # if your Pawn.move API takes a promotion arg:
            piece._captured = True
            # Create the promoted piece
            promotion_map = {
                'q': Queen, 'r': Rook, 'b': Bishop, 'n': Knight
            }
            cls = promotion_map[prom.lower()]
            new_piece = cls(side, (ex, ey), board)
            board.pieces_on_board.append(new_piece)
        else:
            piece.move((ex, ey))

        board.update_grid()
        board.update_checks()
        return board


    def model_move(self, side, in_board):
        board = in_board.clone()
        # map files → 0–7
        file_to_i = {f:i for i,f in enumerate('abcdefgh')}

        fen = board.to_fen()

        with torch.no_grad():
            mask = torch.from_numpy(self.processor.legal_moves_mask(fen))
            in_tensor = torch.from_numpy(self.processor.fen_to_tensor(fen)[0])
            flags = torch.from_numpy(self.processor.fen_to_tensor(fen)[1])

            move_pred = self.model(in_tensor, flags)
            move_pred_masked = move_pred.masked_fill(~mask.bool(), -1e9)
            moves_prob = torch.softmax(move_pred_masked, dim=1, dtype=torch.float32)
            move_uci = self.processor.decode_policy_vector(moves_prob, side_to_move=side)

        if move_uci is None:
            raise RuntimeError("Stockfish returned no move")

        # parse it
        from_sq, to_sq = move_uci[:2], move_uci[2:4]
        prom = move_uci[4] if len(move_uci) == 5 else None

        sx, sy = file_to_i[from_sq[0]], int(from_sq[1]) - 1
        ex, ey = file_to_i[to_sq[0]], int(to_sq[1]) - 1

        piece = board.grid[sy][sx]
        # call your move, passing promotion if any
        if prom:
            # if your Pawn.move API takes a promotion arg:
            piece._captured = True
            # Create the promoted piece
            promotion_map = {
                'q': Queen, 'r': Rook, 'b': Bishop, 'n': Knight
            }
            cls = promotion_map[prom.lower()]
            new_piece = cls(side, (ex, ey), board)
            board.pieces_on_board.append(new_piece)
        else:
            piece.move((ex, ey))

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