<script setup lang="ts">
import Game from "./components/Game.vue";
</script>

<template>
  <Game />
</template>

<style>
body {
  background-color: #dfebeb;
  padding-top: 35px;
}

.container {
  color: #212424;
  background-color: #cddbdb;
  border: 0px;
}

.text {
  color: #1f2323;
}

button,
input {
  outline: none;
  color: #202121;
  background-color: #b3b8b8;
  border: 0px;
}

button {
  margin-left: 5px;
}

.cnone {
  background-color: #ffffff;
}
.cpublic {
  background-color: #8e9797;
}
.cred {
  background-color: #ba8282;
}
.cgreen {
  background-color: #72ab54;
}
.credf {
  background-color: #e0afaf;
}
.cgreenf {
  background-color: #9fc29c;
}
.cavbl {
  background-color: #bb86d4;
}
.cuavbl {
  background-color: #edde55;
}
.ctext {
  color: #2a3337;
}
</style>
