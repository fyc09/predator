import {
  handleRequest,
  copyGame,
  ERR_FROZEN,
  ERR_TOO_MANY_SURROUNDED,
  ERR_SURROUNDED_BASE_CAMP,
  ERR_DISCONNECTED_FROM_BASE_CAMP,
  ERR_NO_SURROUNDED,
  Turn,
  Game,
  Board,
} from "./core";

export type Color = "" | "gray" | "red" | "green" | "sienna" | "goldenrod";
const colorMapping: Color[] = ["", "gray", "red", "green"];
export type Hint =
  | ""
  | "领地未与大本营连接"
  | "领地有太多包围"
  | "已被冻结"
  | "包围大本营"
  | "周围没有包围";
export type Score = string;
export type ColoredGrid = { color: Color; score: Score };
export type ColoredBoard = ColoredGrid[][];
export type RenderedGrid = { hint: Hint; board: ColoredBoard };
export type RenderedBoard = RenderedGrid[][];
export type RenderedGame = { origin: RenderedGrid; board: RenderedBoard };

export function renderBoard(board: Board, _turn: Turn): ColoredBoard {
  let rendered: ColoredBoard = [];
  for (let i = 0; i < board.length; i++) {
    rendered.push([]);
    for (let j = 0; j < board[0].length; j++) {
      let grid = board[i][j];

      rendered[rendered.length - 1].push({
        color: colorMapping[grid[0]],
        score: grid[1].toString(),
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
  const { board, frozen } = game;
  let renderedBoard: RenderedBoard = [];
  let result: RenderedGame = {
    origin: { hint: "", board: renderBoard(board, turn) },
    board: renderedBoard,
  };

  let cache = renderBoard(board, turn);

  for (let i = 0; i < board.length; i++) {
    renderedBoard.push([]);
    let row = renderedBoard[renderedBoard.length - 1];

    for (let j = 0; j < board[i].length; j++) {
      let result = handleRequest(copyGame({ board, frozen }), [i, j], turn);

      let RenderedGrid: RenderedGrid = {
        board: cache.map((val) =>
          val.map((grid) => {
            return { ...grid };
          })
        ),
        hint: "",
      };

      if (turn == currentTurn) {
        let grid = RenderedGrid.board[i][j];
        switch (result) {
          case ERR_DISCONNECTED_FROM_BASE_CAMP:
            grid.color = "sienna";
            RenderedGrid.hint = "领地未与大本营连接";
            break;
          case ERR_TOO_MANY_SURROUNDED:
            grid.color = "sienna";
            RenderedGrid.hint = "领地有太多包围";
            break;
          case ERR_FROZEN:
            grid.color = "sienna";
            RenderedGrid.hint = "已被冻结";
            break;
          case ERR_SURROUNDED_BASE_CAMP:
            grid.color = "sienna";
            RenderedGrid.hint = "包围大本营";
            break;
          case ERR_NO_SURROUNDED:
            grid.color = "sienna";
            RenderedGrid.hint = "周围没有包围";
            break;
          default:
            grid.color = "goldenrod";
        }
      }

      row.push(RenderedGrid);
    }
  }

  return result;
}
