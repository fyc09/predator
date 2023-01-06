<script setup>
import Game from "./components/Game.vue";
</script>

<template>
  <Game />
</template>

<script>
export default {
  components: { Game },
};
</script>

<style>
body {
  background-color: #212323;
  padding-top: 35px;
}

.container {
  color: #ecf1f1;
  background-color: #494d4d;
  border: 0px;
}

.text {
  color: #ecf1f1;
}

button,
input {
  outline: none;
  color: #ecf1f1;
  background-color: #494d4d;
  border: 0px;
}

button {
  margin-left: 5px;
}

.cnone {
  background-color: #ffffff;
}
.cpublic {
  background-color: #404b4d;
}
.cred {
  background-color: #682929;
}
.cgreen {
  background-color: #284f13;
}
.credf {
  background-color: #7a6060;
}
.cgreenf {
  background-color: #657b63;
}
.cavbl {
  background-color: #795789;
}
.cuavbl {
  background-color: #837818;
}
.ctext {
  color: #ccdee1;
}
</style>
