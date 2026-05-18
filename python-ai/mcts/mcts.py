import math
import numpy as np

from game import core
from game.types import WIN_NONE
from model import encoder
from model.network import BOARD_SIZE


class Node:
    def __init__(self, parent, prior_prob=0.0):
        self.parent = parent
        self.children = {}
        self.prior_prob = prior_prob
        self.visit_count = 0
        self.total_value = 0.0
        self.is_terminal = False
        self.winner = WIN_NONE

    @property
    def value(self):
        if self.visit_count == 0:
            return 0.0
        return self.total_value / self.visit_count

    def is_leaf(self):
        return len(self.children) == 0

    def expand(self, legal_moves, priors):
        for move in legal_moves:
            x, y = move
            idx = x * BOARD_SIZE + y
            prior = float(priors[idx])
            self.children[(x, y)] = Node(self, prior)

    def select_child(self, c_puct=1.5):
        best_score = -float("inf")
        best_move = None
        best_child = None
        sqrt_parent = math.sqrt(self.visit_count)

        for move, child in self.children.items():
            q = child.value
            u = c_puct * child.prior_prob * sqrt_parent / (1 + child.visit_count)
            score = q + u
            if score > best_score:
                best_score = score
                best_move = move
                best_child = child

        return best_move, best_child

    def update(self, value):
        self.visit_count += 1
        self.total_value += value

    def backpropagate(self, leaf_value):
        node = self
        v = leaf_value
        while node:
            node.update(v)
            node = node.parent
            v = -v


def mask_policy(policy, legal_moves):
    legal_set = set(tuple(m) for m in legal_moves)
    masked = np.zeros(BOARD_SIZE * BOARD_SIZE, dtype=np.float32)

    for x, y in legal_set:
        idx = x * BOARD_SIZE + y
        masked[idx] = policy[idx]

    total = masked.sum()
    if total > 0:
        masked /= total
    else:
        uniform = 1.0 / len(legal_moves)
        for x, y in legal_moves:
            masked[x * BOARD_SIZE + y] = uniform

    return masked


def _valid_moves(game, turn):
    """Filter legal moves that pass handle_request validation."""
    legal = core.get_legal_moves(game, turn)
    valid = []
    for m in legal:
        r = core.handle_request(core.copy_game(game), m, turn)
        if not isinstance(r, int):
            valid.append(m)
    return valid


class MCTS:
    def __init__(self, game, turn, network, device="cpu", c_puct=1.5):
        self.network = network
        self.device = device
        self.c_puct = c_puct

        self._root_game = core.copy_game(game)
        self._root_turn = turn

        self.root = Node(None)
        self._init_root()

    def _init_root(self):
        legal = _valid_moves(self._root_game, self._root_turn)
        if not legal:
            self.root.is_terminal = True
            self.root.winner = core.check_win(self._root_game["board"])
            return

        encoded = encoder.encode(self._root_game, self._root_turn)
        policy, value = self.network.predict(encoded, self.device)

        masked = mask_policy(policy, legal)
        self.root.expand(legal, masked)
        self.root.total_value += value

    def run(self, iterations=800):
        for _ in range(iterations):
            self._iterate()

    def _iterate(self):
        node = self.root
        game = core.copy_game(self._root_game)
        turn = self._root_turn

        while not node.is_leaf() and not node.is_terminal:
            move, child = node.select_child(self.c_puct)
            r = core.handle_request(game, move, turn)
            if isinstance(r, int):
                del node.children[move]
                if not node.children:
                    return
                continue
            game = r
            turn = 5 - turn
            node = child

        if node.is_terminal:
            node.backpropagate(self._terminal_value(node, turn))
            return

        legal = _valid_moves(game, turn)
        if not legal:
            winner = core.check_win(game["board"])
            node.is_terminal = True
            node.winner = winner
            node.backpropagate(self._terminal_value(node, turn))
            return

        encoded = encoder.encode(game, turn)
        policy, value = self.network.predict(encoded, self.device)

        masked = mask_policy(policy, legal)
        node.expand(legal, masked)
        node.backpropagate(value)

    def _terminal_value(self, node, current_turn):
        if node.winner == WIN_NONE:
            return 0.0
        return 1.0 if node.winner == current_turn else -1.0

    def get_best_move(self):
        best = None
        best_count = -1
        for move, child in self.root.children.items():
            if child.visit_count > best_count:
                best_count = child.visit_count
                best = move
        return best

    def get_policy(self, temperature=1.0):
        visits = np.zeros(BOARD_SIZE * BOARD_SIZE, dtype=np.float32)
        for (x, y), child in self.root.children.items():
            visits[x * BOARD_SIZE + y] = child.visit_count

        if temperature == 0:
            idx = np.argmax(visits)
            policy = np.zeros_like(visits)
            policy[idx] = 1.0
            return policy

        visits = visits ** (1.0 / temperature)
        total = visits.sum()
        if total > 0:
            visits /= total
        return visits

    def select_move(self, temperature=1.0):
        policy = self.get_policy(temperature)
        idx = np.random.choice(len(policy), p=policy)
        return (idx // BOARD_SIZE, idx % BOARD_SIZE)

    def get_winrates(self):
        winrates = {}
        total = sum(c.visit_count for c in self.root.children.values())
        if total == 0:
            return winrates
        for (x, y), child in self.root.children.items():
            winrates[f"{x},{y}"] = child.visit_count / total
        return winrates
