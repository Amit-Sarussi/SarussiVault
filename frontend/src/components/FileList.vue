<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import api from '@/services/api';
import { useAppContext } from '@/context/appContext';
import { useNavigation } from '@/composables/useNavigation';
import { getViewType } from '@/utils/fileTypes';
import FolderIcon from '@/assets/icons/folder-filled.svg';
import FileIcon from '@/assets/icons/file.svg';
import ImageIcon from '@/assets/icons/image.svg';
import VideoIcon from '@/assets/icons/video.svg';

type Entry = {
	name: string;
	is_dir: boolean;
	size: number;
	mtime: number;
	path?: string; // Full path for search results
};

interface Props {
	searchResults?: Entry[];
	searchQuery?: string;
	viewMode?: 'table' | 'grid';
}

const props = withDefaults(defineProps<Props>(), {
	searchResults: undefined,
	searchQuery: '',
	viewMode: 'table',
});

const { currentPath, refreshSeq, storageType, setSelectedFiles, setSelectedEntries, currentUsername } = useAppContext();
const { navigateToFolder, navigateToFile } = useNavigation();

const entries = ref<Entry[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const selectedKeys = ref<Set<string>>(new Set());
const lastSelectedKey = ref<string | null>(null);
const containerRef = ref<HTMLElement | null>(null);
let singleClickTimer: ReturnType<typeof setTimeout> | null = null;

// Track image loading states - optimized for performance
const imageLoadingStates = ref<Map<string, boolean>>(new Map());
const imageLoadedStates = ref<Set<string>>(new Set());
const imageUrlsCache = ref<Map<string, string>>(new Map());

// Normalize path by removing storage prefix (for search results)
const normalizeSearchPath = (path: string): string => {
	if (!path) return '';
	let normalized = path.replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
	const lower = normalized.toLowerCase();
	
	// Remove shared/ prefix
	if (lower.startsWith('shared/')) {
		normalized = normalized.substring(7);
	} else if (lower === 'shared') {
		normalized = '';
	}
	
	// Remove users/username/ prefix
	const lowerAfterShared = normalized.toLowerCase();
	if (lowerAfterShared.startsWith('users/')) {
		const parts = normalized.split('/');
		if (parts.length >= 3 && parts[0].toLowerCase() === 'users') {
			normalized = parts.slice(2).join('/');
		} else if (parts.length <= 2) {
			normalized = '';
		}
	}
	
	// Remove private/ prefix
	const lowerFinal = normalized.toLowerCase();
	if (lowerFinal.startsWith('private/')) {
		normalized = normalized.substring(8);
	} else if (lowerFinal === 'private') {
		normalized = '';
	}
	
	return normalized;
};

const sortedEntries = computed(() => {
	// Use search results if provided, otherwise use regular entries
	const sourceEntries = props.searchResults || entries.value;
	return [...sourceEntries].sort((a, b) => {
		if (a.is_dir !== b.is_dir) {
			return a.is_dir ? -1 : 1; // folders first
		}
		return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
	});
});

// Memoize filtered entries for performance
const imageEntries = computed(() => {
	const entries = sortedEntries.value;
	const images: Entry[] = [];
	for (let i = 0; i < entries.length; i++) {
		if (isImage(entries[i])) {
			images.push(entries[i]);
		}
	}
	return images;
});

const nonImageEntries = computed(() => {
	const entries = sortedEntries.value;
	const nonImages: Entry[] = [];
	for (let i = 0; i < entries.length; i++) {
		if (!isImage(entries[i])) {
			nonImages.push(entries[i]);
		}
	}
	return nonImages;
});

const formatDate = (epochSeconds: number) => {
	const date = new Date(epochSeconds * 1000);
	// e.g., 26/1/2023 5:54 am
	const day = date.getDate();
	const month = date.getMonth() + 1;
	const year = date.getFullYear();
	const time = date.toLocaleTimeString(undefined, {
		hour: 'numeric',
		minute: '2-digit',
		hour12: true,
	});
	return `${day}/${month}/${year} ${time.toLowerCase()}`;
};

const formatSize = (bytes: number) => {
	if (bytes === 0) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(1024));
	const value = bytes / 1024 ** i;
	const fixed = value >= 10 || value % 1 === 0 ? value.toFixed(0) : value.toFixed(1);
	return `${fixed} ${units[i]}`;
};

