from chess2.board import Board
from chess2.pieces import Pawn, Queen, Bishop, Rook, Knight
from chess2 import Color
import numpy as np
import copy
import os
import shutil
from stockfish import Stockfish
import torch
import chess
from chess2.bot import NeuralNetwork, TensorProcessor
from chess2.bot.mcts import MCTS

_stockfish = None


def default_model_path():
    """$CHESS2_MODEL if set, else the weights shipped with the package."""
    return os.environ.get("CHESS2_MODEL") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "weights", "chess2_rb6_c96.pth")


def get_stockfish(elo=1320):
    """Start Stockfish on first use. Binary from $STOCKFISH_PATH, else from PATH."""
    global _stockfish
    if _stockfish is None:
        path = os.environ.get("STOCKFISH_PATH") or shutil.which("stockfish")
        if path is None:
            raise RuntimeError("Stockfish not found: install it or set STOCKFISH_PATH")
        _stockfish = Stockfish(path=path)
        _stockfish.set_elo_rating(elo)
    return _stockfish



class MoveGenerator():
    def __init__(self, model_params_path=None, num_residual_blocks=6, channels=96, policy_channels=16,
                 use_mcts=False, num_simulations=400, mcts_batch_size=16):
        # Architecture must match the checkpoint being loaded. Defaults match the
        # shipped model (bot/weights/chess2_rb6_c96.pth); pass overrides
        # if you load a checkpoint trained with a different tower/head size.
        # Batched MCTS feeds many leaves per forward, so the GPU pays off; raw
        # policy is a single batch=1 forward per move, marginally faster on CPU.
        self.device = "mps" if (use_mcts and torch.backends.mps.is_available()) else "cpu"
        self.model = NeuralNetwork(
            num_residual_blocks=num_residual_blocks,
            channels=channels,
            policy_channels=policy_channels,
        ).to(self.device)
        model_params_path = model_params_path or default_model_path()
        if not os.path.exists(model_params_path):
            raise FileNotFoundError(
                f"no model weights at {model_params_path}: check CHESS2_MODEL")
        self.model.load_state_dict(torch.load(model_params_path, weights_only=True, map_location=self.device))
        self.model.eval()
        self.processor = TensorProcessor()
        self.use_mcts = use_mcts
        self.num_simulations = num_simulations
        self.mcts_batch_size = mcts_batch_size

    def bot_move(self, side, board):
        """Pick a move with PUCT MCTS if enabled, else the raw policy argmax."""
        if self.use_mcts:
            return self.mcts_move(side, board, num_simulations=self.num_simulations)
        return self.model_move(side, board)


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
        stockfish = get_stockfish()
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


    def apply_uci(self, board, move_uci, side):
        """Apply a UCI move (e.g. 'e2e4', 'e7e8q') to `board` in place and return it.

        Routes everything through Piece.move so captures, the 50-move clock,
        en-passant reset and castling-square handling all run -- including for
        promotions (the pawn advances via move(), then is swapped for the
        promoted piece).
        """
        file_to_i = {f: i for i, f in enumerate('abcdefgh')}
        from_sq, to_sq = move_uci[:2], move_uci[2:4]
        prom = move_uci[4] if len(move_uci) == 5 else None

        sx, sy = file_to_i[from_sq[0]], int(from_sq[1]) - 1
        ex, ey = file_to_i[to_sq[0]], int(to_sq[1]) - 1

        piece = board.grid[sy][sx]
        piece.move((ex, ey))

        if prom:
            promotion_map = {'q': Queen, 'r': Rook, 'b': Bishop, 'n': Knight}
            piece._captured = True   # remove the pawn that just advanced
            new_piece = promotion_map[prom.lower()](side, (ex, ey), board)
            board.pieces_on_board.append(new_piece)

        board.update_grid()
        board.update_checks()
        return board

    def model_move(self, side, in_board):
        board = in_board.clone()
        fen = board.to_fen()
        legal = self.processor.legal_move_indices(chess.Board(fen))
        in_tensor, flags, _ = self.processor.fen_to_tensor(fen)

        with torch.no_grad():
            logits, _ = self.model(torch.from_numpy(in_tensor).to(self.device),
                                   torch.from_numpy(flags).float().to(self.device))
        logits = logits[0].cpu().numpy()

        # highest-scoring legal move
        best_idx = max(legal, key=lambda idx: logits[idx])
        return self.apply_uci(board, legal[best_idx].uci(), side)

    def mcts_move(self, side, in_board, num_simulations=200, c_puct=1.5):
        board = in_board.clone()
        root_board = chess.Board(board.to_fen())
        mcts = MCTS(self.model, self.processor, device=self.device, c_puct=c_puct,
                    batch_size=self.mcts_batch_size)
        best_move, _ = mcts.search(root_board, num_simulations)
        return self.apply_uci(board, best_move.uci(), side)


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