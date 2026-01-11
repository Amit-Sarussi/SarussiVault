<script setup lang="ts">
import { computed } from 'vue';
import api from '@/services/api';

const props = defineProps<{
  filePath: string;
  storageType?: 'shared' | 'private';
  shareId?: string;
  isRootFileShare?: boolean;
}>();

const audioUrl = computed(() => {
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
  <div class="h-full w-full bg-white flex items-center justify-center overflow-auto p-4">
    <div class="w-full max-w-2xl">
      <audio
        :src="audioUrl"
        controls
        class="w-full"
        @error="(e) => console.error('Audio load error', e)"
      >
        Your browser does not support the audio tag.
      </audio>
    </div>
  </div>
</template>
