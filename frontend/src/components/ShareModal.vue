<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import Modal from './Modal.vue';
import api from '@/services/api';

const props = defineProps<{
  show: boolean;
  path: string;
  storageType: 'shared' | 'private';
  isFile: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const permissions = ref<'read' | 'read_write'>('read');
const expiresType = ref<'never' | '1day' | '1week' | '1month' | 'custom'>('never');
const customExpiresAt = ref<string>('');
const isCreating = ref(false);
const shareUrl = ref<string | null>(null);
const error = ref<string | null>(null);

// If it's a file, force read-only permissions
watch(() => props.isFile, (isFile) => {
  if (isFile) {
    permissions.value = 'read';
  }
});

// Reset state when modal opens/closes
watch(() => props.show, (show) => {
  if (!show) {
    permissions.value = 'read';
    expiresType.value = 'never';
    customExpiresAt.value = '';
    shareUrl.value = null;
    error.value = null;
  }
});

const canSelectPermissions = computed(() => !props.isFile);

const handleCreateShare = async () => {
  if (isCreating.value) return;
  
  error.value = null;
  isCreating.value = true;
  
  try {
    // Calculate expires_at
    let expiresAt: number | null = null;
    
    if (expiresType.value !== 'never') {
      const now = new Date();
      let expiresDate: Date;
      
      if (expiresType.value === '1day') {
        expiresDate = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      } else if (expiresType.value === '1week') {
        expiresDate = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      } else if (expiresType.value === '1month') {
        expiresDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
      } else if (expiresType.value === 'custom') {
        if (!customExpiresAt.value) {
          error.value = 'Please select an expiration date';
          isCreating.value = false;
          return;
        }
        expiresDate = new Date(customExpiresAt.value);
        if (expiresDate.getTime() <= now.getTime()) {
          error.value = 'Expiration date must be in the future';
          isCreating.value = false;
          return;
        }
      } else {
        expiresDate = now;
      }
      
      expiresAt = Math.floor(expiresDate.getTime() / 1000);
    }
    
    const result = await api.createShare(
      props.path,
      props.storageType,
      permissions.value,
      expiresAt
    );
    
    shareUrl.value = result.share_url;
  } catch (err: any) {
    console.error('Failed to create share', err);
    error.value = err.response?.data?.detail || 'Failed to create share. Please try again.';
  } finally {
    isCreating.value = false;
  }
};

const copyToClipboard = async () => {
  if (shareUrl.value) {
    try {
      await navigator.clipboard.writeText(shareUrl.value);
      // You could show a toast notification here
    } catch (err) {
      console.error('Failed to copy to clipboard', err);
    }
  }
};

const getMinDate = () => {
  const now = new Date();
  now.setMinutes(now.getMinutes() + 1); // At least 1 minute in the future
  return now.toISOString().slice(0, 16); // Format: YYYY-MM-DDTHH:mm
};
</script>

<template>
  <Modal :show="show" title="Share" @close="emit('close')">
    <div class="flex flex-col gap-4">
      <!-- Share URL (shown after creation) -->
      <div v-if="shareUrl" class="flex flex-col gap-2">
        <p class="text-sm text-neutral-600">Share link created:</p>
        <div class="flex items-center gap-2 p-2 bg-neutral-50 rounded border border-neutral-200">
          <input
            :value="shareUrl"
            readonly
            class="flex-1 text-sm text-neutral-800 bg-transparent border-none outline-none"
          />
          <button
            @click="copyToClipboard"
            class="px-3 py-1 text-xs font-medium text-primary hover:bg-neutral-100 rounded transition-colors"
          >
            Copy
          </button>
        </div>
        <button
          @click="emit('close')"
          class="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
        >
          Close
        </button>
      </div>
      
      <!-- Share form (shown before creation) -->
      <template v-else>
        <div class="flex flex-col gap-4">
          <!-- Permissions (only for folders) -->
          <div v-if="canSelectPermissions" class="flex flex-col gap-2">
            <label class="text-sm font-medium text-neutral-700">Permissions</label>
            <div class="flex flex-col gap-2">
              <label class="flex items-center gap-2 p-3 border border-neutral-300 rounded-lg cursor-pointer hover:bg-neutral-50">
                <input
                  type="radio"
                  v-model="permissions"
                  value="read"
                  class="w-4 h-4 text-primary"
                />
                <div class="flex-1">
                  <div class="font-medium text-neutral-800">Read only</div>
                  <div class="text-xs text-neutral-500">Viewers can only view files</div>
                </div>
              </label>
              <label class="flex items-center gap-2 p-3 border border-neutral-300 rounded-lg cursor-pointer hover:bg-neutral-50">
                <input
                  type="radio"
                  v-model="permissions"
                  value="read_write"
                  class="w-4 h-4 text-primary"
                />
                <div class="flex-1">
                  <div class="font-medium text-neutral-800">Read and write</div>
                  <div class="text-xs text-neutral-500">Viewers can view, edit, and upload files</div>
                </div>
              </label>
            </div>
          </div>
          <div v-else class="text-sm text-neutral-600">
            Files can only be shared with read-only permissions.
          </div>
          
          <!-- Expiration -->
          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-neutral-700">Expiration</label>
            <select
              v-model="expiresType"
              class="px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="never">Never</option>
              <option value="1day">1 day</option>
              <option value="1week">1 week</option>
              <option value="1month">1 month</option>
              <option value="custom">Custom date</option>
            </select>
            
            <!-- Custom date picker -->
            <input
              v-if="expiresType === 'custom'"
              type="datetime-local"
              v-model="customExpiresAt"
              :min="getMinDate()"
              class="px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <!-- Error message -->
          <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {{ error }}
          </div>
          
          <!-- Actions -->
          <div class="flex gap-2">
            <button
              @click="emit('close')"
              class="flex-1 px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors font-medium text-neutral-700"
            >
              Cancel
            </button>
            <button
              @click="handleCreateShare"
              :disabled="isCreating"
              class="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isCreating ? 'Creating...' : 'Create Share' }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </Modal>
</template>
