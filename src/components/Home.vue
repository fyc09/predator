<script setup lang="ts">
import { Ref, ref } from "vue";

const props = defineProps<{
  handleEnter: (room: string) => void;
}>();

const room: Ref<string> = ref("");

function onEnter() {
  props.handleEnter(room.value);
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
  </div>
</template>
