import WebSocket from "ws";
import debug from "debug";

const log = debug("predator:ai:bridge");

type Resolver = {
  resolve: (value: any) => void;
  reject: (reason: any) => void;
  timer: NodeJS.Timeout;
};

export class AIBridge {
  private ws: WebSocket | null = null;
  private pending = new Map<string, Resolver>();
  private reqId = 0;
  private _connected = false;
  private host: string;
  private port: number;

  constructor(host = "localhost", port = 5000) {
    this.host = host;
    this.port = port;
  }

  get connected(): boolean {
    return this._connected;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = `ws://${this.host}:${this.port}`;
      log("connecting to %s ...", url);

      const ws = new WebSocket(url);

      ws.on("open", () => {
        log("connected to Python AI service");
        this._connected = true;
        this.ws = ws;
        resolve();
      });

      ws.on("message", (data) => {
        const msg = JSON.parse(data.toString());
        const pending = this.pending.get(msg.id);
        if (pending) {
          clearTimeout(pending.timer);
          this.pending.delete(msg.id);
          if (msg.error) {
            pending.reject(new Error(msg.error));
          } else {
            pending.resolve(msg.result);
          }
        }
      });

      ws.on("close", () => {
        log("connection closed");
        this._connected = false;
        this.ws = null;
        this.rejectAll(new Error("AI bridge connection closed"));
      });

      ws.on("error", (err) => {
        log("connection error: %s", err.message);
        reject(err);
      });
    });
  }

  async request(method: string, params: any = {}, timeoutMs = 10000): Promise<any> {
    if (!this._connected || !this.ws) {
      throw new Error("AI bridge not connected");
    }

    const id = String(++this.reqId);
    const msg = JSON.stringify({ id, method, params });

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`AI request timeout: ${method}`));
      }, timeoutMs);

      this.pending.set(id, { resolve, reject, timer });
      this.ws!.send(msg);
    });
  }

  async getMove(
    board: any[][],
    frozen: number[][],
    turn: number
  ): Promise<[number, number] | null> {
    const result = await this.request("get_move", { board, frozen, turn });
    return result.move;
  }

  async getWinRates(
    board: any[][],
    frozen: number[][],
    turn: number
  ): Promise<Record<string, number>> {
    const result = await this.request("get_winrates", { board, frozen, turn });
    return result.winrates;
  }

  close(): void {
    this.rejectAll(new Error("AI bridge closing"));
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._connected = false;
  }

  private rejectAll(err: Error): void {
    for (const [id, { reject }] of this.pending) {
      reject(err);
    }
    this.pending.clear();
  }
}
