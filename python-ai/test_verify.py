"""验证启发式修复效果：AI 是否优先扩张而非回血"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from game import core
from game.types import *
from game.core import copy_game, handle_request
from mcts.mcts import MCTS

game = core.init_game()
turn = 3
occupy_count = 0
heal_count = 0

for step in range(40):
    mcts = MCTS(game, turn, eval_mode="heuristic")
    mcts.run(iterations=100)
    best = mcts.get_best_move()
    b = game["board"]
    if b[best[0]][best[1]][0] != turn:
        occupy_count += 1
        mtype = "OCCUPY"
    else:
        heal_count += 1
        mtype = "HEAL"
    territory = sum(1 for r in b for c in r if c[0] == turn)
    print(f"step {step+1:2d} | {mtype:6s} | cell={best} | territory={territory}")
    game = handle_request(game, best, turn)
    turn = 5 - turn
    if core.check_win(game["board"]) != WIN_NONE:
        print(f">>> WINNER: {core.check_win(b)}")
        break

print(f"\nOCCUPY={occupy_count}  HEAL={heal_count}")
