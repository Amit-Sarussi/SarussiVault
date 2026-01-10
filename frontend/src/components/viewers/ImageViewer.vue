<script setup lang="ts">
import { computed } from 'vue';
import api from '@/services/api';
import type { StorageType } from '@/context/appContext';

const props = defineProps<{
  filePath: string;
  storageType?: StorageType;
}>();

const imageUrl = computed(() => {
  return api.getFileUrl(props.filePath, props.storageType || 'shared');
});
</script>

<template>
  <div class="w-full h-[calc(100vh-14rem)] bg-neutral-100 flex items-center justify-center overflow-auto p-4">
    <img
      :src="imageUrl"
      :alt="filePath"
      class="w-full h-full object-contain"
      @error="(e) => { (e.target as HTMLImageElement).style.display = 'none'; }"
    />
  </div>
</template>
