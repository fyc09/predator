<script setup>
import Board from "./Board.vue";
import Home from "./Home.vue";
import Chat from "./Chat.vue";
import UserList from "./UserList.vue";
import Navbar from "./Navbar.vue";
</script>

<template>
  <Navbar :message="message" />
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

<script>
export default {
  data() {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    ws.onmessage = (e) => {
      let data = e.data;
      data = JSON.parse(data);
      switch (data.type) {
        case "status":
          this.setHint("");
          this.status = data.status;
          break;
        case "message":
          this.message = data.message;
          break;
        case "data":
          this.data = data.data;
          break;
        case "chat":
          this.chatting = [data.chat, ...this.chatting];
          break;
        case "info":
          for (let key in data.info) {
            this.info[key] = data.info[key];
          }
      }
    };
    return {
      status: 0,
      data: {},
      room: "",
      message: "",
      chatting: [],
      chat_tmp: "",
      info: {},
      ws,
    };
  },
  methods: {
    handleMouseDown(x, y) {
      this.ws.send(
        JSON.stringify({
          type: "click",
          x,
          y,
        })
      );
    },
    handleEnterRoom(room) {
      this.ws.send(
        JSON.stringify({
          type: "apply",
          room: room,
        })
      );
    },
    handleSendMessage(message) {
      this.ws.send(
        JSON.stringify({
          type: "message",
          message,
        })
      );
    },
    handleChangeName(name) {
      this.ws.send(
        JSON.stringify({
          type: "name",
          name,
        })
      );
    },
    setHint(hint) {
      this.message = hint;
    },
  },
  components: { Home, Board, Chat, UserList, Navbar },
};
</script>

<style scoped>
#panel {
  display: flex;
}

.pad {
  padding-left: 20px;
}
</style>
