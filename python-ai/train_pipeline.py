"""
Predator 完整训练管线
自动分阶段执行，日志写入文件
"""
import subprocess
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "train.log")
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_phase(name, *args):
    log(f"\n{'='*60}")
    log(f"PHASE: {name}")
    log(f"{'='*60}")

    cmd = [sys.executable, "-u", "-m", "train.self_play"] + list(args)
    log(f"CMD: {' '.join(cmd)}")

    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        log_f.write(f"\n{'='*60}\nPHASE: {name}\nCMD: {' '.join(cmd)}\n{'='*60}\n")
        log_f.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in iter(proc.stdout.readline, ""):
            print(line, end="", flush=True)
            log_f.write(line)
            log_f.flush()

        proc.wait()
        if proc.returncode != 0:
            log(f"[FAIL] phase exited with code {proc.returncode}")
            return False

    log(f"[OK] phase complete")
    return True


def main():
    phases = [
        ("1a: heuristic step_limit=50",
         "--games", "30", "--iterations", "200", "--epochs", "30",
         "--batch-size", "64",
         "--step-limit", "50", "--cycles", "10",
         "--eval-mode", "heuristic",
         "--save", "weights/phase1a.pt"),

        ("1b: heuristic step_limit=100",
         "--games", "30", "--iterations", "200", "--epochs", "30",
         "--batch-size", "64",
         "--step-limit", "100", "--cycles", "10",
         "--eval-mode", "heuristic",
         "--load", "weights/phase1a.pt",
         "--save", "weights/phase1b.pt"),

        ("1c: heuristic step_limit=200",
         "--games", "30", "--iterations", "200", "--epochs", "30",
         "--batch-size", "64",
         "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "heuristic",
         "--load", "weights/phase1b.pt",
         "--save", "weights/phase1.pt"),

        ("2: nn self-play",
         "--games", "200", "--iterations", "800", "--epochs", "30",
         "--batch-size", "128",
         "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "nn",
         "--load", "weights/phase1.pt",
         "--save", "weights/latest.pt"),
    ]

    log(f"Predator Training Pipeline")
    log(f"Log file: {LOG_FILE}")
    log(f"Weights: {WEIGHTS_DIR}")
    log(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Predator Training Pipeline\n")
        f.write(f"Start: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Weights: {WEIGHTS_DIR}\n\n")

    total_start = time.time()

    for name, *args in phases:
        if not run_phase(name, *args):
            log("\n[ABORTED] training pipeline failed")
            sys.exit(1)

    total = time.time() - total_start
    hours = total // 3600
    minutes = (total % 3600) // 60
    log(f"\n{'='*60}")
    log(f"TRAINING COMPLETE")
    log(f"Total time: {int(hours)}h {int(minutes)}m")
    log(f"Final weights: {os.path.join(WEIGHTS_DIR, 'latest.pt')}")
    log(f"{'='*60}")


if __name__ == "__main__":
    main()
