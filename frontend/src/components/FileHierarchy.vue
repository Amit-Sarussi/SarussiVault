<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';
import api from '@/services/api';
import HierarchyNode from './HierarchyNode.vue';
import type { HierarchyItem } from '@/types/hierarchy';
import { useAppContext } from '@/context/appContext';
import { useNavigation } from '@/composables/useNavigation';

interface Props {
	selectedId?: string;
}

const props = withDefaults(defineProps<Props>(), {
	selectedId: undefined,
});

const emit = defineEmits<{
	itemSelected: [id: string, item: HierarchyItem];
}>();

const { currentPath, viewedFile, hierarchyRefreshSeq, storageType, currentUsername } = useAppContext();
const { navigateToFolder, navigateToFile, navigateHome } = useNavigation();

const expandedIds = ref<Set<string>>(new Set());
const hierarchyItems = ref<HierarchyItem[]>([]);
const selectedNodeId = ref<string | undefined>(undefined);

interface BackendHierarchyEntry {
	name: string;
	path: string;
	is_dir: boolean;
	children?: BackendHierarchyEntry[] | null;
}

// Normalize path by removing storage prefix
// Backend returns paths relative to ROOT_DIR, which include storage prefix
// Frontend paths don't include the storage prefix
const normalizeHierarchyPath = (path: string, storage: 'shared' | 'private', username?: string | null): string => {
	if (!path) return '';
	
	// First normalize path separators (handle Windows backslashes) and remove leading/trailing slashes
	let normalized = path.replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
	
	// Backend paths are relative to ROOT_DIR:
	// - Shared: "shared/folder/subfolder"
	// - Private: "users/username/folder/subfolder" or "private/folder/subfolder"
	
	// Remove shared/ prefix (case-insensitive check)
	const lowerPath = normalized.toLowerCase();
	if (lowerPath.startsWith('shared/')) {
		normalized = normalized.substring(7); // Remove "shared/"
	} else if (lowerPath === 'shared') {
		normalized = '';
	}
	
	// Remove private/ prefix (case-insensitive check)
	const lowerAfterShared = normalized.toLowerCase();
	if (lowerAfterShared.startsWith('private/')) {
		normalized = normalized.substring(8); // Remove "private/"
	} else if (lowerAfterShared === 'private') {
		normalized = '';
	}
	
	// Remove users/username/ prefix for private storage
	// Always check for users/ prefix regardless of storage type, because backend always returns it
	const lowerAfterPrivate = normalized.toLowerCase();
	if (lowerAfterPrivate.startsWith('users/')) {
		const parts = normalized.split('/');
		if (parts.length >= 3 && parts[0].toLowerCase() === 'users') {
			// Remove "users/username/" prefix (username is in parts[1])
			normalized = parts.slice(2).join('/');
		} else if (parts.length <= 2) {
			// If it's just "users" or "users/username", return empty
			normalized = '';
		}
	}
	
	return normalized;
};

// Additional safeguard: ensure path doesn't have storage prefixes before navigation
const ensureNormalizedPath = (path: string, storage: 'shared' | 'private', username?: string | null): string => {
	if (!path) return '';
	
	// Remove any storage prefixes that might have been missed
	// First, normalize path separators and remove leading/trailing slashes
	let normalized = path.replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
	
	// Remove shared/ prefix (case-insensitive)
	const lowerNormalized = normalized.toLowerCase();
	if (lowerNormalized.startsWith('shared/')) {
		normalized = normalized.substring(7);
	} else if (lowerNormalized === 'shared') {
		normalized = '';
	}
	
	// Remove users/username/ prefix (case-insensitive)
	// Check for users/ prefix regardless of storage type
	const lowerAfterShared = normalized.toLowerCase();
	if (lowerAfterShared.startsWith('users/')) {
		const parts = normalized.split('/');
		if (parts.length >= 3 && parts[0].toLowerCase() === 'users') {
			// Remove "users/username/" prefix
			normalized = parts.slice(2).join('/');
		} else if (parts.length <= 2) {
			// Just "users" or "users/username" -> empty
			normalized = '';
		}
	}
	
	// Also check for private/ prefix (in case backend uses that format)
	const lowerFinal = normalized.toLowerCase();
	if (lowerFinal.startsWith('private/')) {
		normalized = normalized.substring(8);
	} else if (lowerFinal === 'private') {
		normalized = '';
	}
	
	return normalized;
};

