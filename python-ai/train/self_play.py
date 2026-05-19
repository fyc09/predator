import os
import sys
import time
import argparse
from multiprocessing import Pool, cpu_count

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch
from torch import nn, optim

from game import core
from game.types import WIN_NONE, RED, GREEN, BOARD_SIZE
from model.encoder import encode
from model.network import PredatorNetwork
from mcts.mcts import MCTS


def play_game(network, device, mcts_iterations=400, temperature=1.0,
              game_idx=0, eval_mode="heuristic", step_limit=200, explore=0.25):
    game = core.init_game()
    turn = GREEN
    samples = []
    steps = 0

    while True:
        steps += 1
        mcts = MCTS(game, turn, network=network, device=device,
                    eval_mode=eval_mode, explore=explore)
        mcts.run(iterations=mcts_iterations)

        encoded = encode(game, turn)
        policy = mcts.get_policy(temperature=temperature)
        samples.append((encoded, policy, turn))

        move = mcts.select_move(temperature=temperature)
        game = core.handle_request(game, move, turn)
        turn = 5 - turn

        if steps % 20 == 0:
            print(f"    game {game_idx} step {steps} turn={5-turn} ...", flush=True)

        winner = core.check_win(game["board"])
        if winner != WIN_NONE:
            print(f"    game {game_idx} done in {steps} steps, winner={winner}", flush=True)
            break

        if steps > step_limit:
            winner = 0  # draw
            print(f"    game {game_idx} timeout at {steps} steps (limit={step_limit}), draw", flush=True)
            break

    training_data = []
    for encoded, policy, t in samples:
        if winner == 0:
            z = 0.0
        else:
            z = 1.0 if winner == t else -1.0
        training_data.append((encoded, policy, z))

    return training_data


def _play_worker(args):
    (state_dict, device_str, mcts_iterations, temperature,
     game_idx, eval_mode, step_limit, explore) = args
    import torch
    from model.network import PredatorNetwork
    net = PredatorNetwork(num_blocks=4, channels=32)
    net.load_state_dict(state_dict)
    net.eval()
    device = torch.device(device_str)
    return play_game(net, device, mcts_iterations, temperature,
                     game_idx, eval_mode, step_limit, explore)


def prepare_batch(batch, device):
    states = np.stack([s for s, _, _ in batch], axis=0)
    states = torch.from_numpy(states).float().permute(0, 3, 1, 2).to(device)

    target_policies = torch.from_numpy(
        np.stack([p for _, p, _ in batch], axis=0)
    ).float().to(device)

    target_values = torch.tensor(
        [z for _, _, z in batch], dtype=torch.float32, device=device
    )

    return states, target_policies, target_values


def train_step(network, batch, optimizer, device):
    states, target_policies, target_values = prepare_batch(batch, device)

    optimizer.zero_grad()
    policies, values = network(states)

    policy_loss = -torch.mean(
        torch.sum(target_policies * policies, dim=1)
    )
    value_loss = nn.MSELoss()(values.squeeze(1), target_values)
    loss = policy_loss + value_loss

    loss.backward()
    optimizer.step()

    return loss.item()


def main():
    parser = argparse.ArgumentParser(description="Predator Self-Play Training")
    parser.add_argument("--games", type=int, default=200, help="Self-play games per cycle")
    parser.add_argument("--iterations", type=int, default=200, help="MCTS iterations per move")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs per cycle")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--save", type=str, default="weights/latest.pt",
                        help="Path to save model weights")
    parser.add_argument("--load", type=str, default=None,
                        help="Path to load existing weights (auto-detected from --save if not set)")
    parser.add_argument("--cycles", type=int, default=5,
                        help="Number of self-play+train cycles")
    parser.add_argument("--workers", type=int, default=0,
                        help="Number of parallel self-play workers (0 = auto = cpu_count)")
    parser.add_argument("--eval-mode", choices=["nn", "heuristic"],
                        default="heuristic",
                        help="MCTS eval mode for self-play: nn or heuristic")
    parser.add_argument("--step-limit", type=int, default=200,
                        help="Max steps per game before draw (curriculum: start small, increase)")
    parser.add_argument("--explore", type=float, default=0.25,
                        help="Dirichlet noise at root for exploration (0=disabled)")
    parser.add_argument("--dataset-size", type=int, default=50000,
                        help="Max training samples to keep (oldest dropped)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    network = PredatorNetwork(num_blocks=4, channels=32).to(device)
    save_path = os.path.join(os.path.dirname(__file__), "..", args.save)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Auto-detect existing weights
    load_path = args.load or args.save
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "..", load_path)):
        load_path = None

    if load_path:
        full_path = os.path.join(os.path.dirname(__file__), "..", load_path)
        print(f"Loading weights from {full_path}")
        network.load(full_path, device)
    else:
        print("Starting with random weights")

    optimizer = optim.Adam(network.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.95)

    for cycle in range(args.cycles):
        print(f"\n{'='*50}")
        print(f"Cycle {cycle + 1}/{args.cycles} "
              f"(lr={optimizer.param_groups[0]['lr']:.6f}, "
              f"step_limit={args.step_limit}, explore={args.explore})")
        print(f"{'='*50}")

        # Self-play: fresh dataset per cycle (old data from weaker play discarded)
        n_workers = args.workers if args.workers > 0 else cpu_count()
        n_workers = min(n_workers, args.games)
        print(f"  Self-play with {n_workers} workers...")

        worker_args = [
            (network.state_dict(), str(device), args.iterations, 1.0,
             g + 1, args.eval_mode, args.step_limit, args.explore)
            for g in range(args.games)
        ]

        dataset = []
        with Pool(n_workers) as pool:
            for g, data in enumerate(pool.imap_unordered(_play_worker, worker_args)):
                dataset.extend(data)
                network.save(save_path)
                print(f"  Game {g + 1}/{args.games} ({len(data)} moves) "
                      f"total_samples={len(dataset)}", flush=True)

        # Cap dataset
        if len(dataset) > args.dataset_size:
            dataset = dataset[-args.dataset_size:]

        # Train
        print(f"\nTraining on {len(dataset)} samples...")
        for epoch in range(args.epochs):
            np.random.shuffle(dataset)
            total_loss = 0
            batches = 0

            for i in range(0, len(dataset), args.batch_size):
                batch = dataset[i:i + args.batch_size]
                loss = train_step(network, batch, optimizer, device)
                total_loss += loss
                batches += 1

            avg_loss = total_loss / batches
            print(f"  Epoch {epoch + 1}/{args.epochs}  loss={avg_loss:.4f}")

        scheduler.step()

        # Save
        network.save(save_path)
        print(f"Saved weights to {save_path}")

    print("\nTraining complete!")


if __name__ == "__main__":
    main()
