<script setup lang="ts">
import { Ref, ref } from "vue";

const props = defineProps<{
  handleEnter: (room: string) => void;
  handleSingle: () => void;
  handleAI: () => void;
  handleAIBattle: () => void;
  handleAIBattleModels: (red: string, green: string) => void;
  models: string[];
  showModelSelect: boolean;
}>();

const room: Ref<string> = ref("");
const redModel: Ref<string> = ref("");
const greenModel: Ref<string> = ref("");

function onEnter() {
  props.handleEnter(room.value);
}

function onSingle() {
  props.handleSingle();
}

function onAI() {
  props.handleAI();
}

function onAIBattle() {
  props.handleAIBattle();
}

function onStartBattle() {
  props.handleAIBattleModels(redModel.value, greenModel.value);
}
</script>

<template>
  <div v-if="!showModelSelect" class="text">
    房间号:
    <input
      type="text"
      title="Room ID"
      placeholder="Room ID"
      v-model="room"
      @keyup.enter.prevent="onEnter"
      class="container"
    />
    <button @click.prevent="onEnter">进入</button>
    <br />
    <button @click.prevent="onSingle">单机模式</button>
    <button @click.prevent="onAI">人机模式</button>
    <button @click.prevent="onAIBattle">AI 对战</button>
  </div>
  <div v-else class="text">
    <div>红方模型:
      <select v-model="redModel">
        <option v-for="m in models" :value="m">{{ m }}</option>
      </select>
    </div>
    <div>绿方模型:
      <select v-model="greenModel">
        <option v-for="m in models" :value="m">{{ m }}</option>
      </select>
    </div>
    <button @click.prevent="onStartBattle">开始对战</button>
  </div>
</template>
