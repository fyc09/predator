from mcts.mcts import MCTS, _valid_moves
from mcts.evaluate import heuristic_value
from game.core import copy_game, handle_request


def get_move(game, turn, network=None, device="cpu", iterations=800, eval_mode="nn"):
    if eval_mode == "heuristic":
        return _greedy(game, turn)
    mcts = MCTS(game, turn, network=network, device=device)
    mcts.run(iterations=iterations)
    return mcts.get_best_move(), mcts.get_winrates()


def get_winrates(game, turn, network=None, device="cpu", iterations=400, eval_mode="nn"):
    if eval_mode == "heuristic":
        legal = _valid_moves(game, turn)
        return {f"{x},{y}": 1.0 / len(legal) for x, y in legal} if legal else {}
    mcts = MCTS(game, turn, network=network, device=device)
    mcts.run(iterations=iterations)
    return mcts.get_winrates()


def _greedy(game, turn):
    legal = _valid_moves(game, turn)
    if not legal:
        return None, {}
    best = None
    best_v = -float("inf")
    for m in legal:
        g = handle_request(copy_game(game), m, turn)
        v = heuristic_value(g, turn)
        if v > best_v:
            best_v = v
            best = m
    return best, {}
