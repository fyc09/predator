"""
Predator 统一启动器
启动 Python AI 服务 + Node.js 后端
"""
import subprocess
import sys
import os
import signal
import time
import threading
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_AI_DIR = os.path.join(BASE_DIR, "python-ai")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")


def pipe_output(stream, prefix):
    for line in iter(stream.readline, ""):
        if line:
            print(f"[{prefix}] {line}", end="")
    stream.close()


def port_can_bind(port):
    for family, addr in [(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")]:
        s = socket.socket(family, socket.SOCK_STREAM)
        try:
            s.bind((addr, port))
            s.close()
        except:
            s.close()
            return False
    return True


def kill_port(port, wait=6):
    if sys.platform != "win32":
        return
    pids = set()
    result = subprocess.run(
        f"netstat -ano | findstr :{port}",
        shell=True, capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 5 and parts[-1] != "0":
            pids.add(parts[-1])
    for pid in pids:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    for i in range(wait):
        if port_can_bind(port):
            return
        time.sleep(1)
    print(f"  [WARN] port {port} still blocked after {wait}s")


def wait_proc(proc, timeout=1):
    try:
        proc.wait(timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        return False


def main():
    processes = []

    try:
        # Kill stale processes first
        print("=== Cleaning ports ===")
        kill_port(5000)
        kill_port(8000)
        time.sleep(1.5)

        # 1. Start Python AI service
        print("=== Starting Python AI service ===")
        p_python = subprocess.Popen(
            [sys.executable, "-u", "main.py"],
            cwd=PYTHON_AI_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(p_python)
        t = threading.Thread(
            target=pipe_output, args=(p_python.stdout, "AI"), daemon=True
        )
        t.start()

        # Wait for Python AI to be ready
        for i in range(10):
            if p_python.poll() is not None:
                print("[ERROR] Python AI service died on startup!")
                return
            try:
                s = socket.socket()
                s.settimeout(0.5)
                s.connect(("localhost", 5000))
                s.close()
                print("  Python AI ready")
                break
            except Exception:
                time.sleep(1)
        else:
            print("[ERROR] Python AI failed to start in time")
            return

        # 2. Start Node.js backend
        print("=== Starting Node.js backend ===")
        npx_cmd = "npx" if sys.platform != "win32" else "npx.cmd"
        p_node = subprocess.Popen(
            [npx_cmd, "ts-node", "src/index.ts"],
            cwd=BACKEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(p_node)
        t = threading.Thread(
            target=pipe_output, args=(p_node.stdout, "BE"), daemon=True
        )
        t.start()

        # Wait for backend to be ready
        for i in range(15):
            if p_node.poll() is not None:
                print("[ERROR] Node.js backend died on startup!")
                return
            try:
                s = socket.socket()
                s.settimeout(0.5)
                s.connect(("localhost", 8000))
                s.close()
                print("  Backend ready")
                break
            except Exception:
                time.sleep(1)
        else:
            print("[ERROR] Backend failed to start in time")
            return

        print("\n=== Both services running. Press Ctrl+C to stop. ===")

        # Wait for either to exit
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n=== Shutting down... ===")
    finally:
        for p in processes:
            if p.poll() is None:
                print(f"  stopping PID {p.pid}...")
                p.kill()
                p.wait(timeout=3)
        print("=== Done ===")


if __name__ == "__main__":
    main()
