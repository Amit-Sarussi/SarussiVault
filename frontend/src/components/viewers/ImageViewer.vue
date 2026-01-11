<script setup lang="ts">
import { computed } from 'vue';
import api from '@/services/api';
import type { StorageType } from '@/context/appContext';

const props = defineProps<{
  filePath: string;
  storageType?: StorageType;
  shareId?: string;
  isRootFileShare?: boolean;
}>();

const imageUrl = computed(() => {
  if (props.shareId) {
    // For root file shares, always pass empty path to API
    // For folder shares, use the filePath as provided
    if (props.isRootFileShare) {
      return api.getSharedFileUrl(props.shareId, '');
    }
    // For folder shares, use the filePath as provided
    return api.getSharedFileUrl(props.shareId, props.filePath || '');
  }
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
