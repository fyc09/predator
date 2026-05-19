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

        env = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}
        proc = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
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
        ("1: heuristic 10 cycles",
         "--games", "30", "--iterations", "400", "--epochs", "30",
         "--batch-size", "64", "--step-limit", "100", "--cycles", "10",
         "--eval-mode", "heuristic", "--explore", "0.25",
         "--load", "weights/phase1.pt",
         "--save", "weights/phase1.pt"),

        ("2a: nn cycles 1-10",
         "--games", "50", "--iterations", "600", "--epochs", "30",
         "--batch-size", "64", "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "nn", "--explore", "0.25",
         "--load", "weights/phase1.pt",
         "--save", "weights/phase2_c10.pt"),

        ("2b: nn cycles 11-20",
         "--games", "50", "--iterations", "600", "--epochs", "30",
         "--batch-size", "64", "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "nn", "--explore", "0.25",
         "--load", "weights/phase2_c10.pt",
         "--save", "weights/phase2_c20.pt"),

        ("2c: nn cycles 21-30",
         "--games", "50", "--iterations", "600", "--epochs", "30",
         "--batch-size", "64", "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "nn", "--explore", "0.25",
         "--load", "weights/phase2_c20.pt",
         "--save", "weights/phase2_c30.pt"),

        ("2d: nn cycles 31-40",
         "--games", "50", "--iterations", "600", "--epochs", "30",
         "--batch-size", "64", "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "nn", "--explore", "0.25",
         "--load", "weights/phase2_c30.pt",
         "--save", "weights/phase2_c40.pt"),

        ("2e: nn cycles 41-50",
         "--games", "50", "--iterations", "600", "--epochs", "30",
         "--batch-size", "64", "--step-limit", "200", "--cycles", "10",
         "--eval-mode", "nn", "--explore", "0.25",
         "--load", "weights/phase2_c40.pt",
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
