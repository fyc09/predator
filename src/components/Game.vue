<script setup lang="ts">
import Board from "./Board.vue";
import Home from "./Home.vue";
import Chat from "./Chat.vue";
import UserList from "./UserList.vue";
import Navbar from "./Navbar.vue";
import { Ref, ref } from "vue";
import { PUBLIC, RED, RenderedGame, Turn } from "../../backend/src/types";
import { initGame } from "../../backend/src/core";
import { renderGame } from "../../backend/src/renderer";

const status: Ref<number> = ref(0);
const data: Ref<RenderedGame> = ref(renderGame(initGame(1, 1), PUBLIC, RED));
const chatting: Ref<
  {
    name: string;
    message: string;
  }[]
> = ref([]);
const hint: Ref<string> = ref("");
const info: Ref<{
  name: string;
  isPlayer: boolean;
  isAdmin: boolean;
  currentTurn: Turn;
  names: string[];
  single: boolean;
}> = ref({
  name: "",
  isPlayer: false,
  isAdmin: false,
  currentTurn: RED,
  names: [""],
  single: false,
});

function handleMouseDown(x: number, y: number) {
  ws.send(
    JSON.stringify({
      type: "click",
      x,
      y,
    })
  );
}

function handleEnterRoom(room: string) {
  ws.send(
    JSON.stringify({
      type: "apply",
      room,
    })
  );
}

function handleSingle() {
  ws.send(
    JSON.stringify({
      type: "single",
    })
  );
}

function handleSendMessage(message: string) {
  ws.send(
    JSON.stringify({
      type: "message",
      message,
    })
  );
}

function handleChangeName(name: string) {
  ws.send(
    JSON.stringify({
      type: "name",
      name,
    })
  );
}

function handleHandin(id: string) {
  ws.send(
    JSON.stringify({
      type: "handin",
      id,
    })
  );
}

function setHint(_hint: string) {
  hint.value = _hint;
}

const ws = new WebSocket(`ws://${window.location.host}/ws`);
ws.onmessage = (e) => {
  let message = e.data;
  message = JSON.parse(message);
  switch (message.type) {
    case "status":
      setHint("");
      status.value = message.data;
      break;
    case "hint":
      hint.value = message.data;
      break;
    case "data":
      data.value = message.data;
      break;
    case "chat":
      chatting.value = [message.data, ...chatting.value];
      break;
    case "info":
      for (let key in message.data) {
        // @ts-ignore
        info.value[key] = message.data[key];
      }
  }
};
</script>

<template>
  <Navbar :hint="hint" />
  <Home
    v-if="status == 0"
    :handle-enter="handleEnterRoom"
    :handle-single="handleSingle"
  />
  <div v-if="status == 1">
    <!--为动效预留空间-->
  </div>
  <div v-if="status == 2" id="panel">
    <div class="pad">
      <Board
        :data="data"
        :handle-grid-click="handleMouseDown"
        :set-hint="setHint"
      />
    </div>
    <div class="pad" v-if="!info.single">
      <Chat
        :history="chatting"
        :info="info"
        :handle-message-send="handleSendMessage"
        :handle-name-change="handleChangeName"
      />
    </div>
    <div class="pad" v-if="!info.single">
      <UserList
        :handle-handin="handleHandin"
        :info="info"
        :current-turn="info.currentTurn"
      />
    </div>
  </div>
</template>

<style scoped>
#panel {
  display: flex;
}

.pad {
  padding-left: 20px;
}
</style>
