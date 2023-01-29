<script setup>
import { ref } from "vue";

const props = defineProps(["handleEnter"]);

const room = ref("");
</script>

<template>
  <div class="text">房间号:</div>
  <input
    type="password"
    v-model="room"
    @keyup.enter="handleEnter(room)"
    class="container"
  />
  <button class="container" @click="handleEnter(room)">进入</button>
</template>

<style scoped>
* {
  color: #ecf1f1;
}
</style>
