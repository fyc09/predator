import {
  Game,
  Board,
  PUBLIC,
  Position,
  RED,
  INIT_SCORE,
  BASE_CAMP_INIT_SCORE,
  NEW_SCORE,
  GREEN,
  Frozen,
  Grid,
  Turn,
  ErrorCode,
  ERR_FROZEN,
  ERR_NO_SURROUNDED,
  ERR_SURROUNDED_BASE_CAMP,
  ZERO_POSITION,
  ERR_FIX_BASE_CAMP,
} from "./types";

export function initGame(width: number, height: number): Game {
  let board: Board = [];
  for (let i = 0; i < width; i++) {
    board.push([]);
    for (let j = 0; j < height; j++) {
      board[board.length - 1].push([PUBLIC, 0]);
    }
  }

  let pos: Position;

  pos = getCamp(board, RED);
  board[pos[0]][pos[1]] = [RED, BASE_CAMP_INIT_SCORE];

  pos = getCamp(board, GREEN);
  board[pos[0]][pos[1]] = [GREEN, BASE_CAMP_INIT_SCORE];

  return {
    board,
    frozen: [
      [-1, -1],
      [-1, -1],
    ],
  };
}

function boardGetPosition(board: Board, pos: Position) {
  return board[pos[0]][pos[1]];
}

function frozenAddPosition(frozen: Frozen, pos: Position) {
  frozen[0] = frozen[1];
  frozen[1] = pos;
}

function gridSet(grid: Grid, tar: Grid) {
  grid[0] = tar[0];
  grid[1] = tar[1];
}

export function handleRequest(
  game: Game,
  pos: Position,
  turn: Turn
): Game | ErrorCode {
  const { board, frozen } = game;

  let OWN: Turn, OTHER: Turn;
  switch (turn) {
    case PUBLIC:
      return game;
    case RED:
      OWN = RED;
      OTHER = GREEN;
      break;
    case GREEN:
      OWN = GREEN;
      OTHER = RED;
      break;
    default:
      throw Error(`Unknown turn: ${turn}`);
  }

  if (frozen.filter((val) => pos.toString() == val.toString()).length) {
    return ERR_FROZEN;
  }

  let grid = boardGetPosition(board, pos);
  let adjacentGridCount: number;

  let getPlace = false;
  let losePlace = false;

  switch (grid[0]) {
    case PUBLIC:
      gridSet(grid, [OWN, INIT_SCORE]);
      frozenAddPosition(frozen, ZERO_POSITION);

      // 必须和大本营连接
      if (!isReachable(board, OWN, getCamp(board, OWN), [pos])) {
        return ERR_NO_SURROUNDED;
      }

      getPlace = true;
      break;

    case OWN:
      if (getCamp(board, turn).toString() == pos.toString()) {
        return ERR_FIX_BASE_CAMP;
      }

      adjacentGridCount = getAdjacentGrids(board, pos, OWN).length;
      grid[1] += getIncrease(adjacentGridCount);

      frozenAddPosition(frozen, pos);
      break;

    case OTHER:
      adjacentGridCount = getAdjacentGrids(board, pos, OWN).length;
      if (!adjacentGridCount) {
        return ERR_NO_SURROUNDED;
      }
      grid[1] -= getDecrease(adjacentGridCount);

      // 如果小于0，改为己方领地
      if (grid[1] < 0) {
        grid[0] = OWN;
        grid[1] = -grid[1] + NEW_SCORE;
        getPlace = true;
        losePlace = true;
      }
      frozenAddPosition(frozen, pos);
      break;
  }

  if (losePlace) {
    for (let i = 0; i < board.length; i++) {
      for (let j = 0; j < board[i].length; j++) {
        // 只有对方的地可能断开
        if (board[i][j][0] != OTHER) {
          continue;
        }

        let NOW = board[i][j][0];
        // 与大本营断开连接的，改为无人区
        if (!isReachable(board, NOW, getCamp(board, NOW), [[i, j]])) {
          board[i][j] = [PUBLIC, 0];
        }
      }
    }
  }

  if (getPlace) {
    let reds: Position[] = [];
    let greens: Position[] = [];
    for (let i = 0; i < board.length; i++) {
      for (let j = 0; j < board[i].length; j++) {
        switch (board[i][j][0]) {
          case RED:
            reds.push([i, j]);
            break;
          case GREEN:
            greens.push([i, j]);
            break;
        }
      }
    }

    if (
      !isReachable(board, -RED, getCamp(board, RED), greens) ||
      !isReachable(board, -GREEN, getCamp(board, GREEN), reds)
    ) {
      return ERR_SURROUNDED_BASE_CAMP;
    }
  }
  return { board, frozen };
}

export function getCamp(board: Board, turn: Turn): Position {
  return turn == RED ? [0, 0] : [board.length - 1, board[0].length - 1];
}

export function isReachable(
  board: Board,
  turn: Turn,
  startPosition: Position,
  endPositions: Position[]
) {
  board = board.map((val) => val.map((pos) => [...pos]));
  endPositions.forEach((pos) => {
    let [x, y] = pos;
    board[x][y][0] = turn > 0 ? turn : PUBLIC;
  });

  let stack = new Set([startPosition.toString()]);
  let finished = new Set();

  while (stack.size) {
    let currentPosition = [...stack][0];
    stack.delete(currentPosition);

    finished.add(currentPosition.toString());

    let newPos = getAdjacentGrids(
      board,
      JSON.parse(`[${currentPosition}]`),
      turn
    ).filter((pos) => !finished.has(pos.toString()));

    newPos.forEach((pos) => stack.add(pos.toString()));
  }

  if (endPositions.filter((pos) => !finished.has(pos.toString())).length) {
    return false;
  } else {
    return true;
  }
}

export function getDecrease(adjacentGridCount: number) {
  if (adjacentGridCount <= 3) {
    return 1;
  } else {
    return 2;
  }
}

export function getIncrease(adjacentGridCount: number) {
  if (adjacentGridCount <= 3) {
    return 1;
  } else {
    return 2;
  }
}

export function getAdjacentGrids(board: Board, pos: Position, turn: Turn) {
  const [x, y] = pos;
  let adjacentGrids = [
    [x, y - 1],
    [x, y + 1],
  ];
  if (x + 1 < board.length) {
    adjacentGrids.push([x + 1, y - 1], [x + 1, y], [x + 1, y + 1]);
  }
  if (x - 1 >= 0) {
    adjacentGrids.push([x - 1, y - 1], [x - 1, y], [x - 1, y + 1]);
  }

  let result = adjacentGrids.filter((pos) => {
    let [x, y] = pos;
    let grid = board[x][y];
    return (
      grid != undefined &&
      (turn == 0 || (turn > 0 ? grid[0] == turn : grid[0] != -turn))
    );
  });
  return result;
}

export function copyGame(game: Game): Game {
  const { board, frozen } = game;
  return {
    board: board.map((row) => row.map((grid) => [...grid])),
    frozen: [
      [frozen[0][0], frozen[0][1]],
      [frozen[1][0], frozen[1][1]],
    ],
  };
}
