<template>
  <div
    v-for="(name, index) in info.names"
    :style="{
      backgroundColor: index <= 1 ? ['red', 'green'][index] : 'gray',
      color: 'white',
      width: '200px',
    }"
  >
    {{ name }}
  </div>
</template>

<script>
export default {
  props: ["info"],
};
</script>
