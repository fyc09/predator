import { randomUUID } from "crypto";
import EventEmitter from "events";
import express from "express";
import expressWs from "express-ws";
import ws from "ws";
import { copyGame, handleRequest, initGame } from "./core";
import { renderGame } from "./renderer";
import {
  Game,
  PUBLIC,
  GREEN,
  RED,
  Turn,
  MessageType,
  updateDataEvent,
  updateNamesEvent,
  updateTurnEvent,
  updateMessageEvent,
  Level,
} from "./types";

console.clear();

const appBase = express();
const app = expressWs(appBase).app;

app.use(express.json());
app.use(express.static("./dist"));

let sessions: Map<string, Room> = new Map();

class Room extends EventEmitter {
  game: Game;
  green: Player;
  red: Player;
  _audiences: Audience[];
  currentTurn: Turn;
  idCount: number;
  roomId: string;

  constructor(roomId: string) {
    super();
    this.game = initGame(11, 11);
    this._audiences = [];
    this.currentTurn = GREEN;
    this.idCount = 0;
    this.roomId = roomId;

    this.on(updateDataEvent, this._updateData);
    this.on(updateNamesEvent, this._updateNames);
    this.on(updateTurnEvent, this._updateTurn);
    this.on(updateMessageEvent, this._updateMessages);
  }

  get audiences() {
    return this._audiences.filter((audience) => !audience.isDeleted);
  }

  addUser(connection: Connection, room: Room): User {
    if (this.green && this.red) {
      return this._addAudience(connection, room);
    } else {
      return this._addPlayer(connection, room);
    }
  }

  _addAudience(connection: Connection, room: Room): Audience {
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

    this.emit(updateNamesEvent);
    return user;
  }

