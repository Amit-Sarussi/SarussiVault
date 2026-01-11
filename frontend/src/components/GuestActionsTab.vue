<script setup lang="ts">
import { ref, computed } from 'vue';
import ActionButton from "./ActionButton.vue";
import IconUpload from "@/assets/icons/upload.svg";
import IconDownload from "@/assets/icons/download.svg";
import IconDelete from "@/assets/icons/delete.svg";
import IconFileAdd from "@/assets/icons/file-add.svg";
import IconFolderAdd from "@/assets/icons/folder-add.svg";
import api from "@/services/api";

const props = defineProps<{
  shareId: string;
  shareInfo: any;
  currentPath: string;
  hasWritePermission: boolean;
  selectedFiles?: Set<string>;
  selectedEntries?: Map<string, { name: string; is_dir: boolean }>;
}>();

const emit = defineEmits<{
  refresh: [];
}>();

const selectedFilesInternal = computed(() => props.selectedFiles || new Set());
const selectedEntriesInternal = computed(() => props.selectedEntries || new Map());

// Basic handlers for guest mode
const handleDownload = async () => {
  if (!selectedFilesInternal.value || selectedFilesInternal.value.size === 0) return;
  
  try {
    const selectedFilesArray = Array.from(selectedFilesInternal.value);
    
    // Check if any selected item is a directory or if multiple files
    const hasDirectory = selectedFilesArray.some(path => {
      const entry = selectedEntriesInternal.value.get(path);
      return entry?.is_dir === true;
    });
    
    // Use zip if multiple files or any directory
    if (selectedFilesArray.length > 1 || hasDirectory) {
      await api.downloadSharedAsZip(props.shareId, selectedFilesArray);
    } else {
      // Single file - use regular download
      api.downloadSharedFile(props.shareId, selectedFilesArray[0]);
    }
  } catch (error) {
    console.error('Failed to download files', error);
    alert('Failed to download files.');
  }
};

const handleUpload = () => {
  console.log('Upload not yet implemented for guest mode');
};

const handleDelete = () => {
  console.log('Delete not yet implemented for guest mode');
};

const handleAddFile = () => {
  console.log('Add file not yet implemented for guest mode');
};

const handleAddFolder = () => {
  console.log('Add folder not yet implemented for guest mode');
};

const hasSelection = computed(() => selectedFilesInternal.value.size > 0);
</script>

<template>
  <div class="w-full flex items-center p-2 border-b-neutral-200 border-b gap-1 overflow-x-auto md:overflow-x-visible scrollbar-hide">
    <!-- Only show actions if write permission -->
    <template v-if="hasWritePermission">
      <ActionButton 
        title="Add file" 
        @click="handleAddFile"
      >
        <template #icon>
          <IconFileAdd class="w-5 h-5 text-text-secondary" />
        </template>
      </ActionButton>
      <ActionButton 
        title="Add folder" 
        @click="handleAddFolder"
      >
        <template #icon>
          <IconFolderAdd class="w-5 h-5 text-text-secondary" />
        </template>
      </ActionButton>
      <ActionButton 
        title="Upload" 
        @click="handleUpload"
      >
        <template #icon>
          <IconUpload class="w-5 h-5 text-text-secondary" />
        </template>
      </ActionButton>
      
      <!-- Separator -->
      <div v-if="hasSelection" class="h-6 w-px bg-neutral-300 mx-1"></div>
      
      <template v-if="hasSelection">
        <ActionButton 
          title="Download" 
          @click="handleDownload"
        >
          <template #icon>
            <IconDownload class="w-5 h-5 text-text-secondary" />
          </template>
        </ActionButton>
        <ActionButton 
          title="Delete" 
          @click="handleDelete"
        >
          <template #icon>
            <IconDelete class="w-5 h-5 text-text-secondary" />
          </template>
        </ActionButton>
      </template>
    </template>
    
    <!-- Read-only mode: only download -->
    <template v-else>
      <template v-if="hasSelection">
        <ActionButton 
          title="Download" 
          @click="handleDownload"
        >
          <template #icon>
            <IconDownload class="w-5 h-5 text-text-secondary" />
          </template>
        </ActionButton>
      </template>
    </template>
  </div>
</template>
