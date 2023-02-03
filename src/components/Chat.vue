<script setup lang="ts">
import { Ref, ref } from "vue";

const props = defineProps<{
  history: {
    name: string;
    message: string;
  }[];
  info: {
    name: string;
  };
  handleMessageSend: (message: string) => void;
  handleNameChange: (name: string) => void;
}>();

const message: Ref<string> = ref("");
const name: Ref<string> = ref(props.info.name);

function onSend() {
  if (message.value == "") {
    return;
  }
  props.handleMessageSend(message.value);
  message.value = "";
}

function onSave() {
  if (name.value == "") {
    return;
  }
  props.handleNameChange(name.value);
}
</script>

<template>
  <form class="text">
    用户名：
    <input
      type="text"
      title="Username"
      placeholder="Username"
      name="name"
      id="chat"
      v-model="name"
      @keyup.enter.prevent="onSave()"
    />
    <button @click.prevent="onSave()">保存</button>
  </form>
  <div class="text">
    你是 <b>{{ info.name }}。</b>
  </div>
  <form class="text">
    发消息：
    <input
      type="text"
      title="Message"
      placeholder="Message"
      name="chat"
      id="chat"
      v-model="message"
      @keyup.enter.prevent="onSend"
    />
    <button @click.prevent="onSend()">发送</button>
  </form>
  <template v-for="msg in history">
    <div class="chat text">
      <b>{{ msg.name }}</b
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
