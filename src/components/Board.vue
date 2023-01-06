<script setup>
import { hints, classes } from "./constants";
</script>

<template>
  <table id="board">
    <tr v-for="(row, i) in data">
      <td
        v-for="(grid, j) in row"
        class="grid ctext"
        :class="[
          classes[
            i == this.position[0] && j == this.position[1]
              ? grid.hover
              : grid.color
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

<script>
export default {
  props: ["data", "handleDown", "setHint"],
  data() {
    return {
      position: [-1, -1],
    };
  },
  methods: {
    handleEnter(x, y) {
      this.position = [x, y];
      this.setHint(hints[this.data[x][y].hint]);
    },
    handleLeave(x, y) {
      this.setHint("");
      this.position = [-1, -1];
    },
  },
};
</script>

<style scoped>
.grid {
  text-align: center;
  width: 20px;
  height: 20px;
  font-size:5pt;
  margin: 0px;
  padding: 0px;
  border: 0px;
}

#message {
  padding-left: 2px;
  margin-bottom: 10px;
}
</style>
