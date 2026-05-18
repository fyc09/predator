import copy
from .types import *

def init_game(width=BOARD_SIZE, height=BOARD_SIZE):
    board = [[[PUBLIC, 0] for _ in range(height)] for _ in range(width)]
    board[0][0] = [RED, BASE_CAMP_INIT_SCORE]
    board[width - 1][height - 1] = [GREEN, BASE_CAMP_INIT_SCORE]
    return {
        "board": board,
        "frozen": [[-1, -1], [-1, -1]],
    }

def get_camp(board, turn):
    return (0, 0) if turn == RED else (len(board) - 1, len(board[0]) - 1)

def get_adjacent_grids(board, pos, turn):
    x, y = pos
    h, w = len(board), len(board[0])
    candidates = [[x, y - 1], [x, y + 1]]
    if x + 1 < h:
        candidates.extend([[x + 1, y - 1], [x + 1, y], [x + 1, y + 1]])
    if x - 1 >= 0:
        candidates.extend([[x - 1, y - 1], [x - 1, y], [x - 1, y + 1]])

    result = []
    for nx, ny in candidates:
        if 0 <= nx < h and 0 <= ny < w:
            grid = board[nx][ny]
            if turn == 0:
                result.append((nx, ny))
            elif turn > 0:
                if grid[0] == turn:
                    result.append((nx, ny))
            else:
                if grid[0] != -turn:
                    result.append((nx, ny))
    return result

def is_reachable(board, turn, start, end_positions):
    h, w = len(board), len(board[0])
    b = [[cell[:] for cell in row] for row in board]

    for x, y in end_positions:
        b[x][y][0] = PUBLIC if turn < 0 else turn

    stack = [tuple(start)]
    finished = set()

    while stack:
        current = stack.pop()
        if current in finished:
            continue
        finished.add(current)

        for adj in get_adjacent_grids(b, current, turn):
            if adj not in finished:
                stack.append(adj)

    return all(tuple(p) in finished for p in end_positions)


def handle_request(game, pos, turn):
    board = game["board"]
    frozen = game["frozen"]
    x, y = pos

    if turn == PUBLIC:
        return game

    OWN = turn
    OTHER = RED if turn == GREEN else GREEN

    if any(f[0] == x and f[1] == y for f in frozen if f[0] != -1):
        return ERR_FROZEN

    grid = board[x][y]
    get_place = False
    lose_place = False

    if grid[0] == PUBLIC:
        grid[0] = OWN
        grid[1] = INIT_SCORE
        frozen[0] = frozen[1][:]
        frozen[1] = [-1, -1]

        if not is_reachable(board, OWN, get_camp(board, OWN), [pos]):
            return ERR_NO_SURROUNDED

        get_place = True

    elif grid[0] == OWN:
        if list(get_camp(board, turn)) == [x, y]:
            return ERR_FIX_BASE_CAMP

        adj_count = len(get_adjacent_grids(board, pos, OWN))
        grid[1] += get_increase(adj_count)
        frozen[0] = frozen[1][:]
        frozen[1] = [x, y]

    else:
        adj_count = len(get_adjacent_grids(board, pos, OWN))
        if not adj_count:
            return ERR_NO_SURROUNDED
        grid[1] -= get_decrease(adj_count)

        if grid[1] < 0:
            grid[0] = OWN
            grid[1] = -grid[1] + NEW_SCORE
            get_place = True
            lose_place = True

        frozen[0] = frozen[1][:]
        frozen[1] = [x, y]

    if lose_place:
        for i in range(len(board)):
            for j in range(len(board[0])):
                if board[i][j][0] != OTHER:
                    continue
                if not is_reachable(board, OTHER, get_camp(board, OTHER), [[i, j]]):
                    board[i][j] = [PUBLIC, 0]

    if get_place:
        reds = []
        greens = []
        for i in range(len(board)):
            for j in range(len(board[0])):
                if board[i][j][0] == RED:
                    reds.append([i, j])
                elif board[i][j][0] == GREEN:
                    greens.append([i, j])

        if (
            not is_reachable(board, -RED, get_camp(board, RED), greens)
            or not is_reachable(board, -GREEN, get_camp(board, GREEN), reds)
        ):
            return ERR_SURROUNDED_BASE_CAMP

    return {"board": board, "frozen": frozen}


def get_decrease(adjacent_count):
    return 1 if adjacent_count <= 3 else 2


def get_increase(adjacent_count):
    return 1 if adjacent_count <= 3 else 2


def check_win(board):
    if board[0][0][0] != RED:
        return WIN_GREEN
    if board[len(board) - 1][len(board[0]) - 1][0] != GREEN:
        return WIN_RED
    return WIN_NONE


def copy_game(game):
    return {
        "board": [[cell[:] for cell in row] for row in game["board"]],
        "frozen": [game["frozen"][0][:], game["frozen"][1][:]],
    }


def get_legal_moves(game, turn):
    board = game["board"]
    frozen = game["frozen"]
    legal = []

    for x in range(len(board)):
        for y in range(len(board[0])):
            if any(f[0] == x and f[1] == y for f in frozen if f[0] != -1):
                continue

            grid = board[x][y]

            if grid[0] == PUBLIC:
                adj = get_adjacent_grids(board, (x, y), turn)
                if any(board[nx][ny][0] == turn for nx, ny in adj):
                    legal.append([x, y])

            elif grid[0] == turn:
                if [x, y] != list(get_camp(board, turn)):
                    legal.append([x, y])

            else:
                adj = get_adjacent_grids(board, (x, y), turn)
                if any(board[nx][ny][0] == turn for nx, ny in adj):
                    legal.append([x, y])

    return legal
