<script setup lang="ts">
import { Ref, ref } from "vue";

const props = defineProps<{
  handleEnter: (room: string) => void;
  handleSingle: () => void;
  handleAI: () => void;
  handleAIBattle: () => void;
}>();

const room: Ref<string> = ref("");

function onEnter() {
  props.handleEnter(room.value);
}

function onSingle() {
  props.handleSingle();
}

function onAI() {
  props.handleAI();
}

function onAIBattle() {
  props.handleAIBattle();
}
</script>

<template>
  <div class="text">
    房间号:
    <input
      type="text"
      title="Room ID"
      placeholder="Room ID"
      v-model="room"
      @keyup.enter.prevent="onEnter"
      class="container"
    />
    <button @click.prevent="onEnter">进入</button>
    <br />
    <button @click.prevent="onSingle">单机模式</button>
    <button @click.prevent="onAI">人机模式</button>
    <button @click.prevent="onAIBattle">AI 对战</button>
  </div>
</template>
