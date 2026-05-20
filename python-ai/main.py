import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(__file__))

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import asyncio
import signal
import torch
from serve.server import start
from serve import handler


async def async_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-mode", choices=["nn", "heuristic"],
                        default="heuristic",
                        help="nn=neural network, heuristic=distance-based")
    args = parser.parse_args()

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

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    handler.load_weights(device)
    t = time.time() - t0

    print(f"[main] Device: {device}  (load time: {t:.1f}s)")
    print(f"[main] Models: {handler.list_models()}")
    print("[main] Listening on ws://localhost:5000")
    print("==================================")

    await start(stop_future=stop)

    print("[main] Server stopped")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