const iconFor = (entry: Entry) => {
	if (entry.is_dir) return FolderIcon;
	const lower = entry.name.toLowerCase();
	if (/\.(png|jpe?g|gif|bmp|webp|svg)$/i.test(lower)) return ImageIcon;
	if (/\.(mp4|mov|avi|mkv|webm|m4v)$/i.test(lower)) return VideoIcon;
	return FileIcon;
};

const isImage = (entry: Entry) => {
	if (entry.is_dir) return false;
	return getViewType(entry.name) === 'image';
};

const getImageUrl = (entry: Entry) => {
	if (!isImage(entry)) return null;
	const key = entryKey(entry);
	
	// Return cached URL if available
	if (imageUrlsCache.value.has(key)) {
		return imageUrlsCache.value.get(key)!;
	}
	
	const fullPath = props.searchResults && entry.path
		? normalizeSearchPath(entry.path)
		: joinPath(currentPath.value, entry.name) || entry.name;
	const url = api.getFileUrl(fullPath, storageType.value);
	
	// Cache the URL
	imageUrlsCache.value.set(key, url);
	return url;
};

// Memoized loading check for performance
const isImageLoading = (entry: Entry) => {
	const key = entryKey(entry);
	// If already loaded, never show loading
	if (imageLoadedStates.value.has(key)) {
		return false;
	}
	// Only show loading if explicitly marked as loading (not just "unknown")
	// This prevents unnecessary placeholders for images that load instantly from cache
	return imageLoadingStates.value.get(key) === true;
};

const handleImageLoad = (entry: Entry, event: Event) => {
	const key = entryKey(entry);
	imageLoadingStates.value.set(key, false);
	imageLoadedStates.value.add(key);
};

const handleImageError = (entry: Entry, event: Event) => {
	const key = entryKey(entry);
	imageLoadingStates.value.set(key, false);
	(event.target as HTMLImageElement).style.display = 'none';
};

const handleImageLoadStart = (entry: Entry) => {
	const key = entryKey(entry);
	// Only set loading state if image hasn't loaded yet
	// This helps show placeholder for slow-loading images
	if (!imageLoadedStates.value.has(key)) {
		imageLoadingStates.value.set(key, true);
	}
};

const joinPath = (base: string, name: string) => {
	if (!base) return name;
	return `${base}/${name}`;
};

const entryKey = (entry: Entry) => {
	// For search results, use the normalized path
	if (props.searchResults && entry.path) {
		return normalizeSearchPath(entry.path);
	}
	// For regular entries, use current path + name
	return joinPath(currentPath.value, entry.name) || entry.name;
};

const loadDirectory = async (path: string) => {
	loading.value = true;
	error.value = null;
	selectedKeys.value = new Set();
	lastSelectedKey.value = null;
	setSelectedFiles(selectedKeys.value);
	updateSelectedEntries();
	try {
		const data = await api.listDirectory(path, storageType.value);
		entries.value = data;
	} catch (err) {
		console.error('Failed to load directory', err);
		error.value = 'Failed to load directory';
	} finally {
		loading.value = false;
	}
};

const selectSingle = (key: string) => {
	selectedKeys.value = new Set([key]);
	lastSelectedKey.value = key;
	setSelectedFiles(selectedKeys.value);
	updateSelectedEntries();
};

const updateSelectedEntries = () => {
	const entriesMap = new Map<string, { name: string; is_dir: boolean }>();
	Array.from(selectedKeys.value).forEach(key => {
		const entry = sortedEntries.value.find(e => entryKey(e) === key);
		if (entry) {
			entriesMap.set(key, { name: entry.name, is_dir: entry.is_dir });
		}
	});
	setSelectedEntries(entriesMap);
};

const toggleSelection = (key: string) => {
	const next = new Set(selectedKeys.value);
	if (next.has(key)) {
		next.delete(key);
	} else {
		next.add(key);
	}
	selectedKeys.value = next;
	lastSelectedKey.value = key;
	setSelectedFiles(selectedKeys.value);
	updateSelectedEntries();
};

const selectRange = (key: string) => {
	if (!lastSelectedKey.value) {
		selectSingle(key);
		return;
	}

	const sorted = sortedEntries.value;
	const startIndex = sorted.findIndex((entry) => entryKey(entry) === lastSelectedKey.value);
	const endIndex = sorted.findIndex((entry) => entryKey(entry) === key);

	if (startIndex === -1 || endIndex === -1) {
		selectSingle(key);
		return;
	}

	const [from, to] = startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
	const next = new Set(selectedKeys.value);
	for (let i = from; i <= to; i += 1) {
		next.add(entryKey(sorted[i]));
	}
	selectedKeys.value = next;
	lastSelectedKey.value = key;
	setSelectedFiles(selectedKeys.value);
	updateSelectedEntries();
};

