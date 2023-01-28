<script setup>
import { ref } from "vue";

const props = defineProps(["history", "info", "handleSendMessage", "handleChangeName"])

const message = ref("");
const name = ref(props.info.name);

function handleClick() {
  if (message.value == "") {
    return;
  }
  props.handleSendMessage(message.value);
  message.value = "";
}

function handleClickChange() {
  if (name.name == "") {
    return;
  }
  props.handleChangeName(name.value);
}
</script>

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

<style scoped>
.chat {
  padding-left: 3px;
  margin-top: 3px;
}
</style>
