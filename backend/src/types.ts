import ws from "ws";

export const INIT_SCORE = 6;

export type Turn = number;

export const PUBLIC: Turn = 1;
export const RED: Turn = 2;
export const GREEN: Turn = 3;

export type ErrorCode = number;

export const ERR_SURROUNDED_BASE_CAMP: ErrorCode = -1;
export const ERR_TOO_MANY_SURROUNDED: ErrorCode = -2;
export const ERR_FROZEN: ErrorCode = -3;
export const ERR_NO_SURROUNDED: ErrorCode = -4;

export type Position = [number, number];
export const ZERO_POSITION: Position = [-1, -1];

export type Score = number;
export type Grid = [Turn, Score];
export type Board = Grid[][];
export type Frozen = [Position, Position];
export type Game = { board: Board; frozen: Frozen };

export type Color = number;
export const COLOR_NONE: Color = 0;
export const COLOR_PUBLIC: Color = PUBLIC;
export const COLOR_RED: Color = RED;
export const COLOR_GREEN: Color = GREEN;
export const COLOR_RED_FROZEN: Color = 4;
export const COLOR_GREEN_FROZEN: Color = 5;
export const COLOR_AVAILABLE: Color = 6;
export const COLOR_UNAVAILABLE: Color = 7;

export type Hint = number;
export const HINT_NONE: Hint = 0;
export const HINT_SURROUNDED_BASE_CAMP: Hint = -ERR_SURROUNDED_BASE_CAMP;
export const HINT_TOO_MANY_SURROUNDED: Hint = -ERR_TOO_MANY_SURROUNDED;
export const HINT_FROZEN: Hint = -ERR_FROZEN;
export const HINT_NO_SURROUNDED: Hint = -ERR_NO_SURROUNDED;
export const HINT_AVAILABLE = 5;

export type RenderedGrid = {
  color: Color;
  hover: Color;
  score: Score;
  hint: Hint;
};
export type RenderedGame = RenderedGrid[][];

export type MessageType = "status" | "data" | "hint" | "chat" | "info";
export type User = { id: number; ws: ws; name: string };
export type Room = {
  game: Game;
  users: User[];
  idCount: number;
  currentTurn: Turn;
};
