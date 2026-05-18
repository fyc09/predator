# Python AI 服务计划

## 整体架构

```
┌─────────────────┐    WebSocket    ┌─────────────────────────┐
│  Node.js 后端    │ ◄─────────────► │  Python AI 服务          │
│  (index.ts)      │   JSON RPC     │  (websockets + PyTorch)  │
│                  │   localhost:5000│                          │
│  AIBridge.ts ◄───┤                │  server.py ←→ handler.py │
│  (RPC 客户端)    │                │       ↓                  │
│                  │                │  mcts.py ←→ network.py   │
│  Vite 前端 ◄─────┤                │       ↓                  │
│  (Vue 3)         │                │  game/core.py (游戏逻辑)  │
└─────────────────┘                └─────────────────────────┘
```

通信方式：Node.js 作为 WebSocket 客户端连接 Python 服务端（`ws://localhost:5000`），采用请求-响应模式。

## 两阶段实施

### 阶段 1：建立连接 + 随机 AI（当前）

目标：跑通端到端流程。

**Python 侧：**
- `main.py` — 入口，启动 WebSocket 服务
- `game/types.py` — 游戏常量
- `game/core.py` — 游戏逻辑移植（`get_legal_moves` 等）
- `ai/random.py` — 随机 AI：从合法走法中随机选一个
- `serve/server.py` — WebSocket RPC 服务端

**Node.js 侧：**
- `backend/src/ai/bridge.ts` — WebSocket RPC 客户端
- `backend/src/index.ts` — 新增 `AIRoom` 类 + `single:ai` 消息

**前端：**
- `Home.vue` — "人机模式"按钮
- `Game.vue` — 处理 AI 模式状态

### 阶段 2：神经网络 + MCTS

目标：达到 KataGo 式持续计算、超越人类水平。

**Python 侧新增：**
- `model/encoder.py` — 棋盘 → 张量（9 通道编码）
- `model/network.py` — PyTorch 网络（ResBlock × 6 + Policy/Value head）
- `mcts/mcts.py` — MCTS 核心（PUCT 算法）
- `train/self_play.py` — 自我对弈训练管线

**Node.js 侧新增：**
- `bridge.ts` 增加 `ponder_start` / `ponder_update` / `ponder_stop` 方法
- 作弊模式：前端轮询胜率显示

---

## 通信协议

所有消息为 JSON 格式，`id` 字段用于匹配请求和响应。

### 请求格式
```json
{"id": "1", "method": "get_move", "params": { "board": [...], "frozen": [...], "turn": 2 }}
```

### 响应格式
```json
{"id": "1", "result": { "move": [3, 5] }}
```

### 方法列表

| 方法 | 阶段 | 说明 |
|------|------|------|
| `get_move` | 1→2 | 给定局面，返回最佳走法 + 胜率 |
| `get_winrates` | 2 | 返回所有格子的胜率（作弊模式） |
| `ponder_start` | 2 | 开始后台持续搜索 |
| `ponder_update` | 2 | 获取当前胜率（作弊模式轮询） |
| `ponder_stop` | 2 | 人类落子后，更新 MCTS 根节点 |

---

## 神经网络设计（阶段 2）

### 输入编码（11×11×9）

| 通道 | 内容 | 类型 |
|------|------|------|
| 0 | 己方位置 | 二值 |
| 1 | 对方位置 | 二值 |
| 2 | 公共格子 | 二值 |
| 3 | 己方分数 | 归一化 /10 |
| 4 | 对方分数 | 归一化 /10 |
| 5 | 己方冻结位置 | 二值 |
| 6 | 对方冻结位置 | 二值 |
| 7 | 己方大本营 | 二值 |
| 8 | 对方大本营 | 二值 |

### 网络架构

```
Input (11, 11, 9)
  ↓ Conv2d(3×3, 9→64) → BatchNorm → ReLU
  ↓ ResBlock × 6
     ┌─ Conv2d(3×3, 64→64) → BN → ReLU
     └─ Conv2d(3×3, 64→64) → BN → +skip → ReLU
  ↓
┌─ Policy Head ──┐  ┌─ Value Head ─────────┐
│ Conv1×1 64→32  │  │ Conv1×1 64→32        │
│ Flatten        │  │ Flatten              │
│ Linear → 121   │  │ Linear → 64 → ReLU   │
│ Softmax        │  │ Linear → 1 → Tanh    │
└────────────────┘  └──────────────────────┘
```

- 输出 1: Policy（121 维，每个格子一步的概率）
- 输出 2: Value（1 维，当前玩家胜率，[-1, 1]）

### 训练

- 自我对弈生成 (state, π_mcts, z) 三元组
- Loss = cross_entropy(π, π_mcts) + 0.5 × MSE(v, z) + L2 regularization
- 每 N 局自我对弈后训练一次

---

## MCTS（阶段 2）

标准 AlphaGo Zero 风格：

```
一次迭代:
  1. Select: 沿 PUCT 公式选择子节点
     score = Q(s,a) + c_puct * P(s,a) * sqrt(ΣN) / (1 + N(s,a))
  2. Expand: 到达叶节点时展开所有合法走法
  3. Evaluate: 神经网络预测 value + 新节点的先验概率
  4. Backpropagate: 沿路径回传 value
  
ponder 模式:
  - 人类回合时持续运行 MCTS
  - 每次迭代后可查询最新胜率
  - 人类落子后回收 MCTS 子树（不从头开始）
```

---

## 训练循环（阶段 2）

```
while True:
    # 自我对弈
    game_data = []
    while not game_over:
        move = mcts_search(game, network)
        game_data.append((game, mcts_policy, None))
        game = apply_move(game, move)
    
    # 标记结果
    for d in game_data:
        d[2] = +1 if winner == d[0].current_turn else -1
    
    # 训练
    dataset.add(game_data)
    if len(dataset) > batch_size:
        network.train(dataset.sample(batch_size))
    
    # 保存权重
    torch.save(network.state_dict(), "weights/latest.pt")
```

---

## 文件结构最终形态

```
python-ai/
├── main.py                  # 入口
├── requirements.txt
├── PLAN.md
├── game/
│   ├── __init__.py
│   ├── types.py             # 常量
│   └── core.py              # 游戏逻辑
├── ai/
│   ├── __init__.py
│   └── random.py            # 随机 AI（阶段 1）
├── serve/
│   ├── __init__.py
│   ├── server.py            # WebSocket RPC 服务
│   └── handler.py           # 方法分发
├── model/                   # 阶段 2
│   ├── __init__.py
│   ├── encoder.py
│   └── network.py
├── mcts/                    # 阶段 2
│   ├── __init__.py
│   └── mcts.py
├── train/                   # 阶段 2
│   ├── __init__.py
│   └── self_play.py
└── weights/                 # 模型权重（gitignored）
    └── .gitkeep
```
