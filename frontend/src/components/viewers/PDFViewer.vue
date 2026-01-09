<script setup lang="ts">
import { computed } from 'vue';
import api from '@/services/api';
import IconDownload from '@/assets/icons/download.svg';

const props = defineProps<{
  filePath: string;
  storageType?: 'shared' | 'private';
}>();

const pdfUrl = computed(() => {
  return api.getFileUrl(props.filePath, props.storageType || 'shared');
});

const fileName = computed(() => {
  const parts = props.filePath.split('/');
  return parts[parts.length - 1] || 'file.pdf';
});

const handleDownload = () => {
  api.downloadFile(props.filePath, props.storageType || 'shared');
};
</script>

<template>
  <div class="h-full w-full bg-neutral-50 flex items-center justify-center p-8">
    <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
      <div class="mb-6">
        <svg class="w-16 h-16 mx-auto text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>
      <h3 class="text-lg font-semibold text-neutral-800 mb-2">PDF Preview Not Available</h3>
      <p class="text-sm text-neutral-600 mb-6">
        PDF files cannot be displayed in the browser. Please download the file to view it.
      </p>
      <button
        @click="handleDownload"
        class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
      >
        <IconDownload class="w-5 h-5" />
        <span>Download PDF</span>
      </button>
      <p class="text-xs text-neutral-500 mt-4">{{ fileName }}</p>
    </div>
  </div>
</template>
