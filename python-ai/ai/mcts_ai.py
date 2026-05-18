from game import core
from mcts.mcts import MCTS


def get_move(game, turn, network, device="cpu", iterations=800):
    mcts = MCTS(game, turn, network, device=device)
    mcts.run(iterations=iterations)
    return mcts.get_best_move(), mcts.get_winrates()


def get_winrates(game, turn, network, device="cpu", iterations=400):
    mcts = MCTS(game, turn, network, device=device)
    mcts.run(iterations=iterations)
    return mcts.get_winrates()
