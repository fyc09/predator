import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import asyncio
import signal
import torch
from serve.server import start
from serve import handler
from model.network import PredatorNetwork

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "weights", "latest.pt")


def load_network():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[main] Device: {device}")

    network = PredatorNetwork(num_blocks=4, channels=32)

    if os.path.exists(WEIGHTS_PATH):
        print(f"[main] Loading weights from {WEIGHTS_PATH}")
        network.load(WEIGHTS_PATH, device)
        network.to(device)
        network.eval()
        print("[main] Network loaded successfully")
        return network, device
    else:
        print(f"[main] No weights found at {WEIGHTS_PATH}")
        print(f"[main] Starting with random weights (AI will play poorly)")
        print(f"[main] Run 'python -m train.self_play' to train")
        network.to(device)
        network.eval()
        return network, device


async def async_main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def on_sigterm():
        print("\n[main] SIGTERM received, shutting down...")
        stop.set_result(None)

    try:
        loop.add_signal_handler(signal.SIGTERM, on_sigterm)
        loop.add_signal_handler(signal.SIGINT, on_sigterm)
    except NotImplementedError:
        pass

    print("=== Predator Python AI Service ===")

    t0 = time.time()
    network, device = load_network()
    handler.set_network(network, device)
    t = time.time() - t0

    if torch.cuda.is_available():
        print(f"[main] Using CUDA GPU (load time: {t:.1f}s)")
    else:
        print(f"[main] Using CPU (load time: {t:.1f}s)")

    print("[main] Listening on ws://localhost:5000")
    print("==================================")

    await start(stop_future=stop)

    print("[main] Server stopped")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
