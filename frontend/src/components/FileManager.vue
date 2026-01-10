<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import ActionsTab from "./ActionsTab.vue";
import TextField from "./TextField.vue";
import PathButton from "./PathButton.vue";
import IconMenu from "@/assets/icons/menu.svg";
import FileHierarchy from "./FileHierarchy.vue";
import FileList from "./FileList.vue";
import FileViewer from "./FileViewer.vue";
import { useAppContext } from "@/context/appContext";
import { useNavigation } from "@/composables/useNavigation";
import { useRouter } from "vue-router";
import api from "@/services/api";
import { getViewType } from "@/utils/fileTypes";

const { currentPath, triggerRefresh, triggerHierarchyRefresh, viewedFile, storageType } = useAppContext();
const { navigateHome, navigateUp, closeFileViewer, navigateToFolder, navigateToFile } = useNavigation();
const router = useRouter();

// Computed property to get the viewed file path (handles null case and type narrowing)
const viewedFilePath = computed(() => {
	const path = viewedFile.value;
	return path || null;
});

// Track the displayed path (may be invalid if user typed invalid path)
const displayedPath = ref<string>(viewedFile.value || currentPath.value || '/');
let isUserEditing = false;

// Search state
const searchQuery = ref<string>('');
const searchResults = ref<any[]>([]);
const isSearching = ref<boolean>(false);
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

// View mode state (table or grid)
const viewMode = ref<'table' | 'grid'>('table');

// Track navigation history for back/forward buttons
const canGoBack = ref<boolean>(false);
const canGoForward = ref<boolean>(false);

// Check if we're at root (empty path)
const isAtRoot = computed(() => !currentPath.value || currentPath.value === '');

// Update back/forward button states
const updateHistoryState = () => {
	// Check if we can go back (if viewing a file, we can go back to folder view)
	canGoBack.value = !!viewedFile.value || window.history.length > 1;
	
	// For forward, we'd need to track our own history or use a more complex approach
	// For now, we'll use a simple heuristic: if we just navigated, we might be able to go forward
	// This is a simplified approach - a full implementation would track navigation history
	canGoForward.value = false; // Disable forward for now as it's complex to track accurately
};

// Update displayed path when current path or viewed file changes (but not if user is editing)
watch(
	() => [viewedFile.value, currentPath.value],
	([newFile, newPath]) => {
		// Only update if not currently editing and path actually changed
		if (!isUserEditing) {
			const newDisplayPath = newFile || newPath || '/';
			if (displayedPath.value !== newDisplayPath) {
				displayedPath.value = newDisplayPath;
			}
		}
		// Update history state when path or viewed file changes
		updateHistoryState();
	}
);

// Reset search when location changes
watch(
	() => [currentPath.value, storageType.value],
	() => {
		// Clear search query and results when navigating to a different folder or storage type
		searchQuery.value = '';
		searchResults.value = [];
		isSearching.value = false;
		// Clear any pending search timeout
		if (searchTimeout) {
			clearTimeout(searchTimeout);
			searchTimeout = null;
		}
	}
);

const handleMenuClick = () => {
	// Toggle between table and grid view
	viewMode.value = viewMode.value === 'table' ? 'grid' : 'table';
};

const goHome = () => {
	navigateHome();
	setTimeout(updateHistoryState, 100);
};
const goUp = () => {
	navigateUp();
	setTimeout(updateHistoryState, 100);
};
const refresh = () => {
	triggerRefresh();
	triggerHierarchyRefresh();
};

const goBack = () => {
	if (viewedFile.value) {
		closeFileViewer();
	} else {
		router.back();
	}
	// Update history state after navigation
	setTimeout(updateHistoryState, 100);
};
const goForward = () => {
	router.go(1);
	// Update history state after navigation
	setTimeout(updateHistoryState, 100);
};
const closeViewer = closeFileViewer;

