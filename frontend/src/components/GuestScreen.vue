<script setup lang="ts">
import { watch, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import GuestFileManager from "./GuestFileManager.vue";
import api from "@/services/api";

const route = useRoute();
const router = useRouter();
const shareId = ref<string>('');
const shareInfo = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

// Define loadShareInfo before using it in watch
const loadShareInfo = async () => {
  if (!shareId.value) {
    console.log('No shareId provided');
    return;
  }
  
  console.log('Loading share info for:', shareId.value);
  loading.value = true;
  error.value = null;
  
  try {
    const info = await api.getShareInfo(shareId.value);
    console.log('Share info loaded:', info);
    shareInfo.value = info;
  } catch (err: any) {
    console.error('Failed to load share info', err);
    error.value = err.response?.data?.detail || err.message || 'Share not found or expired';
  } finally {
    loading.value = false;
    console.log('Loading complete. shareInfo:', shareInfo.value, 'error:', error.value);
  }
};

// Extract share ID from route
watch(
  () => route.params.shareId,
  async (newShareId) => {
    console.log('Route shareId changed:', newShareId, 'route.params:', route.params);
    if (newShareId && typeof newShareId === 'string') {
      shareId.value = newShareId;
      await loadShareInfo();
    } else {
      console.log('Invalid shareId:', newShareId);
      error.value = 'Invalid share ID';
      loading.value = false;
    }
  },
  { immediate: true }
);

// Also watch the full route in case params aren't updating
watch(
  () => route.path,
  (path) => {
    console.log('Route path changed:', path);
    // Extract shareId from path if params didn't update
    const match = path.match(/^\/open\/([^/]+)/);
    if (match && match[1]) {
      const extractedShareId = match[1];
      if (shareId.value !== extractedShareId) {
        console.log('Extracted shareId from path:', extractedShareId);
        shareId.value = extractedShareId;
        loadShareInfo();
      }
    }
  },
  { immediate: true }
);
</script>

<template>
  <div class="w-full h-screen flex flex-col">
    <!-- Simple header for guests -->
    <div class="bg-white border-b border-neutral-200 px-4 py-3 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-neutral-800">Shared Files</h1>
      <div v-if="shareInfo && shareInfo.expires_at" class="text-xs text-neutral-500">
        Expires: {{ new Date(shareInfo.expires_at * 1000).toLocaleDateString() }}
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-neutral-600">Loading...</div>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="text-red-600 font-medium mb-2">{{ error }}</div>
        <div class="text-sm text-neutral-600">The share may have expired or been deleted.</div>
      </div>
    </div>
    
    <!-- Guest file manager -->
    <GuestFileManager
      v-else-if="shareId && shareInfo"
      :share-id="shareId"
      :share-info="shareInfo"
    />
    
    <!-- Fallback: if we have shareId but no shareInfo and no error, something went wrong -->
    <div v-else-if="shareId && !loading && !error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="text-red-600 font-medium mb-2">Failed to load share</div>
        <div class="text-sm text-neutral-600">Share ID: {{ shareId }}</div>
        <div class="text-xs text-neutral-500 mt-2">Debug: shareInfo={{ shareInfo }}, loading={{ loading }}, error={{ error }}</div>
      </div>
    </div>
  </div>
</template>
