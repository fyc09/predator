<script setup>

const props = defineProps(["hint"])

</script>

<template>
  <div id="nav" class="container">
    <b>系统提示：{{ hint }}</b>
  </div>
</template>

<style scoped>
#nav {
  width: 100%;
  position: fixed;
  top: 0px;
  left: 0px;
  padding: 7px;
}
</style>
