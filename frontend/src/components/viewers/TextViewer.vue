<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import api from '@/services/api';
import { useAppContext } from '@/context/appContext';

const props = defineProps<{
  filePath: string;
  storageType?: 'shared' | 'private';
  shareId?: string;
  isRootFileShare?: boolean;
}>();

const { triggerRefresh, triggerHierarchyRefresh, storageType: contextStorageType } = useAppContext();
const content = ref<string>('');
const originalContent = ref<string>('');
const loading = ref(true);
const saving = ref(false);
const error = ref<string | null>(null);
const isEditing = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const effectiveStorageType = props.storageType || contextStorageType.value;

const loadFile = async () => {
  loading.value = true;
  error.value = null;
  try {
    let response: string;
    if (props.shareId) {
      // For root file shares, always pass empty path to API
      // For folder shares, use the filePath as provided
      const apiPath = props.isRootFileShare ? '' : (props.filePath || '');
      response = await api.getSharedFileContent(props.shareId, apiPath);
    } else {
      response = await api.getFileContent(props.filePath, effectiveStorageType);
    }
    content.value = response;
    originalContent.value = response;
  } catch (err) {
    console.error('Failed to load file', err);
    error.value = 'Failed to load file content';
  } finally {
    loading.value = false;
  }
};

const saveFile = async () => {
  if (saving.value) return;
  
  saving.value = true;
  error.value = null;
  try {
    if (props.shareId) {
      // For root file shares, always pass empty path to API
      // For folder shares, use the filePath as provided
      const apiPath = props.isRootFileShare ? '' : (props.filePath || '');
      await api.saveSharedFileContent(props.shareId, apiPath, content.value);
    } else {
      await api.saveFileContent(props.filePath, content.value, effectiveStorageType);
    }
    originalContent.value = content.value;
    isEditing.value = false;
    triggerRefresh();
    triggerHierarchyRefresh();
  } catch (err: any) {
    console.error('Failed to save file', err);
    error.value = err.response?.data?.detail || 'Failed to save file';
  } finally {
    saving.value = false;
  }
};

const cancelEdit = () => {
  content.value = originalContent.value;
  isEditing.value = false;
  error.value = null;
};

const startEdit = () => {
  isEditing.value = true;
  // Focus textarea after it's rendered
  setTimeout(() => {
    textareaRef.value?.focus();
  }, 0);
};

const hasChanges = () => {
  return content.value !== originalContent.value;
};

onMounted(() => {
  loadFile();
});

// Reload when file path changes
watch(() => props.filePath, () => {
  loadFile();
});
</script>

<template>
  <div class="h-full w-full bg-white flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-neutral-200 bg-neutral-50 shrink-0">
      <div class="flex items-center gap-2">
        <button
          v-if="!isEditing"
          @click="startEdit"
          class="px-3 py-1 text-sm text-neutral-700 hover:bg-neutral-200 rounded transition-colors cursor-pointer"
        >
          Edit
        </button>
        <template v-else>
          <button
            @click="saveFile"
            :disabled="saving || !hasChanges()"
            class="px-3 py-1 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
          <button
            @click="cancelEdit"
            :disabled="saving"
            class="px-3 py-1 text-sm text-neutral-700 hover:bg-neutral-200 rounded transition-colors cursor-pointer disabled:opacity-50"
          >
            Cancel
          </button>
        </template>
      </div>
      <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
    </div>
    
    <!-- Content -->
    <div class="flex-1 overflow-auto p-4 min-h-0">
      <pre v-if="loading" class="text-neutral-500">Loading...</pre>
      <pre v-else-if="error && !isEditing" class="text-red-600">{{ error }}</pre>
      <textarea
        v-else-if="isEditing"
        ref="textareaRef"
        v-model="content"
        class="w-full h-full font-mono text-sm whitespace-pre-wrap break-words border border-neutral-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        :disabled="saving"
      />
      <pre v-else class="font-mono text-sm whitespace-pre-wrap break-words">{{ content }}</pre>
    </div>
  </div>
</template>
