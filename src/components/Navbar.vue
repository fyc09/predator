<template>
  <div id="nav" class="container">
    <b>系统提示：{{ message }}</b>
  </div>
</template>

<script>
export default {
  props: ["message"],
};
</script>

<style scoped>
#nav {
  width: 100%;
  position: fixed;
  top: 0px;
  left: 0px;
  padding: 7px;
}
</style>
