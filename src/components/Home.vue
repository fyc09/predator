<script setup lang="ts">
import { Ref, ref } from "vue";

const props = defineProps<{
  handleEnter: (room: string) => void;
}>();

const room: Ref<string> = ref("");
</script>

<template>
  <form class="text">
    房间号:
    <input
      type="text"
      title="Room ID"
      placeholder="Room ID"
      v-model="room"
      @keyup.enter.prevent="handleEnter(room)"
      class="container"
    />
    <button type="button" class="container" @click.prevent="handleEnter(room)">
      进入
    </button>
  </form>
</template>

<style scoped>
* {
  color: #ecf1f1;
}
</style>
