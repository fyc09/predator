import express from "express";
import expressWs from "express-ws";
import ws from "ws";
import { copyGame, handleRequest, initGame } from "./core";
import { renderGame } from "./renderer";
import { Game, PUBLIC, GREEN, RED, Turn, MessageType } from "./types";

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

  addUser(connection: Connection, room: Room) {
    if (this.green && this.red) {
      return this.addAudience(connection, room);
    } else {
      return this.addPlayer(connection, room);
    }
  }

  addAudience(connection: Connection, room: Room): User {
    let id = this.idCount;
    this.idCount++;

    const user = new Audience(`user-${id + 1}`, connection, room);
    this._audiences.push(user);
    user.sendMessage("data", renderGame(this.game, PUBLIC, this.currentTurn));
    user.sendMessage("info", {
      name: user.name,
      currentTurn: this.currentTurn,
      id,
      isPlayer: false,
    });
    user.sendMessage("status", 2);

    this.updateNames();
    return user;
  }

  addPlayer(connection: Connection, room: Room): User {
    let id = this.idCount;
    this.idCount++;

    if (id == 0) {
      let red = new Player(`user-${id + 1}`, connection, room, RED);
      this.red = red;

      red.sendMessage("status", 1);
      red.sendMessage("hint", "请等待");
      return red;
    }

    let green = new Player(`user-${id + 1}`, connection, room, GREEN);
    this.green = green;
    let red = this.red;

    this.updateData();

    red.sendMessage("info", {
      name: red.name,
      names: [this.red.name, this.green.name],
      currentTurn: this.currentTurn,
      id,
      isPlayer: true,
    });
    red.sendMessage("status", 2);

    green.sendMessage("info", {
      name: green.name,
      names: [this.red.name, this.green.name],
      currentTurn: this.currentTurn,
      id: 0,
      isPlayer: true,
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

  change(turn: Turn, audienceId: number) {
    let player: Player;
    let audience: Audience;

    if (turn === GREEN) {
      player = this.green;
      audience = this.audiences[audienceId];
      audience.connection.user = this.green = new Player(
        audience.name,
        audience.connection,
        player.room,
        GREEN
      );
    } else {
      player = this.red;
      audience = this.audiences[audienceId];
      audience.connection.user = this.red = new Player(
        audience.name,
        audience.connection,
        player.room,
        RED
      );
    }

    player.connection.user = this._audiences[audienceId] = new Audience(
      player.name,
      player.connection,
      player.room
    );

    this.updateData();
    this.updateNames();

    player.sendMessage("info", { isPlayer: false });
    audience.sendMessage("info", { isPlayer: true });
  }

  close() {
    const data = {
      name: "系统",
      message: "房间已关闭",
    };
    const OPEN = this.red.connection.ws.OPEN;
    this.audiences.forEach((target) => {
      if (target.connection.ws.readyState == OPEN) {
        target.sendMessage("chat", data);
        target.connection.ws.close();
      }
    });
    if (this.red?.connection?.ws?.readyState == OPEN) {
      this.red.sendMessage("chat", data);
      this.red.connection.ws.close();
    }
    if (this.green?.connection?.ws?.readyState == OPEN) {
      this.green.sendMessage("chat", data);
      this.green.connection.ws.close();
    }
    sessions.delete(this.roomId);
  }
}

class User {
  connection: Connection;
  name: string;
  room: Room;

  constructor(name: string, connection: Connection, room: Room) {
    this.name = name;
    this.connection = connection;
    this.room = room;
  }

  sendMessage(type: MessageType, msg: any) {
    let data: any = { type };
    data.data = msg;
    this.connection.ws.send(JSON.stringify(data));
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

  handleHandin(id: string) {}
  handleExit() {}
}

class Player extends User {
  turn: Turn;

  constructor(name: string, connection: Connection, room: Room, turn: Turn) {
    super(name, connection, room);
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

  handleHandin(id: string) {
    if (id === "GREEN" || id === "RED") {
      return;
    }
    const audienceId = Number(id);
    if (isNaN(audienceId)) {
      return;
    }

    this.room.change(this.turn, audienceId);
  }

  handleExit() {
    this.room.close();
  }
}

class Audience extends User {
  isDeleted: boolean;

  constructor(name: string, connection: Connection, room: Room) {
    super(name, connection, room);
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

        this.user = this.room.addUser(this, this.room);
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

      case "handin":
        if (this.user) {
          this.user.handleHandin(data.id);
        }
        break;
    }
  }
}

app.ws("/ws", (ws, _req) => {
  new Connection(ws);
});

app.listen(8000, "localhost");
