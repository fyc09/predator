<script setup>
import Board from "./Board.vue";
import Home from "./Home.vue";
import Chat from "./Chat.vue";
import UserList from "./UserList.vue";
import Navbar from "./Navbar.vue";
import { ref } from "vue";

const status = ref(0);
const data = ref({});
const chatting = ref([])
const hint = ref("");
const info = ref({});7

function handleMouseDown(x, y) {
  ws.send(
    JSON.stringify({
      type: "click",
      x,
      y,
    })
  );
}

function handleEnterRoom(room) {
  ws.send(
    JSON.stringify({
      type: "apply",
      room: room,
    })
  );
}

function handleSendMessage(message) {
  ws.send(
    JSON.stringify({
      type: "message",
      message,
    })
  );
}

function handleChangeName(name) {
  ws.send(
    JSON.stringify({
      type: "name",
      name,
    })
  );
}

function setHint(_hint) {
  hint.value = _hint;
}

const ws = new WebSocket(`ws://${window.location.host}/ws`);
ws.onmessage = (e) => {
  let message = e.data;
  message = JSON.parse(message);
  switch (message.type) {
    case "status":
      setHint("");
      status.value = message.status;
      break;
    case "hint":
      hint.value = message.hint;
      break;
    case "data":
      data.value = message.data;
      break;
    case "chat":
      chatting.value = [message.chat, ...chatting.value];
      break;
    case "info":
      for (let key in message.info) {
        info.value[key] = message.info[key];
      }
  }
};

</script>

<template>
  <Navbar :hint="hint" />
  <Home v-if="status == 0" :handleEnter="handleEnterRoom" />
  <div v-if="status == 1">
    <!--为动效预留空间-->
  </div>
  <div v-if="status == 2" id="panel">
    <div class="pad">
      <Board :data="data" :handle-down="handleMouseDown" :set-hint="setHint" />
    </div>
    <div class="pad">
      <Chat
        :history="chatting"
        :info="info"
        :handle-send-message="handleSendMessage"
        :handle-change-name="handleChangeName"
      />
    </div>
    <div class="pad">
      <UserList
        :info="info"
        :current-turn="info.currentTurn"
        :user-id="info.id"
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
