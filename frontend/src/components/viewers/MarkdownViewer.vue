<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';

const props = defineProps<{
  filePath: string;
  storageType?: 'shared' | 'private';
}>();

const content = ref<string>('');
const loading = ref(true);
const error = ref<string | null>(null);

const loadFile = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.getFileContent(props.filePath, props.storageType || 'shared');
    content.value = response;
  } catch (err) {
    console.error('Failed to load file', err);
    error.value = 'Failed to load file content';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadFile();
});
</script>

<template>
  <div class="h-full w-full bg-white flex flex-col overflow-hidden">
    <div class="flex-1 overflow-auto p-4 prose prose-sm max-w-none min-h-0">
      <div v-if="loading" class="text-neutral-500">Loading...</div>
      <div v-else-if="error" class="text-red-600">{{ error }}</div>
      <div v-else class="markdown-content whitespace-pre-wrap break-words">{{ content }}</div>
    </div>
  </div>
</template>

<style scoped>
.markdown-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  font-weight: bold;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-content h1 { font-size: 2em; }
.markdown-content h2 { font-size: 1.5em; }
.markdown-content h3 { font-size: 1.25em; }

.markdown-content p {
  margin-bottom: 1em;
}

.markdown-content code {
  background-color: #f4f4f4;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background-color: #f4f4f4;
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 1em;
}

.markdown-content pre code {
  background-color: transparent;
  padding: 0;
}

.markdown-content ul,
.markdown-content ol {
  margin-left: 2em;
  margin-bottom: 1em;
}

.markdown-content blockquote {
  border-left: 4px solid #ddd;
  padding-left: 1em;
  margin-left: 0;
  color: #666;
}
</style>