const handleRowClick = (entry: Entry, event: MouseEvent) => {
	const key = joinPath(currentPath.value, entry.name) || entry.name;

	if (event.shiftKey) {
		selectRange(key);
		return;
	}

	if (event.ctrlKey || event.metaKey) {
		toggleSelection(key);
		return;
	}

	// Clear any pending single-click navigation
	if (singleClickTimer) {
		clearTimeout(singleClickTimer);
		singleClickTimer = null;
	}

	const isSingleSelected = selectedKeys.value.size === 1 && selectedKeys.value.has(key);
	if (isSingleSelected && entry.is_dir) {
		// Delay navigation to allow double-click to cancel it
		singleClickTimer = setTimeout(() => {
			// For search results, use the normalized path
			if (props.searchResults && entry.path) {
				const normalizedPath = normalizeSearchPath(entry.path);
				navigateToFolder(normalizedPath);
			} else {
				const newPath = joinPath(currentPath.value, entry.name);
				navigateToFolder(newPath);
			}
			singleClickTimer = null;
		}, 300); // 300ms delay - double-click typically fires within 200-300ms
		return;
	}

	selectSingle(key);
};

const handleRowDoubleClick = (entry: Entry) => {
	// Cancel any pending single-click navigation
	if (singleClickTimer) {
		clearTimeout(singleClickTimer);
		singleClickTimer = null;
	}

	// For search results, use the normalized path
	if (props.searchResults && entry.path) {
		const normalizedPath = normalizeSearchPath(entry.path);
		if (entry.is_dir) {
			navigateToFolder(normalizedPath);
		} else {
			navigateToFile(normalizedPath);
		}
	} else {
		// For regular entries, use current path + name
		if (entry.is_dir) {
			const newPath = joinPath(currentPath.value, entry.name);
			navigateToFolder(newPath);
		} else {
			// Open file for viewing
			const filePath = joinPath(currentPath.value, entry.name);
			navigateToFile(filePath);
		}
	}
};

const handleContainerClick = (event: MouseEvent) => {
	const target = event.target as HTMLElement | null;
	if (!target) return;

	const row = target.closest('[data-entry-row]');
	if (!row) {
		selectedKeys.value = new Set();
		lastSelectedKey.value = null;
		setSelectedFiles(selectedKeys.value);
		updateSelectedEntries();
	}
};

const handleOutsideClick = (event: MouseEvent) => {
	if (!containerRef.value) return;
	if (!containerRef.value.contains(event.target as Node)) {
		selectedKeys.value = new Set();
		lastSelectedKey.value = null;
		setSelectedFiles(selectedKeys.value);
		updateSelectedEntries();
	}
};

onMounted(() => {
	document.addEventListener('click', handleOutsideClick);
});

onBeforeUnmount(() => {
	document.removeEventListener('click', handleOutsideClick);
});

watch(
	() => currentPath.value,
	(path) => {
		// Only load directory if not showing search results
		if (!props.searchResults) {
			loadDirectory(path);
		}
	},
	{ immediate: true }
);

watch(
	() => refreshSeq.value,
	() => {
		loadDirectory(currentPath.value);
	}
);

// Clear loading states when path changes (entries completely change)
watch(
	() => currentPath.value,
	() => {
		// Clear loading states but keep loaded states for browser cache
		imageLoadingStates.value = new Map();
	}
);
</script>

