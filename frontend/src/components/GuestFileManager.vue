<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import GuestActionsTab from "./GuestActionsTab.vue";
import TextField from "./TextField.vue";
import PathButton from "./PathButton.vue";
import IconMenu from "@/assets/icons/menu.svg";
import GuestFileList from "./GuestFileList.vue";
import FileViewer from "./FileViewer.vue";
import api from "@/services/api";

const props = defineProps<{
  shareId: string;
  shareInfo: any;
}>();

const route = useRoute();
const router = useRouter();

const currentPath = ref<string>('');
const viewedFile = ref<string | null>(null);
const displayedPath = ref<string>('');
let isUserEditing = false;

// Search state
const searchQuery = ref<string>('');
const searchResults = ref<any[]>([]);
const isSearching = ref<boolean>(false);
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

// View mode state
const viewMode = ref<'table' | 'grid'>('table');

// Check if we're at root (empty path)
const isAtRoot = computed(() => !currentPath.value || currentPath.value === '');

// Check permissions
const hasWritePermission = computed(() => props.shareInfo?.permissions === 'read_write');

// Check if the shared resource is a file (has file extension)
const isFileShare = computed(() => {
  const sharePath = props.shareInfo?.path || '';
  // Check if path has a file extension (contains a dot followed by characters at the end)
  // AND doesn't look like a folder (e.g., "folder.jpg" is ambiguous, but "file.jpg" is likely a file)
  // For now, just check if it ends with an extension
  return /\.\w+$/.test(sharePath);
});

// Extract filename from share path for file shares
const shareFileName = computed(() => {
  if (!isFileShare.value) return '';
  const sharePath = props.shareInfo?.path || '';
  // Remove "shared/" or "private/username/" prefix and return just the filename
  const parts = sharePath.split('/');
  return parts[parts.length - 1] || '';
});

// Track if we're viewing a root file (the shared file itself) vs a nested file
const isViewingRootFile = computed(() => {
  return isFileShare.value && (!currentPath.value || currentPath.value === '') && viewedFile.value === shareFileName.value;
});

// Sync route -> context
watch(
  () => [route.params.pathMatch, route.params.shareId, route.path],
  ([pathMatch, shareIdParam, routePath]) => {
    // Make sure we're on the right share
    if (shareIdParam && shareIdParam !== props.shareId) return;
    
    let pathFromRoute = '';
    
    // Handle pathMatch (could be undefined, string, or array)
    if (pathMatch !== undefined && pathMatch !== null && pathMatch !== '') {
      if (Array.isArray(pathMatch)) {
        pathFromRoute = pathMatch
          .filter(Boolean)
          .map(segment => decodeURIComponent(String(segment)))
          .join('/');
      } else {
        pathFromRoute = decodeURIComponent(String(pathMatch));
      }
    }
    
    pathFromRoute = pathFromRoute.replace(/\\/g, '/');
    
    // If it's a file share and no path from route, automatically show the shared file
    if (isFileShare.value && (!pathFromRoute || pathFromRoute === '')) {
      viewedFile.value = shareFileName.value || '';
      currentPath.value = '';
      displayedPath.value = shareFileName.value || '';
      console.log('GuestFileManager: File share at root, showing file:', shareFileName.value);
      return;
    }
    
    // For guest mode, check if the path looks like a file
    const isFile = pathFromRoute && /\.\w+$/.test(pathFromRoute);
    
    if (isFile && pathFromRoute) {
      viewedFile.value = pathFromRoute;
      const pathParts = pathFromRoute.split("/").filter(Boolean);
      if (pathParts.length > 1) {
        pathParts.pop();
        currentPath.value = pathParts.join("/");
      } else {
        currentPath.value = "";
      }
    } else {
      viewedFile.value = null;
      currentPath.value = pathFromRoute || '';
    }
    
    displayedPath.value = viewedFile.value || currentPath.value || '';
    console.log('GuestFileManager route sync:', { pathMatch, pathFromRoute, viewedFile: viewedFile.value, currentPath: currentPath.value, isFileShare: isFileShare.value });
  },
  { immediate: true }
);

// Sync context -> route
watch(
  () => [viewedFile.value, currentPath.value],
  ([filePath, dirPath]) => {
    if (!isUserEditing) {
      const targetPath = filePath || dirPath || '';
      const encodedPath = targetPath
        .split("/")
        .filter(Boolean)
        .map(segment => encodeURIComponent(segment))
        .join("/");
      
      const newRoute = `/open/${props.shareId}${encodedPath ? '/' + encodedPath : ''}`;
      if (router.currentRoute.value.path !== newRoute) {
        router.push(newRoute);
      }
    }
  }
);

// Reset search when location changes
watch(
  () => currentPath.value,
  () => {
    searchQuery.value = '';
    searchResults.value = [];
    isSearching.value = false;
    if (searchTimeout) {
      clearTimeout(searchTimeout);
      searchTimeout = null;
    }
  }
);

const handleMenuClick = () => {
  viewMode.value = viewMode.value === 'table' ? 'grid' : 'table';
};

const goHome = () => {
  viewedFile.value = null;
  currentPath.value = '';
};

const goUp = () => {
  if (viewedFile.value) {
    viewedFile.value = null;
  } else if (currentPath.value) {
    const pathParts = currentPath.value.split("/").filter(Boolean);
    if (pathParts.length > 0) {
      pathParts.pop();
      currentPath.value = pathParts.join("/");
    } else {
      currentPath.value = "";
    }
  }
};

const triggerRefresh = ref(0);
const triggerHierarchyRefresh = ref(0);

const refresh = () => {
  triggerRefresh.value += 1;
  triggerHierarchyRefresh.value += 1;
};

