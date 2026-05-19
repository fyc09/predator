from mcts.mcts import MCTS, _valid_moves
from mcts.evaluate import heuristic_value
from game.core import copy_game, handle_request


def get_move(game, turn, network=None, device="cpu", iterations=800, eval_mode="nn"):
    if eval_mode == "heuristic":
        mcts = MCTS(game, turn, network=None, device=device, eval_mode="heuristic")
        mcts.run(iterations=iterations)
        return mcts.get_best_move(), mcts.get_winrates()
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
