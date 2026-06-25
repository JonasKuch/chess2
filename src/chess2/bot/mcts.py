"""
AlphaZero-style PUCT Monte-Carlo Tree Search around the policy+value net.

The search runs on python-chess `Board`s (legal move generation, push/pop and
terminal detection come for free). The network supplies, per node:
  - priors P(a) from the policy head (used in the PUCT exploration term),
  - a scalar value V in [-1, 1] from the value head (leaf evaluation, no rollout).

Move <-> policy-index mapping reuses TensorProcessor (legal_moves_mask,
fen_to_tensor, uci_to_idx), so the search shares exactly the encoding the net
was trained on.
"""

import math

import chess
import numpy as np
import torch


class MCTSNode:
    __slots__ = ("prior", "visits", "value_sum", "children", "is_expanded")

    def __init__(self, prior):
        self.prior = prior
        self.visits = 0
        self.value_sum = 0.0
        self.children = {}        # chess.Move -> MCTSNode
        self.is_expanded = False

    def q(self):
        # mean value from the perspective of the player to move AT this node
        return self.value_sum / self.visits if self.visits else 0.0


class MCTS:
    def __init__(self, model, processor, device="cpu", c_puct=1.5):
        self.model = model
        self.processor = processor
        self.device = device
        self.c_puct = c_puct

    # --- network evaluation -------------------------------------------------
    @torch.no_grad()
    def evaluate(self, board):
        """Return (priors: dict[chess.Move, float], value: float) for `board`.

        value is from the side-to-move's perspective.
        """
        fen = board.fen()
        mask = self.processor.legal_moves_mask(fen).astype(bool)   # (1858,)
        in_tensor, flags, _ = self.processor.fen_to_tensor(fen)

        x = torch.from_numpy(in_tensor).to(self.device)
        fl = torch.from_numpy(flags).float().to(self.device)
        policy_logits, value = self.model(x, fl)

        logits = policy_logits.cpu().numpy().reshape(-1)
        value = float(value.reshape(-1)[0])

        # masked softmax over legal indices only
        logits = np.where(mask, logits, -np.inf)
        logits -= logits.max()
        exp = np.exp(logits)
        exp[~mask] = 0.0
        probs = exp / (exp.sum() + 1e-8)

        side = "w" if board.turn else "b"
        priors = {}
        for move in board.legal_moves:
            uci = move.uci()
            if uci[-1] == "n":          # knight promotions are not in the 1858 space
                continue
            priors[move] = float(probs[self.processor.uci_to_idx(uci, side)])
        return priors, value

    # --- tree ops -----------------------------------------------------------
    def _expand(self, node, priors):
        node.is_expanded = True
        for move, p in priors.items():
            node.children[move] = MCTSNode(prior=p)

    def _select_child(self, parent):
        best_score, best = -math.inf, None
        sqrt_total = math.sqrt(parent.visits + 1)
        for move, child in parent.children.items():
            q = -child.q()  # child stores the opponent's perspective
            u = self.c_puct * child.prior * sqrt_total / (1 + child.visits)
            score = q + u
            if score > best_score:
                best_score, best = score, (move, child)
        return best

    @staticmethod
    def _terminal_value(board):
        # called when board.is_game_over(); from the side-to-move's perspective
        if board.is_checkmate():
            return -1.0     # side to move is mated -> loss
        return 0.0          # stalemate / insufficient material / 50-move / repetition

    @staticmethod
    def _backup(path, leaf_value):
        v = leaf_value
        for node in reversed(path):
            node.visits += 1
            node.value_sum += v
            v = -v          # flip perspective each ply

    # --- public API ---------------------------------------------------------
    def search(self, root_board, num_simulations):
        root = MCTSNode(prior=1.0)
        priors, _ = self.evaluate(root_board)
        self._expand(root, priors)

        for _ in range(num_simulations):
            board = root_board.copy()
            node = root
            path = [root]

            # SELECT down to a leaf
            while node.is_expanded and node.children:
                move, node = self._select_child(node)
                board.push(move)
                path.append(node)

            # EXPAND + EVALUATE
            if board.is_game_over():
                value = self._terminal_value(board)
            else:
                priors, value = self.evaluate(board)
                self._expand(node, priors)

            self._backup(path, value)

        best_move = max(root.children.items(), key=lambda kv: kv[1].visits)[0]
        return best_move, root
