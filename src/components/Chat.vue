<template>
  <div class="text">
    用户名：
    <input
      type="text"
      name="name"
      id="chat"
      v-model="name"
      @keyup.enter="handleClickChange()"
    />
    <button @click="handleClickChange()">保存</button>
  </div>
  <div class="text">
    你是 <b>{{ info.name }}。</b>
  </div>
  <div class="text">
    发消息：
    <input
      type="text"
      name="chat"
      id="chat"
      v-model="message"
      @keyup.enter="handleClick"
    />
    <button @click="handleClick()">发送</button>
  </div>
  <template v-for="msg in history">
    <div class="chat text">
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
