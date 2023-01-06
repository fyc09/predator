import express from "express";
import expressWs from "express-ws";
import { updateReturn } from "typescript";
import ws from "ws";
import { copyGame, handleRequest, initGame } from "./core.js";
import { renderGame } from "./renderer.js";
import { Game, PUBLIC, GREEN, RED, MessageType, Room, User } from "./types.js";

const appBase = express();
const app = expressWs(appBase).app;

app.use(express.json());
app.use(express.static("./dist"));

let sessions: Map<string, Room> = new Map();

function sendMessage(ws: ws, type: MessageType, msg: any) {
  let data: any = { type };
  data[type] = msg;
  ws.send(JSON.stringify(data));
}

function updateNames(room: Room) {
  let names = room.users.map((user) => user.name);
  room.users.forEach((target) => {
    sendMessage(target.ws, "info", { names: names });
  });
}

function updateData(room: Room) {
  let publicBoard = renderGame(room.game, PUBLIC, room.currentTurn);
  room.users.forEach((target) => {
    if (target.id >= 2) {
      sendMessage(target.ws, "data", publicBoard);
    } else if (target.id == 1) {
      sendMessage(
        target.ws,
        "data",
        renderGame(room.game, GREEN, room.currentTurn)
      );
    } else if (target.id == 0) {
      sendMessage(
        target.ws,
        "data",
        renderGame(room.game, RED, room.currentTurn)
      );
    }
  });
}

function updateTurn(room: Room) {
  room.users.forEach((target) => {
    sendMessage(target.ws, "info", { currentTurn: room.currentTurn });
  });
}

app.ws("/ws", (ws, _req) => {
  let roomid: string;
  let room: Room;
  let id: number;
  let user: User;

  ws.on("message", (msg) => {
    let data: any = JSON.parse(msg.toString());
    switch (data.type) {
      case "apply":
        roomid = data.room;
        sendMessage(ws, "status", 1);

        if (!sessions.has(roomid)) {
          room = {
            game: initGame(10, 10),
            users: [],
            currentTurn: GREEN,
            idCount: 0,
          };
          sessions.set(roomid, room);
        }

        room = sessions.get(roomid);

        let users = room.users;
        id = room.idCount;
        room.idCount++;

        // 作为观众
        if (users.length >= 2) {
          user = { id, ws, name: `au${id - 1}` };
          room.users.push(user);
          sendMessage(
            ws,
            "data",
            renderGame(room.game, PUBLIC, room.currentTurn)
          );
          sendMessage(ws, "info", {
            name: user.name,
            currentTurn: room.currentTurn,
            id,
          });
          sendMessage(ws, "status", 2);

          updateNames(room);
          break;
        }

        // 作为玩家
        user = { id, ws, name: `pl${id + 1}` };
        users.push(user);

        // 第一位玩家
        if (users.length == 1) {
          sendMessage(ws, "message", "请等待");
          return;
        }

        updateData(room);

        sendMessage(ws, "info", {
          name: user.name,
          names: ["pl1", "pl2"],
          currentTurn: room.currentTurn,
          id,
        });
        sendMessage(ws, "status", 2);
        sendMessage(users[0].ws, "info", {
          name: users[0].name,
          names: ["pl1", "pl2"],
          currentTurn: room.currentTurn,
          id: 0,
        });
        sendMessage(users[0].ws, "status", 2);
        break;

      case "click":
        if (id + 2 != room.currentTurn) {
          return;
        }

        let result = handleRequest(
          copyGame(room.game),
          [data.x, data.y],
          id + 2
        );

        if (result < 0) {
          return;
        }

        room.game = result as Game;
        room.currentTurn = 5 - room.currentTurn;

        updateData(room);
        updateTurn(room);
        break;

      case "message":
        room.users.forEach((target) => {
          sendMessage(target.ws, "chat", {
            message: data.message,
            identify: user.name,
          });
        });
        break;

      case "name":
        let ok = true;
        room.users.forEach((target) => {
          if (target.name == data.name) {
            ok = false;
          }
        });
        if (data.name.length == 0) {
          ok = false;
        }

        if (ok) {
          user.name = data.name;
          sendMessage(ws, "info", { name: data.name });
        }

        updateNames(room);
        break;
    }
  });

  ws.on("close", (e) => {
    if (!room) {
      return;
    }
    if (id >= 2) {
      room.users.splice(id, 1);
      return;
    }
    if (room.users.length == 1) {
      return;
    }
    sendMessage(room.users[1 - id].ws, "status", 1);
    sendMessage(room.users[1 - id].ws, "message", "对方已经退出，请刷新页面");
    room.users.forEach((target) => {
      if (target.id >= 2) {
        sendMessage(target.ws, "status", 1);
        sendMessage(target.ws, "message", "一方已退出，请刷新页面");
      }
    });
    room.users[1 - id].ws.close();
    sessions.delete(roomid);
  });
});

app.listen(8000, "localhost");