  _addPlayer(connection: Connection, room: Room): Player {
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

    this._updateData();

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

  _updateData() {
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

  _updateNames() {
    let names: string[] = [this.red.name, this.green.name];
    names.push(...this.audiences.map((user) => user.name));

    this.audiences.forEach((target) => {
      target.sendMessage("info", { names });
    });
    this.red.sendMessage("info", { names });
    this.green.sendMessage("info", { names });
  }

  _updateTurn() {
    let currentTurn = this.currentTurn;
    this.audiences.forEach((target) => {
      target.sendMessage("info", { currentTurn });
    });
    this.red.sendMessage("info", { currentTurn });
    this.green.sendMessage("info", { currentTurn });
  }

  _updateMessages(message: string, name: string): void {
    this.audiences.forEach((target) => {
      target.messsage(name, message);
    });
    this.green.messsage(name, message);
    this.red.messsage(name, message);
  }

  change(turn: Turn, audienceId: number): void {
    let player: Player;
    let audience: Audience;

    if (turn === GREEN) {
      player = this.green;
      audience = this.audiences[audienceId];
      if (audience.isAdmin) {
        player.sendMessage("chat", {
          message: "该用户是管理员，无法交接",
          name: "系统",
        });
        return;
      }

      audience.connection.user = this.green = new Player(
        audience.name,
        audience.connection,
        player.room,
        GREEN
      );
    } else {
      player = this.red;
      audience = this.audiences[audienceId];
      if (audience.isAdmin) {
        player.sendMessage("chat", {
          message: "该用户是管理员，无法交接",
          name: "系统",
        });
        return;
      }

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

    this.emit(updateDataEvent);
    this.emit(updateNamesEvent);

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
      if (target.connection.ws.readyState == OPEN && !target.isAdmin) {
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

  sendMessage(type: MessageType, msg: any): void {
    let data: any = { type };
    data.data = msg;
    this.connection.ws.send(JSON.stringify(data));
  }

  messsage(name: string, message: string) {
    this.sendMessage("chat", { name, message });
  }

  handleClick(x: number, y: number): void {}

  handleMessage(message: string): void {
    this.room.emit(updateMessageEvent, message, this.name);
  }

  handleName(name: string): void {
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

    this.room.emit(updateNamesEvent);
  }

  handleHandin(id: string): void {}
  handleExit(): void {}
}

class Player extends User {
  turn: Turn;

  constructor(name: string, connection: Connection, room: Room, turn: Turn) {
    super(name, connection, room);
    this.turn = turn;
  }

  handleClick(x: number, y: number): void {
    if (this.turn != this.room.currentTurn) {
      return;
    }

    let result = handleRequest(copyGame(this.room.game), [x, y], this.turn);

    if (result < 0) {
      return;
    }

    this.room.game = result as Game;
    this.room.currentTurn = 5 - this.room.currentTurn;

    this.room.emit(updateDataEvent);
    this.room.emit(updateDataEvent);
  }

  handleHandin(id: string): void {
    if (id === "GREEN" || id === "RED") {
      return;
    }
    const audienceId = Number(id);
    if (isNaN(audienceId)) {
      return;
    }

    this.room.change(this.turn, audienceId);
  }

  handleExit(): void {
    this.room.close();
  }
}

class Audience extends User {
  isDeleted: boolean;
  isAdmin: boolean;

  constructor(name: string, connection: Connection, room: Room) {
    super(name, connection, room);
    this.isDeleted = false;
  }

  handleExit() {
    this.isDeleted = true;
  }
}

class Admin extends Audience {
  methods: any;
  eventListeners: [EventEmitter, symbol, (...args: any[]) => void][];
  user: Audience;

  constructor(connection: Connection) {
    super("Admin", connection, undefined);

    this.sendMessage("status", 2);
    this.sendMessage("data", {});
    this.sendMessage("info", { names: [] });
    this.message("info", "Welcome to administrators' command line!");

    this.methods = {
      ping(this: Admin, ...args: string[]): void {
        this.message("info", "pong");
        for (let arg of args) {
          this.message("info", arg);
        }
      },
      ls(this: Admin): void {
        for (let roomid of sessions.keys()) {
          this.message("info", `room - ${roomid}`);
        }
        if (!this.room) {
          return;
        }

        this.message("info", `users:`);
        let users: User[] = [
          ...this.room.audiences,
          this.room.red,
          this.room.green,
        ];

        for (let id in users) {
          let audience = users[id];
          this.message(
            "info",
            `user - ${id} - ${audience.name} - ${audience.connection.ip}`
          );
        }
      },

      enter(this: Admin, roomid: string): void {
        this.message("info", `entering ${roomid}`);
        let room = sessions.get(roomid);
        if (room === undefined) {
          this.message("error", `room not found`);
          return;
        }
        this.user = room._addAudience(this.connection, room);
        this.room = room;
        this.user.isAdmin = true;
        this.message("info", `entered`);
      },
      exit(this: Admin): void {
        this.message("info", `exit`);
        this.sendMessage("data", {});
        this.sendMessage("info", { names: [] });
        this.user.handleExit();
        this.user = undefined;
        this.message("info", `exited`);
      },
      close(this: Admin): void {
        this.message("info", `closing`);
        this.sendMessage("data", {});
        this.sendMessage("info", { names: [] });
        this.room.close();
        this.user = undefined;
        this.message("info", `closed`);
      },
      send(this: Admin, name: string, message: string): void {
        this.message("info", `sending ${message}`);
        this.room._updateMessages(message, name);
        this.message("info", `sent`);
      },
      delete(this: Admin, _id: string): void {
        let id: number = Number(_id);
        if (isNaN(id)) {
          this.message("error", "Unknown id");
        }
        this.message("info", `deleting ${id}`);
        this.room._audiences[id].messsage("系统", "你已被管理员移出");
        this.room._audiences[id].handleExit();
        this.room.emit(updateNamesEvent);
        this.message("info", `deleted`);
      },
      handin(this: Admin, _turn: string, _id: string) {
        let turn = _turn.toLowerCase() === "green" ? GREEN : RED;
        let id = Number(_id);
        if (isNaN(id)) {
          this.message("error", "Unknown id");
        }
        this.message(
          "info",
          `handing ${turn === GREEN ? "GREEN" : "RED"} to ${id}`
        );
        this.room.change(turn, id);
        this.message("info", `handed`);
      },
      name(this: Admin, id: string, name: string) {
        if (id === "green") {
          this.room.green.name = name;
        } else if (id === "red") {
          this.room.red.name = name;
        } else {
          let audienceId = Number(id);
          if (isNaN(audienceId)) {
            this.message("error", "Unknown id");
          }
          this.room._audiences[audienceId].name = name;
        }
        this.room.emit(updateNamesEvent);
      },
    };
  }

  message(level: Level, message: string, system: boolean = true): void {
    this.sendMessage("chat", {
      name: system ? "==>" : "<==",
      message: `[${level}] ${message}`,
    });
  }

  handleMessage(message: string): void {
    this.message("input", `${message}`, false);
    let path: string[];
    let args: string[];
    let parts: string[];
    parts = message.split(" ");
    path = parts[0].split(".");
    args = parts.slice(1, parts.length);

    this.message("info", `executer: ${path.join("->")}`, false);
    this.message("info", `arguments: ${args.join(";")}`, false);

    let executer: any = this.methods;
    for (let key of path) {
      executer = executer[key];
      if (executer === undefined) {
        this.message("error", `got undefined when accessing ${key}`);
        return;
      }
    }

    try {
      executer.call(this, ...args);
    } catch (e) {
      this.message("error", e.toString());
      console.error(e);
    }
  }

  handleClick(x: number, y: number): void {}
  handleExit(): void {}
  handleHandin(id: string): void {}
  handleName(name: string): void {}
}

class Connection {
  id: number;
  ws: ws.WebSocket;
  ip: string;
  name: string;
  roomId: string;
  room: Room;
  user: User;

  constructor(ws: ws.WebSocket, ip: string) {
    this.ws = ws;
    this.ip = ip;

    ws.on("message", (message) => this.handleMessage(message));

    ws.on("close", (e) => {
      if (this.user) {
        this.user.handleExit();
      }
      this.ws.close();
    });
  }

  handleMessage(message: any): void {
    let data: any = JSON.parse(message.toString());

    switch (data.type) {
      case "apply":
        if (tokens.in(data.room)) {
          this.user = new Admin(this);
          break;
        }

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

class Tokens {
  tokenList: string[];

  constructor() {
    this.tokenList = [];
    for (let i = 0; i < 6; i++) {
      const uuid = randomUUID();
      this.tokenList = [uuid, ...this.tokenList];
      console.log(uuid);
    }
    setInterval(() => {
      this.tokenList.pop();
      const uuid = randomUUID();
      this.tokenList = [uuid, ...this.tokenList];
      console.log(uuid);
    }, 10000);
  }

  in(token: string): boolean {
    return this.tokenList.find((value) => value === token) !== undefined;
  }
}

const tokens = new Tokens();

app.ws("/ws", (ws, req) => {
  new Connection(ws, req.ip);
});

app.listen(8000, "localhost");
