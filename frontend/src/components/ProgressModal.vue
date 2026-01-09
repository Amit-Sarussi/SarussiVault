<script setup lang="ts">
import { computed } from 'vue';
import Modal from './Modal.vue';

const props = defineProps<{
  show: boolean;
  progress: number; // 0-100
  status?: string;
  estimatedTime?: number; // seconds remaining
}>();

const progressBarStyle = computed(() => ({
  width: `${Math.min(100, Math.max(0, props.progress))}%`,
}));

const formatTime = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
};
</script>

<template>
  <Modal :show="show" title="Uploading..." :closable="false">
    <div class="space-y-4">
      <div v-if="status" class="text-sm text-neutral-600">
        {{ status }}
      </div>
      
      <!-- Progress bar -->
      <div class="w-full bg-neutral-200 rounded-full h-2.5 overflow-hidden">
        <div
          class="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
          :style="progressBarStyle"
        ></div>
      </div>
      
      <!-- Progress percentage -->
      <div class="flex items-center justify-between text-sm">
        <span class="text-neutral-600">{{ Math.round(progress) }}%</span>
        <span v-if="estimatedTime !== undefined && estimatedTime > 0" class="text-neutral-500">
          {{ formatTime(estimatedTime) }} remaining
        </span>
      </div>
    </div>
  </Modal>
</template>