const toHierarchyItem = (entry: BackendHierarchyEntry): HierarchyItem => {
	// Normalize the path to match frontend path format (without storage prefix)
	// Use ensureNormalizedPath for extra safety to catch any edge cases
	let normalizedPath = normalizeHierarchyPath(entry.path, storageType.value, currentUsername.value);
	normalizedPath = ensureNormalizedPath(normalizedPath, storageType.value, currentUsername.value);
	
	const item: HierarchyItem = {
		id: normalizedPath || '/',
		path: normalizedPath,
		name: entry.name,
		type: entry.is_dir ? 'folder' : 'file',
		children: undefined,
	};
	
	// Recursively convert children if they exist
	if (entry.is_dir && entry.children !== undefined && entry.children !== null) {
		if (entry.children.length > 0) {
			item.children = entry.children.map(toHierarchyItem);
		} else {
			item.children = [];
		}
	}
	
	return item;
};

const updateSelection = () => {
	const targetPath = viewedFile.value || currentPath.value;
	
	// Normalize target path for comparison
	const normalizedTarget = normalizePathForComparison(targetPath || '');
	
	// If at root (empty path), select the root item
	if (!normalizedTarget || normalizedTarget === '') {
		selectedNodeId.value = '__root__';
		// Expand root to show its children
		expandedIds.value.add('__root__');
		return;
	}
	
	// Find the node path (all ancestors + the target node)
	const nodePath = findNodePath(normalizedTarget, hierarchyItems.value);
	if (nodePath && nodePath.length > 0) {
		const targetNode = nodePath[nodePath.length - 1];
		// Force reactivity by creating a new value
		selectedNodeId.value = targetNode.id;
		
		// Expand all parent folders so the file/folder is visible (including root)
		for (let i = 0; i < nodePath.length - 1; i++) {
			const parent = nodePath[i];
			if (parent.type === 'folder') {
				expandedIds.value.add(parent.id);
			}
		}
		// Also expand root if we found a path
		expandedIds.value.add('__root__');
	} else {
		// Node not found - debug logging
		console.log('[FileHierarchy] Selection update failed:', {
			targetPath,
			normalizedTarget,
			currentPath: currentPath.value,
			viewedFile: viewedFile.value,
			hierarchyItemsCount: hierarchyItems.value.length
		});
		// Select root as fallback
		selectedNodeId.value = '__root__';
		// Still expand root to show children
		expandedIds.value.add('__root__');
	}
};

	const loadFullHierarchy = async () => {
		try {
			const entries = await api.getHierarchy('', storageType.value);
			const mapped = entries.map(toHierarchyItem);
			
			// Create a root parent item
			const rootLabel = storageType.value === 'shared' 
				? 'Shared Storage' 
				: (currentUsername.value ? `${currentUsername.value}'s Storage` : 'My Storage');
			
			const rootItem: HierarchyItem = {
				id: '__root__',
				path: '',
				name: rootLabel,
				type: 'folder',
				children: mapped.length > 0 ? mapped : []
			};
			
			hierarchyItems.value = [rootItem];
			
			// Don't expand root by default - folders should be collapsed
			
			// After hierarchy loads, update selection to highlight current location
			// Use nextTick to ensure Vue has processed the hierarchy update
			setTimeout(() => {
				updateSelection();
			}, 0);
		} catch (err) {
			console.error('Failed to load hierarchy', err);
			hierarchyItems.value = [];
		}
	};

onMounted(async () => {
	await loadFullHierarchy();
});

// Watch for hierarchy refresh trigger
watch(
	() => hierarchyRefreshSeq.value,
	async () => {
		// Preserve expanded state
		const previouslyExpanded = new Set(expandedIds.value);
		await loadFullHierarchy();
		// Restore expanded state
		expandedIds.value = previouslyExpanded;
		// Update selection after hierarchy reloads
		updateSelection();
	}
);

