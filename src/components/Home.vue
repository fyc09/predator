<template>
  <div class="text">Room ID:</div>
  <input
    type="password"
    v-model="room"
    @keyup.enter="handleEnter(room)"
    class="container"
  />
  <button class="container" @click="handleEnter(room)">Enter</button>
</template>

<script>
export default {
  data() {
    return {
      room: "",
    };
  },
  props: ["handleEnter"],
};
</script>

<style scoped>
* {
  color: #ecf1f1;
}
</style>
