<script setup lang="ts">
import { Turn } from "../../backend/src/types";

const props = defineProps<{
  info: { names: string[] };
  currentTurn: Turn;
  userName: string;
}>();
</script>

<template>
  <div class="text">用户列表</div>
  <div
    v-for="(name, index) in info.names"
    class="user ctext"
    :class="[
      index > 1
        ? 'cpublic'
        : (currentTurn == 2 + index
            ? ['cred', 'cgreen']
            : ['credf', 'cgreenf'])[index],
    ]"
  >
    <b v-if="name == userName">{{ name }}</b>
    <template v-else>{{ name }}</template>
  </div>
</template>

<style>
.user {
  width: 200px;
  padding: 3px;
}
</style>
