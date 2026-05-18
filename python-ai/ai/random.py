import random
from game import core


def get_move(game, turn):
    legal = core.get_legal_moves(game, turn)
    if not legal:
        return None
    return random.choice(legal)


def get_winrates(game, turn):
    legal = core.get_legal_moves(game, turn)
    return {f"{x},{y}": 1.0 / len(legal) for x, y in legal} if legal else {}
