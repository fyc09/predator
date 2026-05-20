import os
import glob
from ai import random as random_ai
from ai import mcts_ai
from model.network import PredatorNetwork

_models = {}


def load_weights(device="cpu"):
    weights_dir = os.path.join(os.path.dirname(__file__), "..", "weights")
    for path in sorted(glob.glob(os.path.join(weights_dir, "*.pt"))):
        name = os.path.splitext(os.path.basename(path))[0]
        net = PredatorNetwork(num_blocks=4, channels=32)
        net.load(path, device)
        net.to(device)
        net.eval()
        _models[name] = (net, device, "nn")
        print(f"[handler] loaded model '{name}'")


def list_models():
    return sorted(_models.keys())


async def handle(method, params):
    if method == "ping":
        return "pong"

    if method == "list_models":
        return list_models()

    if method == "get_move":
        turn = params["turn"]
        board = params["board"]
        frozen = params["frozen"]
        model = params.get("model", "latest")
        game = {"board": board, "frozen": frozen}

        entry = _models.get(model)
        if entry:
            net, device, mode = entry
            move, winrates = mcts_ai.get_move(
                game, turn, network=net, device=device,
                iterations=200, eval_mode=mode,
            )
        else:
            move = random_ai.get_move(game, turn)
            winrates = {}
        return {"move": move, "winrates": winrates}

    raise ValueError(f"Unknown method: {method}")
