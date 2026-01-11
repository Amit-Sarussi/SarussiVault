<script setup lang="ts">
import { computed } from 'vue';
import api from '@/services/api';

const props = defineProps<{
  filePath: string;
  storageType?: 'shared' | 'private';
  shareId?: string;
  isRootFileShare?: boolean;
}>();

const videoUrl = computed(() => {
  if (props.shareId) {
    // For root file shares, always pass empty path to API
    // For folder shares, use the filePath as provided
    if (props.isRootFileShare) {
      return api.getSharedFileUrl(props.shareId, '');
    }
    return api.getSharedFileUrl(props.shareId, props.filePath || '');
  }
  return api.getFileUrl(props.filePath, props.storageType || 'shared');
});
</script>

<template>
  <div class="h-full w-full bg-black flex items-center justify-center overflow-auto p-4">
    <video
      :src="videoUrl"
      controls
      class="max-w-full max-h-full"
      @error="(e) => console.error('Video load error', e)"
    >
      Your browser does not support the video tag.
    </video>
  </div>
</template>
