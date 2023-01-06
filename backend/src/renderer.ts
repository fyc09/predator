import { copyGame, handleRequest } from "./core";
import {
  Board,
  COLOR_AVAILABLE,
  COLOR_RED_FROZEN,
  COLOR_GREEN_FROZEN,
  COLOR_NONE,
  COLOR_UNAVAILABLE,
  ERR_FROZEN,
  Game,
  HINT_AVAILABLE,
  HINT_NONE,
  RenderedGame,
  Turn,
  COLOR_RED,
} from "./types";

export function renderBoard(board: Board): RenderedGame {
  let rendered: RenderedGame = [];
  for (let i = 0; i < board.length; i++) {
    rendered.push([]);
    for (let j = 0; j < board[0].length; j++) {
      let grid = board[i][j];

      rendered[rendered.length - 1].push({
        color: grid[0],
        score: grid[1],
        hover: grid[0],
        hint: HINT_NONE,
      });
    }
  }
  return rendered;
}

export function renderGame(
  game: Game,
  turn: Turn,
  currentTurn: Turn
): RenderedGame {
  let renderedGame = renderBoard(game.board);

  let isCurrent = false;
  if (turn == currentTurn) {
    isCurrent = true;
  }

  for (let i = 0; i < game.board.length; i++) {
    for (let j = 0; j < game.board[0].length; j++) {
      let result = handleRequest(copyGame(game), [i, j], currentTurn);
      let grid = renderedGame[i][j];
      if (result < 0) {
        grid.hint = -result;
        grid.hover = COLOR_UNAVAILABLE;
      } else {
        grid.hint = HINT_AVAILABLE;
        grid.hover = isCurrent ? turn : COLOR_AVAILABLE;
      }
      if (result == ERR_FROZEN) {
        if (grid.color == COLOR_RED) {
          grid.color = COLOR_RED_FROZEN;
        } else {
          grid.color = COLOR_GREEN_FROZEN;
        }
        grid.hover = grid.color;
      }
    }
  }

  return renderedGame;
}
