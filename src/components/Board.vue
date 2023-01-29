<script setup>
import { hints, classes } from "./constants";
import { ref } from "vue";

const props = defineProps(["data", "handleDown", "setHint"]);

const position = ref([-1, -1]);

function handleEnter(x, y) {
  position.value = [x, y];
  props.setHint(hints[props.data[x][y].hint]);
}

function handleLeave(x, y) {
  props.setHint("");
  position.value = [-1, -1];
}
</script>

<template>
  <table id="board">
    <tr v-for="(row, i) in data">
      <td
        v-for="(grid, j) in row"
        class="grid ctext"
        :class="[
          classes[
            i == position[0] && j == position[1] ? grid.hover : grid.color
          ],
        ]"
        @mouseenter="handleEnter(i, j)"
        @mouseleave="handleLeave(i, j)"
        @mousedown="handleDown(i, j)"
      >
        {{ grid.score }}
      </td>
    </tr>
  </table>
</template>

<style scoped>
.grid {
  text-align: center;
  width: 20px;
  height: 20px;
  font-size: 5pt;
  margin: 0px;
  padding: 0px;
  border: 0px;
}

#message {
  padding-left: 2px;
  margin-bottom: 10px;
}
</style>
