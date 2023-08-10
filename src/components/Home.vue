<script setup lang="ts">
import { Ref, ref } from "vue";

const props = defineProps<{
  handleEnter: (room: string) => void;
  handleSingle: () => void;
}>();

const room: Ref<string> = ref("");

function onEnter() {
  props.handleEnter(room.value);
}

function onSingle() {
  props.handleSingle();
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
  </div>
</template>
