"""
端到端测试：启动 Python AI + Node.js 后端，测试 AI 通信
"""
import subprocess
import sys
import os
import json
import time
import asyncio
import websockets
import socket
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")

_processes = []


def cleanup():
    for p in _processes:
        if p.poll() is None:
            print(f"  cleaning PID {p.pid}...")
            p.kill()
            try:
                p.wait(timeout=3)
            except:
                pass


def port_can_bind(port):
    """Check if port is free on both IPv4 (127.0.0.1) and IPv6 (::1) localhost."""
    for family, addr in [(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")]:
        s = socket.socket(family, socket.SOCK_STREAM)
        try:
            s.bind((addr, port))
            s.close()
        except:
            s.close()
            return False
    return True


def kill_port(port):
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

    if not pids:
        return

    for pid in pids:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        print(f"  killed PID {pid} on port {port}")

    for i in range(10):
        time.sleep(1)
        if port_can_bind(port):
            print(f"  port {port} is free")
            return

    print(f"  [WARN] port {port} still in TIME_WAIT after 10s, continuing anyway")


def _drain(stream):
    for line in iter(stream.readline, ""):
        pass


def start(cmd, cwd, name):
    use_shell = sys.platform == "win32" and any("npx" in c for c in cmd)
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=use_shell,
    )
    _processes.append(p)
    t = threading.Thread(target=_drain, args=(p.stdout,), daemon=True)
    t.start()
    return p


def read_all_output(p):
    """Read all remaining output from a dead process."""
    try:
        out, _ = p.communicate(timeout=2)
        return out
    except:
        return ""


async def wait_ws(uri, timeout=15):
    for i in range(timeout):
        try:
            ws = await websockets.connect(uri, open_timeout=2)
            return ws
        except:
            await asyncio.sleep(1)
    return None


async def test():
    print("=" * 50)
    print("Predator E2E Test")
    print("=" * 50)

    # Clean ports first
    print("\n[setup] Cleaning ports...")
    kill_port(5000)
    kill_port(8000)
    await asyncio.sleep(1)

    # Start Python AI
    print("\n[setup] Starting Python AI service...")
    p_ai = start([sys.executable, "-u", "main.py"], BASE_DIR, "Python AI")
    await asyncio.sleep(2)

    if p_ai.poll() is not None:
        out = read_all_output(p_ai)
        print(f"[FAIL] Python AI died immediately. Output:\n{out}")
        return False

    # Start Node.js backend
    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
    print(f"[setup] Starting Node.js backend ({npx_cmd})...")
    p_node = start([npx_cmd, "ts-node", "src/index.ts"], BACKEND_DIR, "Backend")

    # Wait for backend to be ready
    backend_ready = False
    for i in range(20):
        if p_node.poll() is not None:
            out = read_all_output(p_node)
            print(f"[FAIL] Node.js backend died. Output:\n{out}")
            return False
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect(("127.0.0.1", 8000))
            s.close()
            backend_ready = True
            print(f"  Backend ready after {i+1}s")
            break
        except:
            await asyncio.sleep(1)

    if not backend_ready:
        print("[FAIL] Node.js backend not ready after 20s")
        if p_node.poll() is not None:
            out = read_all_output(p_node)
            print(f"  Process died. Output:\n{out}")
        return False

    # 1. Test Python AI ping
    print("\n[test 1] Python AI ping...")
    try:
        async with websockets.connect("ws://localhost:5000", open_timeout=5) as ws:
            await ws.send(json.dumps({"id": "1", "method": "ping", "params": {}}))
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            assert resp["result"] == "pong"
            print("  ✓ Python AI responds to ping")
    except Exception as e:
        print(f"  ✗ Python AI ping failed: {e}")
        return False

    # 2. Test Python AI get_move
    print("\n[test 2] Python AI get_move...")
    try:
        async with websockets.connect("ws://localhost:5000", open_timeout=5) as ws:
            board = [[[1, 0] for _ in range(11)] for _ in range(11)]
            board[0][0] = [2, 5]
            board[10][10] = [3, 5]
            frozen = [[-1, -1], [-1, -1]]

            await ws.send(json.dumps({
                "id": "2", "method": "get_move",
                "params": {"board": board, "frozen": frozen, "turn": 3},
            }))
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            move = resp["result"]["move"]
            assert move is not None and len(move) == 2
            print(f"  ✓ AI returned move: {move}")
    except Exception as e:
        print(f"  ✗ get_move failed: {e}")
        return False

    # 3. Test backend AI mode
    print("\n[test 3] Backend AI mode...")
    try:
        ws = await wait_ws("ws://127.0.0.1:8000/ws", timeout=10)
        if ws is None:
            if p_node.poll() is not None:
                out = read_all_output(p_node)
                print(f"[FAIL] Backend died. Output:\n{out}")
            else:
                print("[FAIL] Could not connect to backend (timeout)")
            return False

        print("  ✓ Connected to backend")

        await ws.send(json.dumps({"type": "single:ai"}))

        ai_confirmed = False
        got_data = False
        while True:
            try:
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            except asyncio.TimeoutError:
                break  # no more messages

            if resp["type"] == "status":
                assert resp["data"] == 2, f"expected status 2, got {resp['data']}"
                print("  ✓ Got status=2")
            elif resp["type"] == "info":
                if resp["data"].get("ai"):
                    ai_confirmed = True
                    print(f"  ✓ AI mode confirmed (humanTurn={resp['data'].get('humanTurn')})")
                else:
                    print(f"  info: {resp['data']}")
            elif resp["type"] == "data":
                got_data = True
                dlen = len(resp["data"])
                print(f"  ✓ Board data received ({dlen}×{len(resp['data'][0]) if dlen else 0})")

        assert ai_confirmed, "AI mode flag not received"
        assert got_data, "Board data not received"
        print("  ✓ AI mode fully verified")
        await ws.close()

    except Exception as e:
        print(f"  ✗ Backend AI mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)
    return True


async def main():
    success = False
    try:
        success = await test()
    finally:
        cleanup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
