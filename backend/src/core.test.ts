import { initGame, copyGame, handleRequest, isReachable } from "./core";
import {
  Game,
  RED,
  PUBLIC,
  GREEN,
  ERR_FROZEN,
  ERR_SURROUNDED_BASE_CAMP,
  ERR_NO_SURROUNDED,
} from "./types";

const sample: Game = {
  board: [
    [
      [RED, 5],
      [PUBLIC, 0],
      [PUBLIC, 0],
      [PUBLIC, 0],
    ],
    [
      [PUBLIC, 0],
      [RED, 5],
      [PUBLIC, 0],
      [PUBLIC, 0],
    ],
    [
      [PUBLIC, 0],
      [RED, 0],
      [GREEN, 4],
      [PUBLIC, 0],
    ],
    [
      [PUBLIC, 0],
      [GREEN, 5],
      [GREEN, 5],
      [GREEN, 5],
    ],
  ],
  frozen: [
    [3, 2],
    [-1, -1],
  ],
};

test("test init_game", () => {
  expect(initGame(3, 3)).toEqual({
    board: [
      [
        [2, 6],
        [1, 0],
        [1, 0],
      ],
      [
        [1, 0],
        [1, 0],
        [1, 0],
      ],
      [
        [1, 0],
        [1, 0],
        [3, 6],
      ],
    ],
    frozen: [
      [-1, -1],
      [-1, -1],
    ],
  });
});

test("test copy_game", () => {
  expect(copyGame(sample)).toEqual(sample);
  expect(copyGame(sample)).not.toBe(sample);
});

describe("test handle_request", () => {
  describe("error cases", () => {
    test("returns ERR_FROZEN", () => {
      expect(handleRequest(copyGame(sample), [3, 2], GREEN)).toBe(ERR_FROZEN);
    });

    test("returns ERR_SURROUNDED_BASE_CAMP", () => {
      expect(handleRequest(copyGame(sample), [2, 3], GREEN)).toBe(
        ERR_SURROUNDED_BASE_CAMP
      );
    });

    test("returns ERR_DISCONNECTED_FROM_BASE_CAMP", () => {
      expect(handleRequest(copyGame(sample), [1, 0], GREEN)).toBe(
        ERR_NO_SURROUNDED
      );
    });

    test("returns ERR_NO_SURROUNDED", () => {
      expect(handleRequest(copyGame(sample), [0, 0], GREEN)).toBe(
        ERR_NO_SURROUNDED
      );
    });

    test("throws unknown turn", () => {
      expect(() => {
        handleRequest(copyGame(sample), [1, 0], 9);
      }).toThrow(Error);
    });
  });

  describe("normal cases", () => {
    test("with frozen", () => {
      let exp = copyGame(sample);
      exp.board[2][2][1]++;
      exp.frozen = [
        [-1, -1],
        [2, 2],
      ];
      expect(handleRequest(copyGame(sample), [2, 2], GREEN)).toEqual(exp);
    });

    test("without frozen", () => {
      let exp = copyGame(sample);
      exp.board[0][1] = [RED, 6];
      exp.frozen = [
        [-1, -1],
        [-1, -1],
      ];
      expect(handleRequest(copyGame(sample), [0, 1], RED)).toEqual(exp);
    });

    test("hit other", () => {
      let exp = copyGame(sample);
      exp.board[1][1] = [RED, 4];
      exp.frozen = [
        [-1, -1],
        [1, 1],
      ];
      expect(handleRequest(copyGame(sample), [1, 1], GREEN)).toEqual(exp);
    });

    test("disconnect", () => {
      let inp = copyGame(sample);
      inp.board[3][2][1] = 0;
      inp.board[2][2] = [PUBLIC, 0];
      inp.frozen = [
        [-1, -1],
        [-1, -1],
      ];

      let exp = copyGame(inp);
      exp.board[3][2] = [RED, 4];
      exp.board[3][1] = [PUBLIC, 0];
      exp.frozen = [
        [-1, -1],
        [3, 2],
      ];
      expect(handleRequest(copyGame(inp), [3, 2], RED)).toEqual(exp);
    });

    describe("surround many", () => {
      const new_sample: Game = {
        board: [
          [
            [RED, 5],
            [PUBLIC, 0],
            [PUBLIC, 0],
            [PUBLIC, 0],
          ],
          [
            [PUBLIC, 0],
            [RED, 5],
            [GREEN, 5],
            [PUBLIC, 0],
          ],
          [
            [RED, 5],
            [GREEN, 5],
            [GREEN, 5],
            [PUBLIC, 0],
          ],
          [
            [PUBLIC, 0],
            [GREEN, 5],
            [GREEN, 5],
            [GREEN, 5],
          ],
        ],
        frozen: [
          [3, 2],
          [-1, -1],
        ],
      };

      test("hit", () => {
        let inp = copyGame(new_sample);
        inp.board[2][1][0] = RED;

        let exp = copyGame(inp);
        exp.board[2][1][1] = 3;
        exp.frozen = [
          [-1, -1],
          [2, 1],
        ];
        expect(handleRequest(copyGame(inp), [2, 1], GREEN)).toEqual(exp);
      });

      test("save", () => {
        let exp = copyGame(new_sample);
        exp.board[2][1] = [GREEN, 7];
        exp.frozen = [
          [-1, -1],
          [2, 1],
        ];
        expect(handleRequest(copyGame(new_sample), [2, 1], GREEN)).toEqual(exp);
      });
    });

    test("input PUBLIC", () => {
      expect(handleRequest(copyGame(sample), [1, 0], PUBLIC)).toEqual(sample);
    });
  });
});

describe("test is_reachable", () => {
  test("simple", () => {
    expect(isReachable(sample.board, GREEN, [3, 3], [[2, 2]])).toBe(true);
  });

  test("1 to more", () => {
    expect(
      isReachable(
        sample.board,
        GREEN,
        [3, 3],
        [
          [2, 2],
          [3, 1],
        ]
      )
    ).toBe(true);
  });

  test("complex", () => {
    expect(isReachable(sample.board, GREEN, [3, 3], [[3, 0]])).toBe(true);
  });
});