const goBack = () => {
  if (viewedFile.value) {
    viewedFile.value = null;
  } else {
    router.back();
  }
};

const goForward = () => {
  router.go(1);
};

const closeViewer = () => {
  viewedFile.value = null;
};

const handlePathChange = async (newPath: string) => {
  const normalizedPath = newPath.trim() || '';
  
  isUserEditing = true;
  displayedPath.value = normalizedPath;
  
  // For guest mode, we can't check if path exists easily
  // Just try to navigate to it
  const isFile = /\.\w+$/.test(normalizedPath);
  if (isFile) {
    viewedFile.value = normalizedPath;
    const pathParts = normalizedPath.split("/").filter(Boolean);
    if (pathParts.length > 1) {
      pathParts.pop();
      currentPath.value = pathParts.join("/");
    } else {
      currentPath.value = "";
    }
  } else {
    viewedFile.value = null;
    currentPath.value = normalizedPath;
  }
  
  isUserEditing = false;
};

const handleSearch = async (query: string) => {
  searchQuery.value = query;
  
  if (searchTimeout) {
    clearTimeout(searchTimeout);
    searchTimeout = null;
  }
  
  if (!query || !query.trim()) {
    isSearching.value = false;
    searchResults.value = [];
    return;
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      isSearching.value = true;
      const results = await api.searchSharedFiles(props.shareId, currentPath.value, query.trim());
      searchResults.value = results;
    } catch (err) {
      console.error('Search failed:', err);
      searchResults.value = [];
    } finally {
      isSearching.value = false;
    }
  }, 300);
};

const navigateToFolder = (path: string) => {
  viewedFile.value = null;
  currentPath.value = path;
};

const navigateToFile = (path: string) => {
  viewedFile.value = path;
  const pathParts = path.split("/").filter(Boolean);
  if (pathParts.length > 1) {
    pathParts.pop();
    currentPath.value = pathParts.join("/");
  } else {
    currentPath.value = "";
  }
};

const selectedFiles = ref<Set<string>>(new Set());
const selectedEntries = ref<Map<string, { name: string; is_dir: boolean }>>(new Map());
const setSelectedFiles = (files: Set<string>) => {
  selectedFiles.value = files;
};
const setSelectedEntries = (entries: Map<string, { name: string; is_dir: boolean }>) => {
  selectedEntries.value = entries;
};
</script>

<template>
  <div class="w-full h-full flex flex-col">
    <GuestActionsTab 
      :share-id="shareId"
      :share-info="shareInfo"
      :current-path="currentPath"
      :has-write-permission="hasWritePermission"
      :selected-files="selectedFiles"
      :selected-entries="selectedEntries"
      @refresh="refresh"
    />
    
    <!-- Path controls -->
    <div class="flex flex-col md:flex-row items-stretch gap-2 p-2 md:p-3 border-b border-b-neutral-200">
      <TextField
        mode="path"
        :path="displayedPath"
        :can-go-home="!isAtRoot"
        :can-go-up="!isAtRoot"
        :can-go-back="false"
        :can-go-forward="false"
        @go-home="goHome"
        @go-up="goUp"
        @refresh="refresh"
        @path-change="handlePathChange"
      />
      <div class="flex gap-2 items-stretch">
        <TextField mode="search" placeholder="Search..." :search-query="searchQuery" @search="handleSearch" />
        <PathButton @click="handleMenuClick">
          <IconMenu class="w-5 h-5 md:w-6 md:h-6 text-text-secondary stroke-2 z-20" />
        </PathButton>
      </div>
    </div>
    
    <div class="flex flex-row w-full flex-1 overflow-hidden">
      <!-- File viewer or file list -->
      <div v-if="viewedFile !== null" class="flex-1 flex flex-col overflow-hidden min-w-0">
        <div class="flex items-center justify-between px-2 md:px-4 py-2 border-b border-neutral-200 bg-neutral-50 shrink-0">
          <span class="text-xs md:text-sm text-neutral-700 truncate flex-1">{{ viewedFile || shareFileName }}</span>
          <button
            @click="closeViewer"
            class="ml-2 md:ml-4 px-2 md:px-3 py-1 text-xs md:text-sm text-neutral-700 hover:bg-neutral-200 rounded transition-colors"
          >
            Close
          </button>
        </div>
        <div class="max-h-[calc(100vh-14rem)] overflow-y-auto flex-1">
          <!-- For file shares at root: pass filename for type detection, but viewers will use empty path for API -->
          <!-- For folder shares: pass the full path as provided -->
          <FileViewer 
            v-if="viewedFile || (isFileShare && shareFileName)"
            :file-path="isViewingRootFile ? shareFileName : (viewedFile || '')"
            :share-id="shareId"
            :is-root-file-share="isViewingRootFile"
          />
        </div>
      </div>
      <div v-else-if="!isFileShare" class="max-h-[calc(100vh-11rem)] overflow-y-auto w-full flex-1">
        <GuestFileList 
          :share-id="shareId"
          :current-path="currentPath"
          :search-results="isSearching || searchQuery ? searchResults : undefined"
          :search-query="searchQuery"
          :view-mode="viewMode"
          :refresh-seq="triggerRefresh"
          @navigate-to-folder="navigateToFolder"
          @navigate-to-file="navigateToFile"
          @selected-files="setSelectedFiles"
          @selected-entries="setSelectedEntries"
        />
      </div>
      <div v-else class="max-h-[calc(100vh-11rem)] overflow-y-auto w-full flex-1 flex items-center justify-center">
        <div class="text-neutral-500">Loading file...</div>
      </div>
    </div>
  </div>
</template>