<template>
	<div ref="containerRef" class="h-full w-full bg-white overflow-auto" @click.capture="handleContainerClick">
		<!-- Table View -->
		<table v-if="viewMode === 'table'" class="w-full text-sm">
			<thead class="sticky top-0 bg-neutral-50 border-b border-neutral-200 text-neutral-800">
				<tr>
					<th class="text-left font-medium px-3 py-3">Name</th>
					<th class="text-left font-medium px-3 py-3">Date modified</th>
					<th class="text-left font-medium px-3 py-3">Type</th>
					<th class="text-right font-medium px-3 py-3">Size</th>
				</tr>
			</thead>
			<tbody>
				<tr v-if="loading">
					<td colspan="4" class="px-3 py-4 text-neutral-500">Loading...</td>
				</tr>
				<tr v-else-if="error">
					<td colspan="4" class="px-3 py-4 text-red-800">{{ error }}</td>
				</tr>
				<tr v-else-if="sortedEntries.length === 0">
					<td colspan="4" class="px-3 py-4 text-neutral-500 text-center italic">
						{{ searchQuery ? `No results found for "${searchQuery}"` : 'This folder is empty' }}
					</td>
				</tr>
				<tr
					v-for="entry in sortedEntries"
					v-else
					:key="entryKey(entry)"
					class="hover:bg-blue-50 cursor-pointer border-b border-neutral-200"
					data-entry-row
					:class="selectedKeys.has(entryKey(entry)) ? 'bg-blue-50' : ''"
					@click="handleRowClick(entry, $event)"
					@dblclick="handleRowDoubleClick(entry)"
				>
					<td class="px-3">
						<div class="flex items-center gap-2 overflow-hidden">
							<component :is="iconFor(entry)" class="w-5 h-5 shrink-0" :class="entry.is_dir ? 'text-secondary' : 'text-neutral-600'" />
							<span class="truncate">{{ entry.name }}</span>
						</div>
					</td>
					<td class="px-3 py-3 text-neutral-600">{{ formatDate(entry.mtime) }}</td>
					<td class="px-3 py-3 text-neutral-600">
						{{ entry.is_dir ? 'Folder' : 'File' }}
					</td>
					<td class="px-3 py-3 text-neutral-600 text-right">{{ entry.is_dir ? '' : formatSize(entry.size) }}</td>
				</tr>
			</tbody>
		</table>

		<!-- Grid View -->
		<div v-else class="p-4">
			<div v-if="loading" class="text-neutral-500 text-center py-8">Loading...</div>
			<div v-else-if="error" class="text-red-800 text-center py-8">{{ error }}</div>
			<div v-else-if="sortedEntries.length === 0" class="text-neutral-500 text-center py-8 italic">
				{{ searchQuery ? `No results found for "${searchQuery}"` : 'This folder is empty' }}
			</div>
			<div v-else class="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-0">
				<!-- Image files - show only the image, no metadata -->
				<div
					v-for="entry in imageEntries"
					v-memo="[entryKey(entry), selectedKeys.has(entryKey(entry)), imageLoadedStates.has(entryKey(entry))]"
					:key="entryKey(entry)"
					class="w-full aspect-square overflow-hidden border border-neutral-200 hover:border-blue-300 cursor-pointer transition-colors relative bg-neutral-100"
					data-entry-row
					:class="selectedKeys.has(entryKey(entry)) ? 'border-blue-500 ring-2 ring-blue-200' : ''"
					@click="handleRowClick(entry, $event)"
					@dblclick="handleRowDoubleClick(entry)"
				>
					<!-- Loading placeholder -->
					<div
						v-if="isImageLoading(entry)"
						class="absolute inset-0 bg-neutral-200 animate-pulse"
					></div>
					<!-- Image -->
					<img
						:src="getImageUrl(entry)"
						:alt="entry.name"
						class="w-full h-full object-cover"
						loading="lazy"
						decoding="async"
						@load="handleImageLoad(entry, $event)"
						@error="handleImageError(entry, $event)"
					/>
				</div>
				<!-- Non-image files/folders - show with metadata -->
				<div
					v-for="entry in nonImageEntries"
					v-memo="[entryKey(entry), selectedKeys.has(entryKey(entry))]"
					:key="entryKey(entry)"
					class="w-full aspect-square flex flex-col items-center justify-center border border-neutral-200 hover:bg-blue-50 cursor-pointer transition-colors"
					data-entry-row
					:class="selectedKeys.has(entryKey(entry)) ? 'bg-blue-50 border-blue-300' : ''"
					@click="handleRowClick(entry, $event)"
					@dblclick="handleRowDoubleClick(entry)"
				>
					<!-- Icon for non-image files/folders -->
					<div class="mb-2 bg-neutral-100 flex items-center justify-center w-16 h-16">
						<component
							:is="iconFor(entry)"
							class="w-12 h-12"
							:class="entry.is_dir ? 'text-blue-600' : 'text-neutral-600'"
						/>
					</div>
					<!-- File/Folder name and metadata -->
					<div class="w-full text-center px-2">
						<div class="text-sm font-medium text-neutral-800 truncate w-full" :title="entry.name">
							{{ entry.name }}
						</div>
						<div class="text-xs text-neutral-500 mt-1">
							{{ formatDate(entry.mtime) }}
						</div>
						<div v-if="!entry.is_dir" class="text-xs text-neutral-500">
							{{ formatSize(entry.size) }}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
