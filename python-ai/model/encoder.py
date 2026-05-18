import numpy as np

from game.core import get_camp
from game.types import RED, GREEN, BOARD_SIZE

NUM_CHANNELS = 9


def encode_board(board, frozen, turn):
    h, w = len(board), len(board[0])
    other = RED if turn == GREEN else GREEN
    camp = get_camp(board, turn)
    other_camp = get_camp(board, other)

    frozen_set = set()
    for fx, fy in frozen:
        if fx != -1:
            frozen_set.add((fx, fy))

    c = np.zeros((h, w, NUM_CHANNELS), dtype=np.float32)

    for i in range(h):
        for j in range(w):
            owner, score = board[i][j]

            if owner == turn:
                c[i, j, 0] = 1.0
                c[i, j, 3] = score / 10.0
            elif owner == other:
                c[i, j, 1] = 1.0
                c[i, j, 4] = score / 10.0
            else:
                c[i, j, 2] = 1.0

            if (i, j) in frozen_set:
                if owner == turn:
                    c[i, j, 5] = 1.0
                else:
                    c[i, j, 6] = 1.0

            if (i, j) == camp:
                c[i, j, 7] = 1.0
            if (i, j) == other_camp:
                c[i, j, 8] = 1.0

    return c


def encode(game, turn):
    return encode_board(game["board"], game["frozen"], turn)


def encode_batch(games, turns):
    batch = np.stack([encode(g, t) for g, t in zip(games, turns)], axis=0)
    return batch
