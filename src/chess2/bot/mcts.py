"""
AlphaZero-style PUCT Monte-Carlo Tree Search around the policy+value net.

The search runs on python-chess `Board`s (legal move generation, push/pop and
terminal detection come for free). The network supplies, per node:
  - priors P(a) from the policy head (used in the PUCT exploration term),
  - a scalar value V in [-1, 1] from the value head (leaf evaluation, no rollout).

Move <-> policy-index mapping reuses TensorProcessor (legal_moves_mask,
fen_to_tensor, uci_to_idx), so the search shares exactly the encoding the net
was trained on.

The dominant cost of a search is the per-simulation network forward pass. Rather
than evaluate one leaf at a time (batch=1, which starves the GPU), the search is
*leaf-parallel*: it descends `batch_size` times per step, applying a temporary
"virtual loss" along each descent so the descents diverge to different leaves,
then evaluates all collected leaves in a SINGLE batched forward. Virtual loss is
removed at backup. This changes the search slightly versus a purely sequential
MCTS (the standard, accepted tradeoff) but makes each forward ~10-40x cheaper
per position on a GPU.
"""

import math

import chess
import numpy as np
import torch


class MCTSNode:
    __slots__ = ("prior", "visits", "value_sum", "children", "is_expanded", "virtual_loss")

    def __init__(self, prior):
        self.prior = prior
        self.visits = 0
        self.value_sum = 0.0
        self.children = {}        # chess.Move -> MCTSNode
        self.is_expanded = False
        self.virtual_loss = 0     # pending in-flight visits within the current batch

    def q(self):
        # mean value from the perspective of the player to move AT this node.
        # virtual loss counts as in-flight visits that lost, so concurrent
        # descents are discouraged from re-selecting the same path.
        eff_visits = self.visits + self.virtual_loss
        if not eff_visits:
            return 0.0
        return (self.value_sum - self.virtual_loss) / eff_visits


class MCTS:
    def __init__(self, model, processor, device="cpu", c_puct=1.5,
                 batch_size=16, virtual_loss=1.0):
        self.model = model
        self.processor = processor
        self.device = device
        self.c_puct = c_puct
        self.batch_size = batch_size
        self.virtual_loss = virtual_loss

    # --- network evaluation -------------------------------------------------
    def _encode(self, board):
        """CPU-only: encode `board` to (in_tensor, flags, mask, legal_moves).

        No network call -- the encodings are stacked and evaluated in batches.
        """
        fen = board.fen()
        mask = self.processor.legal_moves_mask(fen).astype(bool)   # (1858,)
        in_tensor, flags, _ = self.processor.fen_to_tensor(fen)    # (1,12,8,8), (1,5)
        legal_moves = list(board.legal_moves)
        return in_tensor, flags, mask, legal_moves

    @torch.no_grad()
    def _forward_batch(self, in_tensors, flags_list):
        """Run a single batched forward over stacked encodings.

        Returns (logits[B,1858], values[B]) as numpy arrays.
        """
        x = torch.from_numpy(np.concatenate(in_tensors, axis=0)).to(self.device)
        fl = torch.from_numpy(np.concatenate(flags_list, axis=0)).float().to(self.device)
        policy_logits, value = self.model(x, fl)
        return policy_logits.cpu().numpy(), value.reshape(-1).cpu().numpy()

    def _priors_from_logits(self, logits, mask, legal_moves, turn):
        """Masked softmax over legal indices -> {chess.Move: prior}."""
        logits = np.where(mask, logits, -np.inf)
        logits = logits - logits.max()
        exp = np.exp(logits)
        exp[~mask] = 0.0
        probs = exp / (exp.sum() + 1e-8)

        side = "w" if turn else "b"
        priors = {}
        for move in legal_moves:
            uci = move.uci()
            if uci[-1] == "n":          # knight promotions are not in the 1858 space
                continue
            priors[move] = float(probs[self.processor.uci_to_idx(uci, side)])
        return priors

    def evaluate(self, board):
        """Single-board (priors, value) -- convenience wrapper over the batch path."""
        in_tensor, flags, mask, legal_moves = self._encode(board)
        logits, values = self._forward_batch([in_tensor], [flags])
        priors = self._priors_from_logits(logits[0], mask, legal_moves, board.turn)
        return priors, float(values[0])

    # --- tree ops -----------------------------------------------------------
    def _expand(self, node, priors):
        node.is_expanded = True
        for move, p in priors.items():
            node.children[move] = MCTSNode(prior=p)

    def _select_child(self, parent):
        best_score, best = -math.inf, None
        sqrt_total = math.sqrt(parent.visits + parent.virtual_loss + 1)
        for move, child in parent.children.items():
            q = -child.q()  # child stores the opponent's perspective
            eff_visits = child.visits + child.virtual_loss
            u = self.c_puct * child.prior * sqrt_total / (1 + eff_visits)
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

    @staticmethod
    def _add_virtual_loss(path, amount):
        for node in path:
            node.virtual_loss += amount

    @staticmethod
    def _remove_virtual_loss(path, amount):
        for node in path:
            node.virtual_loss -= amount

    # --- public API ---------------------------------------------------------
    def search(self, root_board, num_simulations):
        root = MCTSNode(prior=1.0)
        priors, _ = self.evaluate(root_board)
        self._expand(root, priors)

        done = 0
        while done < num_simulations:
            batch_target = min(self.batch_size, num_simulations - done)
            collected = []   # entries: (path, board, leaf_node, terminal_value)

            for _ in range(batch_target):
                board = root_board.copy()
                node = root
                path = [root]

                # SELECT down to a leaf, marking the path with virtual loss so
                # the next descent in this batch avoids it.
                while node.is_expanded and node.children:
                    move, node = self._select_child(node)
                    board.push(move)
                    path.append(node)

                self._add_virtual_loss(path, self.virtual_loss)

                terminal_value = self._terminal_value(board) if board.is_game_over() else None
                collected.append((path, board, node, terminal_value))

            # EVALUATE all non-terminal leaves in one batched forward.
            pending = [c for c in collected if c[3] is None]
            if pending:
                encodings = [self._encode(b) for (_, b, _, _) in pending]
                in_tensors = [e[0] for e in encodings]
                flags_list = [e[1] for e in encodings]
                logits, values = self._forward_batch(in_tensors, flags_list)
                expanded = set()
                for i, (path, board, node, _) in enumerate(pending):
                    in_tensor, flags, mask, legal_moves = encodings[i]
                    priors = self._priors_from_logits(logits[i], mask, legal_moves, board.turn)
                    # the same leaf can be collected twice in a batch; expand once
                    if id(node) not in expanded and not node.is_expanded:
                        self._expand(node, priors)
                        expanded.add(id(node))
                    value = float(values[i])
                    self._remove_virtual_loss(path, self.virtual_loss)
                    self._backup(path, value)

            # terminal leaves: no network eval needed.
            for path, board, node, terminal_value in collected:
                if terminal_value is None:
                    continue
                self._remove_virtual_loss(path, self.virtual_loss)
                self._backup(path, terminal_value)

            done += batch_target

        best_move = max(root.children.items(), key=lambda kv: kv[1].visits)[0]
        return best_move, root
