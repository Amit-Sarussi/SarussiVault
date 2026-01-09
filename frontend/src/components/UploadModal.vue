<script setup lang="ts">
import Modal from './Modal.vue';
import IconFile from '@/assets/icons/file.svg';
import IconFolderGray from '@/assets/icons/folder-gray.svg';

const emit = defineEmits<{
  selectFiles: [];
  selectFolders: [];
  close: [];
}>();

const handleSelectFiles = () => {
  emit('selectFiles');
  emit('close');
};

const handleSelectFolders = () => {
  emit('selectFolders');
  emit('close');
};
</script>

<template>
  <Modal :show="true" title="Upload" @close="emit('close')">
    <div class="flex flex-col gap-3">
      <p class="text-sm text-neutral-600 mb-2">What would you like to upload?</p>
      <button
        @click="handleSelectFiles"
        class="flex items-center gap-3 p-4 border border-neutral-300 rounded-lg hover:bg-neutral-50 hover:border-blue-500 transition-colors text-left w-full cursor-pointer"
      >
        <IconFile class="w-6 h-6 text-neutral-600 flex-shrink-0" />
        <div class="flex-1">
          <div class="font-medium text-neutral-800">Files</div>
          <div class="text-sm text-neutral-500">Upload one or more files</div>
        </div>
      </button>
      <button
        @click="handleSelectFolders"
        class="flex items-center gap-3 p-4 border border-neutral-300 rounded-lg hover:bg-neutral-50 hover:border-blue-500 transition-colors text-left w-full cursor-pointer"
      >
        <IconFolderGray class="w-6 h-6 flex-shrink-0" />
        <div class="flex-1">
          <div class="font-medium text-neutral-800">Folders</div>
          <div class="text-sm text-neutral-500">Upload one or more folders</div>
        </div>
      </button>
    </div>
  </Modal>
</template>