// Watch for storage type or username changes to update root label
watch(
	() => [storageType.value, currentUsername.value],
	async () => {
		await loadFullHierarchy();
		// Update selection after storage type changes
		updateSelection();
	}
);

const openFolder = (item: HierarchyItem) => {
	if (item.type !== 'folder') return;
	if (expandedIds.value.has(item.id)) return;
	expandedIds.value.add(item.id);
};

const closeFolder = (item: HierarchyItem) => {
	if (item.type !== 'folder') return;
	expandedIds.value.delete(item.id);
};

const toggleExpand = (item: HierarchyItem) => {
	if (item.type !== 'folder') return;
	if (expandedIds.value.has(item.id)) {
		closeFolder(item);
	} else {
		openFolder(item);
	}
};

const isExpanded = (id: string) => expandedIds.value.has(id);

const handleItemClick = (item: HierarchyItem) => {
	if (item.id === '__root__') {
		// Root item clicked - navigate to home
		navigateHome();
		emit('itemSelected', item.id, item);
		// Selection will be updated by watcher
		return;
	}
	
	// Ensure path is normalized (remove any storage prefixes)
	// Double-check normalization even though it should already be normalized in toHierarchyItem
	const normalizedPath = ensureNormalizedPath(item.path, storageType.value, currentUsername.value);
	
	if (item.type === 'folder') {
		navigateToFolder(normalizedPath);
		emit('itemSelected', item.id, item);
		// Toggle expansion on click
		if (!expandedIds.value.has(item.id)) {
			openFolder(item);
		}
		// Selection will be updated by watcher after navigation
	} else {
		// For files, open them for viewing
		navigateToFile(normalizedPath);
		emit('itemSelected', item.id, item);
		// Selection will be updated by watcher after navigation
	}
};

// Normalize paths for comparison (handle trailing slashes, etc.)
const normalizePathForComparison = (path: string): string => {
	if (!path) return '';
	return path.replace(/\/+$/, ''); // Remove trailing slashes
};

// Helper function to find a node by path and return the path to it
const findNodePath = (targetPath: string, items: HierarchyItem[]): HierarchyItem[] | null => {
	const normalizedTarget = normalizePathForComparison(targetPath);
	
	for (const item of items) {
		// Skip root item in path search
		if (item.id === '__root__') {
			if (item.children) {
				const childPath = findNodePath(targetPath, item.children);
				if (childPath) {
					return [item, ...childPath];
				}
			}
			continue;
		}
		
		// Normalize both paths for comparison
		const normalizedItemPath = normalizePathForComparison(item.path);
		
		// Check for exact match first
		if (normalizedItemPath === normalizedTarget) {
			return [item];
		}
		
		// Check if target is a child of this item (for nested paths)
		// Only check children if the target path starts with this item's path
		if (normalizedTarget.startsWith(normalizedItemPath + '/')) {
			if (item.children) {
				const childPath = findNodePath(targetPath, item.children);
				if (childPath) {
					return [item, ...childPath];
				}
			}
		}
		
		// Recursively search children for any match
		if (item.children) {
			const childPath = findNodePath(targetPath, item.children);
			if (childPath) {
				return [item, ...childPath];
			}
		}
	}
	return null;
};

// Keep selection aligned with current path or viewed file
// This watcher ensures the hierarchy highlights the current location
watch(
	() => [currentPath.value, viewedFile.value, storageType.value],
	([newPath, newFile, newStorage]) => {
		// Only update selection if hierarchy is loaded
		if (hierarchyItems.value.length > 0) {
			// Use nextTick to ensure Vue has processed any reactive updates
			// This is especially important when navigating from other components
			setTimeout(() => {
				updateSelection();
			}, 50);
		}
	},
	{ immediate: true }
);
</script>

<template>
	<div class="h-full w-100 overflow-y-auto bg-white py-2">
		<HierarchyNode
			v-for="item in hierarchyItems"
			:key="item.id"
			:item="item"
			:level="0"
			:is-expanded="isExpanded(item.id)"
			:is-selected="selectedNodeId === item.id"
			:expanded-ids="expandedIds"
			:selected-id="selectedNodeId"
			@toggle-expand="toggleExpand"
			@item-click="handleItemClick"
		/>
	</div>
</template>
