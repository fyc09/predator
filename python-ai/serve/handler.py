from game import core
from ai import random as random_ai
from ai import mcts_ai

_network = None
_device = "cpu"
_eval_mode = "nn"


def set_network(network, device):
    global _network, _device
    _network = network
    _device = device


def set_eval_mode(mode):
    global _eval_mode
    _eval_mode = mode


def _call_mcts(game, turn, iterations=200):
    if _eval_mode == "heuristic":
        return mcts_ai.get_move(game, turn, eval_mode="heuristic")
    elif _eval_mode == "nn" and _network is not None:
        return mcts_ai.get_move(
            game, turn, network=_network, device=_device,
            iterations=iterations, eval_mode="nn",
        )
    else:
        move = random_ai.get_move(game, turn)
        return move, {}


async def handle(method, params):
    if method == "ping":
        return "pong"

    if method == "get_move":
        turn = params["turn"]
        board = params["board"]
        frozen = params["frozen"]
        game = {"board": board, "frozen": frozen}

        move, winrates = _call_mcts(game, turn, iterations=200)
        return {"move": move, "winrates": winrates}

    if method == "get_winrates":
        turn = params["turn"]
        board = params["board"]
        frozen = params["frozen"]
        game = {"board": board, "frozen": frozen}

        if _eval_mode == "heuristic":
            winrates = mcts_ai.get_winrates(game, turn, eval_mode="heuristic")
        elif _eval_mode == "nn" and _network is not None:
            winrates = mcts_ai.get_winrates(
                game, turn, network=_network, device=_device,
                iterations=200, eval_mode="nn",
            )
        else:
            winrates = random_ai.get_winrates(game, turn)
        return {"winrates": winrates}

    raise ValueError(f"Unknown method: {method}")