const handlePathChange = async (newPath: string) => {
	// Normalize the path
	const normalizedPath = newPath.trim() || '/';
	
	// Store the previous valid path before checking
	const previousValidPath = viewedFile.value || currentPath.value || '/';
	
	isUserEditing = true;
	// Update displayed path immediately (so user sees what they typed)
	displayedPath.value = normalizedPath;
	
	// Check if path exists
	const exists = await api.pathExists(normalizedPath, storageType.value);
	
	if (exists) {
		// Path exists - navigate to it
		const isFile = /\.\w+$/.test(normalizedPath) || getViewType(normalizedPath) !== 'binary';
		if (isFile) {
			navigateToFile(normalizedPath);
		} else {
			navigateToFolder(normalizedPath);
		}
		// Allow watch to update displayedPath when navigation completes
		isUserEditing = false;
	} else {
		// Path doesn't exist - reset to previous valid path
		displayedPath.value = previousValidPath;
		isUserEditing = false;
	}
};

const handleSearch = async (query: string) => {
	searchQuery.value = query;
	
	// Clear previous timeout
	if (searchTimeout) {
		clearTimeout(searchTimeout);
		searchTimeout = null;
	}
	
	// If query is empty, clear search results
	if (!query || !query.trim()) {
		isSearching.value = false;
		searchResults.value = [];
		return;
	}
	
	// Debounce search - wait 300ms after user stops typing
	searchTimeout = setTimeout(async () => {
		try {
			isSearching.value = true;
			// Search within the current folder
			const results = await api.searchFiles(currentPath.value, query.trim(), storageType.value);
			searchResults.value = results;
		} catch (error) {
			console.error('Search failed:', error);
			searchResults.value = [];
		} finally {
			isSearching.value = false;
		}
	}, 300);
};

// Initialize history state on mount
onMounted(() => {
	updateHistoryState();
});
</script>

<template>
	<div class="w-full h-full flex flex-col">
		<ActionsTab />
		<div class="flex items-stretch gap-2 p-3 border-b border-b-neutral-200">
			<TextField
				mode="path"
				:path="displayedPath"
				:can-go-home="!isAtRoot"
				:can-go-up="!isAtRoot"
				:can-go-back="canGoBack"
				:can-go-forward="canGoForward"
				@go-home="goHome"
				@go-up="goUp"
				@refresh="refresh"
				@go-back="goBack"
				@go-forward="goForward"
				@path-change="handlePathChange"
			/>
			<TextField mode="search" placeholder="Search..." :search-query="searchQuery" @search="handleSearch" />
			<PathButton @click="handleMenuClick">
				<IconMenu class="w-6 h-6 text-text-secondary stroke-2 z-20" />
			</PathButton>
		</div>
		<div class="flex flex-row w-full flex-1">
			<div class="w-100 max-h-[calc(100vh-11rem)] overflow-y-auto border-r border-r-neutral-200">
				<FileHierarchy />
			</div>
			<div v-if="viewedFilePath" class="flex-1 flex flex-col overflow-hidden min-w-0">
				<div class="flex items-center justify-between px-4 py-2 border-b border-neutral-200 bg-neutral-50 shrink-0">
					<span class="text-sm text-neutral-700 truncate flex-1">{{ viewedFilePath }}</span>
					<button
						@click="closeViewer"
						class="ml-4 px-3 py-1 text-sm text-neutral-700 hover:bg-neutral-200 rounded transition-colors"
					>
						Close
					</button>
				</div>
				<div class="max-h-[calc(100vh-14rem)] overflow-y-auto">
					<FileViewer :file-path="viewedFilePath" />
				</div>
			</div>
			<div v-else class="max-h-[calc(100vh-11rem)] overflow-y-auto w-full">
				<FileList :search-results="isSearching || searchQuery ? searchResults : undefined" :search-query="searchQuery" :view-mode="viewMode" />
			</div>
		</div>
	</div>
</template>
