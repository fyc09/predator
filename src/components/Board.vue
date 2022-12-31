<template>
  <div id="message">
    message: <b>{{ data.hint }}</b>
  </div>
  <table id="board">
    <tr v-for="(row, i) in data.board">
      <td
        v-for="(grid, j) in row"
        class="grid"
        :style="{
          backgroundColor: grid.color,
        }"
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
  props: ["data", "handleEnter", "handleLeave", "handleDown"],
};
</script>

<style scoped>
.grid {
  text-align: center;
  color: white;
  width: 20px;
  margin: 0px;
  padding: 0px;
  border: 0px;
}

#message {
  padding-left: 2px;
  margin-bottom: 10px;
}
</style>
