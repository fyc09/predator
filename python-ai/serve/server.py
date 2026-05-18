import asyncio
import json
import websockets

from . import handler


async def handle_connection(websocket):
    print(f"[server] New connection")
    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
                req_id = msg.get("id")
                method = msg.get("method")
                params = msg.get("params", {})

                print(f"[server] Request: {method} (id={req_id})")

                result = await handler.handle(method, params)

                response = {"id": req_id, "result": result}
                await websocket.send(json.dumps(response))

                print(f"[server] Response sent for {method} (id={req_id})")

            except Exception as e:
                print(f"[server] Error: {e}")
                error_response = {
                    "id": msg.get("id", None),
                    "error": str(e),
                }
                await websocket.send(json.dumps(error_response))

    except websockets.exceptions.ConnectionClosed:
        print(f"[server] Connection closed")


async def start(host="localhost", port=5000, stop_future=None, max_retries=5):
    """
    Start WebSocket server with retry logic for port binding.
    On Windows, killed processes leave TIME_WAIT sockets; retry handles that.
    """
    for attempt in range(max_retries):
        try:
            print(f"[server] Starting AI server on ws://{host}:{port} (attempt {attempt+1})")
            async with websockets.serve(handle_connection, host, port):
                print(f"[server] AI server ready")
                await (stop_future or asyncio.Future())
            print(f"[server] Server stopped")
            return
        except OSError as e:
            if attempt < max_retries - 1:
                print(f"[server] Bind failed ({e}), retrying in {2 ** attempt}s...")
                await asyncio.sleep(2 ** attempt)  # exponential backoff: 1, 2, 4, 8s
            else:
                print(f"[server] Failed to bind after {max_retries} attempts: {e}")
                raise
