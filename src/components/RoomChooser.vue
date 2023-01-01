<template>
  Room ID:
  <input type="password" v-model="room" @keyup.enter="handleEnter(room)" />
  <button @click="handleEnter(room)">Enter</button>
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
