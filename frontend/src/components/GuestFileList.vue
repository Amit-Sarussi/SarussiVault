<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import api from '@/services/api';
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
	path?: string;
};

interface Props {
	shareId: string;
	currentPath: string;
	searchResults?: Entry[];
	searchQuery?: string;
	viewMode?: 'table' | 'grid';
	refreshSeq?: number;
}

const props = withDefaults(defineProps<Props>(), {
	searchResults: undefined,
	searchQuery: '',
	viewMode: 'table',
	refreshSeq: 0,
});

const emit = defineEmits<{
	'navigate-to-folder': [path: string];
	'navigate-to-file': [path: string];
	'selected-files': [files: Set<string>];
	'selected-entries': [entries: Map<string, { name: string; is_dir: boolean }>];
}>();

const entries = ref<Entry[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const selectedKeys = ref<Set<string>>(new Set());
const lastSelectedKey = ref<string | null>(null);

// Track image loading states
const imageLoadingStates = ref<Map<string, boolean>>(new Map());
const imageLoadedStates = ref<Set<string>>(new Set());
const imageUrlsCache = ref<Map<string, string>>(new Map());

const sortedEntries = computed(() => {
	const sourceEntries = props.searchResults || entries.value;
	return [...sourceEntries].sort((a, b) => {
		if (a.is_dir !== b.is_dir) {
			return a.is_dir ? -1 : 1;
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
		? entry.path
		: joinPath(props.currentPath, entry.name) || entry.name;
	const url = api.getSharedFileUrl(props.shareId, fullPath);
	
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
	if (!imageLoadedStates.value.has(key)) {
		imageLoadingStates.value.set(key, true);
	}
};

const joinPath = (base: string, name: string) => {
	if (!base) return name;
	return `${base}/${name}`;
};

const entryKey = (entry: Entry) => {
	if (props.searchResults && entry.path) {
		return entry.path;
	}
	return joinPath(props.currentPath, entry.name) || entry.name;
};

const loadDirectory = async (path: string) => {
	loading.value = true;
	error.value = null;
	selectedKeys.value = new Set();
	lastSelectedKey.value = null;
	updateSelection();
	try {
		const data = await api.listSharedDirectory(props.shareId, path);
		entries.value = data;
	} catch (err: any) {
		console.error('Failed to load directory', err);
		// If it's a "Cannot list a file" error, it means this is a file share
		// and we shouldn't try to list it - this is expected behavior
		if (err.response?.status === 400 && err.response?.data?.detail?.includes('Cannot list a file')) {
			// Silently ignore - this is expected for file shares
			error.value = null;
			entries.value = [];
			return;
		}
		error.value = err.response?.data?.detail || 'Failed to load directory';
		entries.value = [];
	} finally {
		loading.value = false;
	}
};

const updateSelection = () => {
	const entriesMap = new Map<string, { name: string; is_dir: boolean }>();
	Array.from(selectedKeys.value).forEach(key => {
		const entry = sortedEntries.value.find(e => entryKey(e) === key);
		if (entry) {
			entriesMap.set(key, { name: entry.name, is_dir: entry.is_dir });
		}
	});
	emit('selected-files', selectedKeys.value);
	emit('selected-entries', entriesMap);
};

const selectSingle = (key: string) => {
	selectedKeys.value = new Set([key]);
	lastSelectedKey.value = key;
	updateSelection();
};

const handleRowClick = (entry: Entry, event: MouseEvent) => {
	const key = entryKey(entry);
	
	if (event.shiftKey) {
		// Range selection - simplified
		if (!lastSelectedKey.value) {
			selectSingle(key);
			return;
		}
		const sorted = sortedEntries.value;
		const startIndex = sorted.findIndex(e => entryKey(e) === lastSelectedKey.value);
		const endIndex = sorted.findIndex(e => entryKey(e) === key);
		if (startIndex !== -1 && endIndex !== -1) {
			const [from, to] = startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
			const next = new Set(selectedKeys.value);
			for (let i = from; i <= to; i++) {
				next.add(entryKey(sorted[i]));
			}
			selectedKeys.value = next;
			lastSelectedKey.value = key;
			updateSelection();
		}
		return;
	}
	
	if (event.ctrlKey || event.metaKey) {
		// Toggle selection
		const next = new Set(selectedKeys.value);
		if (next.has(key)) {
			next.delete(key);
		} else {
			next.add(key);
		}
		selectedKeys.value = next;
		lastSelectedKey.value = key;
		updateSelection();
		return;
	}
	
	// Single selection
	selectSingle(key);
};

const handleRowDoubleClick = (entry: Entry) => {
	if (props.searchResults && entry.path) {
		if (entry.is_dir) {
			emit('navigate-to-folder', entry.path);
		} else {
			emit('navigate-to-file', entry.path);
		}
	} else {
		if (entry.is_dir) {
			const newPath = joinPath(props.currentPath, entry.name);
			emit('navigate-to-folder', newPath);
		} else {
			const filePath = joinPath(props.currentPath, entry.name);
			emit('navigate-to-file', filePath);
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
		updateSelection();
	}
};

watch(
	() => props.currentPath,
	(path) => {
		if (!props.searchResults) {
			// Try to load directory, but catch errors gracefully
			loadDirectory(path).catch(err => {
				// If it's a "Cannot list a file" error, it means this is a file share
				// and we shouldn't try to list it - this is expected behavior
				if (err.response?.status === 400 && err.response?.data?.detail?.includes('Cannot list a file')) {
					// Silently ignore - this is expected for file shares
					return;
				}
				// Re-throw other errors
				throw err;
			});
		}
	},
	{ immediate: true }
);

watch(
	() => props.refreshSeq,
	() => {
		loadDirectory(props.currentPath);
	}
);

// Clear loading states when path changes (entries completely change)
watch(
	() => props.currentPath,
	() => {
		// Clear loading states but keep loaded states for browser cache
		imageLoadingStates.value = new Map();
	}
);
</script>

<template>
	<div class="h-full w-full bg-white overflow-auto" @click.capture="handleContainerClick">
		<div v-if="viewMode === 'table'" class="md:hidden">
			<div v-if="loading" class="px-3 py-4 text-neutral-500 text-sm">Loading...</div>
			<div v-else-if="error" class="px-3 py-4 text-red-800 text-sm">{{ error }}</div>
			<div v-else-if="sortedEntries.length === 0" class="px-3 py-4 text-neutral-500 text-center italic text-sm">
				{{ searchQuery ? `No results found for "${searchQuery}"` : 'This folder is empty' }}
			</div>
			<div v-else class="p-2 space-y-2">
				<div
					v-for="entry in sortedEntries"
					:key="entryKey(entry)"
					class="p-3 rounded-lg border border-neutral-200 cursor-pointer transition-colors"
					data-entry-row
					:class="selectedKeys.has(entryKey(entry)) ? 'bg-blue-50 border-blue-300' : 'hover:bg-blue-50'"
					@click="handleRowClick(entry, $event)"
					@dblclick="handleRowDoubleClick(entry)"
				>
					<div class="flex items-start gap-3">
						<component :is="iconFor(entry)" class="w-6 h-6 shrink-0 mt-0.5" :class="entry.is_dir ? 'text-secondary' : 'text-neutral-600'" />
						<div class="flex-1 min-w-0">
							<div class="font-medium text-sm text-neutral-800 truncate">{{ entry.name }}</div>
							<div class="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-xs text-neutral-600">
								<span>{{ formatDate(entry.mtime) }}</span>
								<span v-if="!entry.is_dir">{{ formatSize(entry.size) }}</span>
								<span>{{ entry.is_dir ? 'Folder' : 'File' }}</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		
		<table v-if="viewMode === 'table'" class="hidden md:table w-full text-sm">
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
					<td class="px-3 py-3 text-neutral-600">{{ entry.is_dir ? 'Folder' : 'File' }}</td>
					<td class="px-3 py-3 text-neutral-600 text-right">{{ entry.is_dir ? '' : formatSize(entry.size) }}</td>
				</tr>
			</tbody>
		</table>
		
		<!-- Grid View -->
		<div v-else class="p-2 md:p-4">
			<div v-if="loading" class="text-neutral-500 text-center py-8 text-sm md:text-base">Loading...</div>
			<div v-else-if="error" class="text-red-800 text-center py-8 text-sm md:text-base">{{ error }}</div>
			<div v-else-if="sortedEntries.length === 0" class="text-neutral-500 text-center py-8 italic text-sm md:text-base">
				{{ searchQuery ? `No results found for "${searchQuery}"` : 'This folder is empty' }}
			</div>
			<div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-2 md:gap-0">
				<!-- Image files - show only the image, no metadata -->
				<div
					v-for="entry in imageEntries"
					v-memo="[entryKey(entry), selectedKeys.has(entryKey(entry)), imageLoadedStates.has(entryKey(entry))]"
					:key="entryKey(entry)"
					class="w-full aspect-square overflow-hidden border border-neutral-200 hover:border-blue-300 cursor-pointer transition-colors relative bg-neutral-100 md:border-0"
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
					class="w-full aspect-square flex flex-col items-center justify-center border border-neutral-200 hover:bg-blue-50 cursor-pointer transition-colors md:border-0"
					data-entry-row
					:class="selectedKeys.has(entryKey(entry)) ? 'bg-blue-50 border-blue-300' : ''"
					@click="handleRowClick(entry, $event)"
					@dblclick="handleRowDoubleClick(entry)"
				>
					<!-- Icon for non-image files/folders -->
					<div class="mb-1 md:mb-2 bg-neutral-100 flex items-center justify-center w-12 h-12 md:w-16 md:h-16">
						<component
							:is="iconFor(entry)"
							class="w-8 h-8 md:w-12 md:h-12"
							:class="entry.is_dir ? 'text-blue-600' : 'text-neutral-600'"
						/>
					</div>
					<!-- File/Folder name and metadata -->
					<div class="w-full text-center px-1 md:px-2">
						<div class="text-xs md:text-sm font-medium text-neutral-800 truncate w-full" :title="entry.name">
							{{ entry.name }}
						</div>
						<div class="text-[10px] md:text-xs text-neutral-500 mt-0.5 md:mt-1 hidden sm:block">
							{{ formatDate(entry.mtime) }}
						</div>
						<div v-if="!entry.is_dir" class="text-[10px] md:text-xs text-neutral-500 hidden sm:block">
							{{ formatSize(entry.size) }}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
