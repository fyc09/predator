<template>
  <div>
    <input type="text" name="name" id="chat" v-model="name" />
    <button @click="handleClickChange()">Submit</button>
  </div>
  You are <b>{{ info.name }}</b>
  <div>
    <input type="text" name="chat" id="chat" v-model="message" />
    <button @click="handleClick()">Send</button>
  </div>
  <template v-for="msg in history">
    <div class="chat">
      <b>{{ msg.identify }}</b
      >: {{ msg.message }}
    </div>
  </template>
</template>

<script>
export default {
  data() {
    return {
      message: "",
      name: this.info.name,
    };
  },
  props: ["history", "info", "handleSendMessage", "handleChangeName"],
  methods: {
    handleClick() {
      if (this.message == "") {
        return;
      }
      this.handleSendMessage(this.message);
      this.message = "";
    },
    handleClickChange() {
      if (this.name == "") {
        return;
      }
      this.handleChangeName(this.name);
    },
  },
};
</script>

<style scoped>
.chat {
  padding-left: 3px;
  margin-top: 3px;
}
</style>
