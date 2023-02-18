<script setup lang="ts">
import { Turn } from "../../backend/src/types";

const props = defineProps<{
  info: { names: string[]; name: string; isPlayer: boolean };
  currentTurn: Turn;
  handleHandin: (id: string) => void;
}>();

function getId(index: number) {
  return index > 1 ? (index - 2).toString() : ["RED", "GREEN"][index];
}

function onHandin(index: number) {
  props.handleHandin(getId(index));
}
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
    <b v-if="name == info.name">
      {{ name }}
    </b>
    <template v-else>
      {{ name }}
      <button
        v-if="index >= 2 && info.isPlayer"
        @click.prevent="onHandin(index)"
      >
        交接
      </button>
    </template>
  </div>
</template>

<style>
.user {
  width: 200px;
  padding: 3px;
}
</style>
