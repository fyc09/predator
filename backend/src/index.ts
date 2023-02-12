import express from "express";
import expressWs from "express-ws";
import ws from "ws";
import { copyGame, handleRequest, initGame } from "./core.js";
import { renderGame } from "./renderer.js";
import { Game, PUBLIC, GREEN, RED, Turn, MessageType } from "./types.js";

const appBase = express();
const app = expressWs(appBase).app;

app.use(express.json());
app.use(express.static("./dist"));

let sessions: Map<string, Room> = new Map();

class Room {
  game: Game;
  green: Player;
  red: Player;
  _audiences: Audience[];
  currentTurn: Turn;
  idCount: number;
  roomId: string;

  constructor(roomId: string) {
    this.game = initGame(11, 11);
    this._audiences = [];
    this.currentTurn = GREEN;
    this.idCount = 0;
    this.roomId = roomId;
  }

  get audiences() {
    return this._audiences.filter((audience) => !audience.isDeleted);
  }

  addUser(ws: ws.WebSocket, room: Room) {
    if (this.green && this.red) {
      return this.addAudience(ws, room);
    } else {
      return this.addPlayer(ws, room);
    }
  }

  addAudience(ws: ws.WebSocket, room: Room): User {
    let id = this.idCount;
    this.idCount++;

    const user = new Audience(`au${id - 1}`, ws, room);
    this._audiences.push(user);
    user.sendMessage("data", renderGame(this.game, PUBLIC, this.currentTurn));
    user.sendMessage("info", {
      name: user.name,
      currentTurn: this.currentTurn,
      id,
    });
    user.sendMessage("status", 2);

    this.updateNames();
    return user;
  }

  addPlayer(ws: ws.WebSocket, room: Room): User {
    let id = this.idCount;
    this.idCount++;

    if (id == 0) {
      let red = new Player(`RED`, ws, room, RED);
      this.red = red;

      red.sendMessage("status", 1);
      red.sendMessage("hint", "请等待");
      return red;
    }

    let green = new Player(`GREEN`, ws, room, GREEN);
    this.green = green;
    let red = this.red;

    this.updateData();

    red.sendMessage("info", {
      name: red.name,
      names: [this.red.name, this.green.name],
      currentTurn: this.currentTurn,
      id,
    });
    red.sendMessage("status", 2);

    green.sendMessage("info", {
      name: green.name,
      names: [this.red.name, this.green.name],
      currentTurn: this.currentTurn,
      id: 0,
    });
    green.sendMessage("status", 2);

    return green;
  }

  updateData() {
    let publicBoard = renderGame(this.game, PUBLIC, this.currentTurn);
    this.audiences.forEach((target) => {
      target.sendMessage("data", publicBoard);
    });
    this.green.sendMessage(
      "data",
      renderGame(this.game, GREEN, this.currentTurn)
    );
    this.red.sendMessage("data", renderGame(this.game, RED, this.currentTurn));
  }

  updateNames() {
    let names: string[] = [this.red.name, this.green.name];
    names.push(...this.audiences.map((user) => user.name));
    this.audiences.forEach((target) => {
      target.sendMessage("info", { names });
    });
    this.red.sendMessage("info", { names });
    this.green.sendMessage("info", { names });
  }

  updateTurn() {
    let currentTurn = this.currentTurn;
    this.audiences.forEach((target) => {
      target.sendMessage("info", { currentTurn });
    });
    this.red.sendMessage("info", { currentTurn });
    this.green.sendMessage("info", { currentTurn });
  }

  updateMessages(message: string, name: string) {
    const data = {
      message: message,
      name: name,
    };
    this.audiences.forEach((target) => {
      target.sendMessage("chat", data);
    });
    this.green.sendMessage("chat", data);
    this.red.sendMessage("chat", data);
  }

  close() {
    const data = {
      name: "系统",
      message: "房间已关闭",
    };
    const OPEN = this.red.ws.OPEN;
    this.audiences.forEach((target) => {
      if (target.ws.readyState == OPEN) {
        target.sendMessage("chat", data);
        target.ws.close();
      }
    });
    if (this.red?.ws?.readyState == OPEN) {
      this.red.sendMessage("chat", data);
      this.red.ws.close();
    }
    if (this.green?.ws?.readyState == OPEN) {
      this.green.sendMessage("chat", data);
      this.green.ws.close();
    }
    sessions.delete(this.roomId);
  }
}

class User {
  ws: ws.WebSocket;
  name: string;
  room: Room;

  constructor(name: string, ws: ws.WebSocket, room: Room) {
    this.name = name;
    this.ws = ws;
    this.room = room;
  }

  sendMessage(type: MessageType, msg: any) {
    let data: any = { type };
    data.data = msg;
    this.ws.send(JSON.stringify(data));
  }

  handleClick(x: number, y: number): void {}

  handleMessage(message: string) {
    this.room.updateMessages(message, this.name);
  }

  handleName(name: string) {
    let ok = true;
    name = name.replace(/ \t\n\r/g, "");
    this.room.audiences.forEach((target) => {
      if (target.name == name) {
        ok = false;
      }
    });
    if (name.length == 0) {
      ok = false;
    }

    if (ok) {
      this.name = name;
      this.sendMessage("info", { name });
    }

    this.room.updateNames();
  }

  handleExit() {}
}

class Player extends User {
  turn: Turn;

  constructor(name: string, ws: ws.WebSocket, game: Room, turn: Turn) {
    super(name, ws, game);
    this.turn = turn;
  }

  handleClick(x: number, y: number) {
    if (this.turn != this.room.currentTurn) {
      return;
    }

    let result = handleRequest(copyGame(this.room.game), [x, y], this.turn);

    if (result < 0) {
      return;
    }

    this.room.game = result as Game;
    this.room.currentTurn = 5 - this.room.currentTurn;

    this.room.updateData();
    this.room.updateTurn();
  }

  handleExit() {
    this.room.close();
  }
}

class Audience extends User {
  isDeleted: boolean;

  constructor(name: string, ws: ws.WebSocket, room: Room) {
    super(name, ws, room);
    this.isDeleted = false;
  }

  handleExit() {
    this.isDeleted = true;
  }
}

class Connection {
  id: number;
  ws: ws.WebSocket;
  name: string;
  roomId: string;
  room: Room;
  user: User;

  constructor(ws: ws.WebSocket) {
    this.ws = ws;

    ws.on("message", (message) => this.handleMessage(message));

    ws.on("close", (e) => {
      if (this.user) {
        this.user.handleExit();
      }
      this.ws.close();
    });
  }

  handleMessage(message: any) {
    let data: any = JSON.parse(message.toString());

    switch (data.type) {
      case "apply":
        let roomId = (this.id = data.room);

        if (!sessions.has(roomId)) {
          this.room = new Room(roomId);
          sessions.set(roomId, this.room);
        }

        this.room = sessions.get(roomId);

        this.user = this.room.addUser(this.ws, this.room);
        break;

      case "click":
        if (this.user) {
          this.user.handleClick(data.x, data.y);
        }
        break;

      case "message":
        if (this.user) {
          this.user.handleMessage(data.message);
        }
        break;

      case "name":
        if (this.user) {
          this.user.handleName(data.name);
        }
        break;
    }
  }
}
app.ws("/ws", (ws, _req) => {
  new Connection(ws);
});

app.listen(8000, "localhost");
