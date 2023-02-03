<script setup lang="ts">
import Game from "./components/Game.vue";
</script>

<template>
  <Game />
</template>

<style>
body {
  background-color: #e8e8e8;
  padding-top: 35px;
}

.container {
  color: #2b2b2b;
  background-color: #b5b5b5;
  border: 0px;
}

.text {
  color: #2b2b2b;
}

button,
input {
  outline: none;
  color: #222222;
  background-color: #b7b7b7;
  border: 0px;
}

button {
  margin-left: 5px;
}

.cnone {
  background-color: #ffffff;
}
.cpublic {
  background-color: #9e9e9e;
}
.cred {
  background-color: #c16262;
}
.cgreen {
  background-color: #549332;
}
.credf {
  background-color: #e0afaf;
}
.cgreenf {
  background-color: #79cf71;
}
.cavbl {
  background-color: #bb86d4;
}
.cuavbl {
  background-color: #edde55;
}
.ctext {
  color: #3c3c3c;
}
</style>
