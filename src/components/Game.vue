<script setup>
import Board from "./Board.vue";
import RoomChooser from "./RoomChooser.vue";
import Chat from "./Chat.vue";
import UserList from "./UserList.vue";
</script>

<template>
  <RoomChooser v-if="status == 0" :handleEnter="handleEnterRoom" />
  <div v-if="status == 1">
    message: <b>{{ message }}</b>
  </div>
  <div v-if="status == 2" id="panel">
    <div class="pad">
      <Board
        :data="appearance"
        :handle-enter="handleMounseEnter"
        :handle-leave="handleMouseLeave"
        :handle-down="handleMouseDown"
      />
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
      <UserList :info="info" />
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
          this.status = data.status;
          break;
        case "message":
          this.message = data.message;
          break;
        case "data":
          this.data = data.data;
          this.appearance = this.data.origin;
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
      appearance: [],
      room: "",
      message: "",
      chatting: [],
      chat_tmp: "",
      info: {},
      ws,
    };
  },
  methods: {
    handleMounseEnter(x, y) {
      this.appearance = this.data.board[x][y];
    },
    handleMouseLeave(x, y) {
      this.appearance = this.data.origin;
    },
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
  },
  components: { RoomChooser, Board, Chat, UserList },
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
