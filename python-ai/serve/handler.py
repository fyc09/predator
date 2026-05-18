from game import core
from ai import random as random_ai
from ai import mcts_ai

_network = None
_device = "cpu"
_use_mcts = False


def set_network(network, device):
    global _network, _device, _use_mcts
    _network = network
    _device = device
    _use_mcts = network is not None


async def handle(method, params):
    if method == "ping":
        return "pong"

    if method == "get_move":
        turn = params["turn"]
        board = params["board"]
        frozen = params["frozen"]
        game = {"board": board, "frozen": frozen}

        if _use_mcts and _network is not None:
            move, winrates = mcts_ai.get_move(
                game, turn, _network, device=_device, iterations=800
            )
            return {"move": move, "winrates": winrates}
        else:
            move = random_ai.get_move(game, turn)
            return {"move": move, "winrates": {}}

    if method == "get_winrates":
        turn = params["turn"]
        board = params["board"]
        frozen = params["frozen"]
        game = {"board": board, "frozen": frozen}

        if _use_mcts and _network is not None:
            winrates = mcts_ai.get_winrates(
                game, turn, _network, device=_device, iterations=200
            )
            return {"winrates": winrates}
        else:
            winrates = random_ai.get_winrates(game, turn)
            return {"winrates": winrates}

    raise ValueError(f"Unknown method: {method}")
