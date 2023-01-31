<script setup lang="ts">
import { hints, classes } from "./constants";
import { Ref, ref } from "vue";
import { Position, RenderedGame, ZERO_POSITION } from "../../backend/src/types";

const props = defineProps<{
  data: RenderedGame;
  setHint: (hint: string) => void;
  handleDown: (x: number, y: number) => void;
}>();

const position: Ref<Position> = ref(ZERO_POSITION);

function handleEnter(x: number, y: number) {
  position.value = [x, y];
  props.setHint(hints[props.data[x][y].hint]);
}

function handleLeave(_x: number, _y: number) {
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
