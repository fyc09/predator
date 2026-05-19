import math
from game.types import RED, GREEN
from game.core import get_camp, get_legal_moves


def is_adjacent(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1


def heuristic_value(game, turn):
    board = game["board"]
    own = turn
    opp = RED if turn == GREEN else GREEN
    camp_opp = get_camp(board, opp)
    camp_own = get_camp(board, own)

    own_cells = []
    opp_cells = []
    h, w = len(board), len(board[0])

    for i in range(h):
        for j in range(w):
            t, _ = board[i][j]
            if t == own:
                own_cells.append((i, j))
            elif t == opp:
                opp_cells.append((i, j))

    max_dist = h + w

    dist_to_target = min(
        (abs(x - camp_opp[0]) + abs(y - camp_opp[1]) for x, y in own_cells),
        default=max_dist
    )
    dist_from_target = min(
        (abs(x - camp_own[0]) + abs(y - camp_own[1]) for x, y in opp_cells),
        default=0
    )

    territory = len(own_cells) - len(opp_cells)
    my_mobility = len(get_legal_moves(game, turn))
    opp_mobility = len(get_legal_moves(game, opp))
    mobility = my_mobility - opp_mobility

    adj_to_target = sum(1 for x, y in own_cells if is_adjacent((x, y), camp_opp))
    adj_to_my_base = sum(1 for x, y in opp_cells if is_adjacent((x, y), camp_own))

    raw = (-dist_to_target * 0.6
           + dist_from_target * 0.3
           + territory * 1.0
           + mobility * 0.3
           + adj_to_target * 2.0
           - adj_to_my_base * 1.0)
    return math.tanh(raw / (max_dist * 0.4))
