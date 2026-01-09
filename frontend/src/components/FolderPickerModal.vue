<script setup lang="ts">
import { ref, watch } from 'vue';
import Modal from './Modal.vue';
import HierarchyNode from './HierarchyNode.vue';
import type { HierarchyItem } from '@/types/hierarchy';
import api from '@/services/api';
import type { StorageType } from '@/context/appContext';

const props = defineProps<{
	show: boolean;
	currentStorageType: StorageType;
	currentUsername: string | null;
}>();

const emit = defineEmits<{
	select: [path: string, storageType: StorageType];
	close: [];
}>();

const expandedIds = ref<Set<string>>(new Set());
const sharedHierarchy = ref<HierarchyItem[]>([]);
const privateHierarchy = ref<HierarchyItem[]>([]);
const selectedPath = ref<{ path: string; storageType: StorageType } | null>(null);
const loading = ref(true);

interface BackendHierarchyEntry {
	name: string;
	path: string;
	is_dir: boolean;
	children?: BackendHierarchyEntry[] | null;
}

const toHierarchyItem = (entry: BackendHierarchyEntry): HierarchyItem => {
	const item: HierarchyItem = {
		id: entry.path || '/',
		path: entry.path,
		name: entry.name,
		type: entry.is_dir ? 'folder' : 'file',
		children: undefined,
	};
	
	if (entry.is_dir && entry.children !== undefined && entry.children !== null) {
		if (entry.children.length > 0) {
			item.children = entry.children.map(toHierarchyItem);
		} else {
			item.children = [];
		}
	}
	
	return item;
};

const loadHierarchies = async () => {
	loading.value = true;
	try {
		// Load shared hierarchy
		const sharedEntries = await api.getHierarchy('', 'shared');
		sharedHierarchy.value = sharedEntries.map(toHierarchyItem);
		
		// Load private hierarchy
		const privateEntries = await api.getHierarchy('', 'private');
		privateHierarchy.value = privateEntries.map(toHierarchyItem);
		
		// Don't expand root folders by default - folders should be collapsed
	} catch (err) {
		console.error('Failed to load hierarchies', err);
	} finally {
		loading.value = false;
	}
};

const handleItemClick = (item: HierarchyItem) => {
	if (item.type === 'folder') {
		// Determine which storage this item belongs to
		const isShared = sharedHierarchy.value.some(h => findItemInHierarchy(h, item.id));
		selectedPath.value = {
			path: item.path,
			storageType: isShared ? 'shared' : 'private'
		};
	}
};

const handleRootClick = (storageType: StorageType) => {
	selectedPath.value = {
		path: '',
		storageType: storageType
	};
};

const findItemInHierarchy = (root: HierarchyItem, id: string): boolean => {
	if (root.id === id) return true;
	if (root.children) {
		return root.children.some(child => findItemInHierarchy(child, id));
	}
	return false;
};

const handleToggleExpand = (item: HierarchyItem) => {
	if (item.type === 'folder') {
		if (expandedIds.value.has(item.id)) {
			expandedIds.value.delete(item.id);
		} else {
			expandedIds.value.add(item.id);
		}
	}
};

const handleConfirm = () => {
	if (selectedPath.value) {
		emit('select', selectedPath.value.path, selectedPath.value.storageType);
	}
};

const handleCancel = () => {
	selectedPath.value = null;
	emit('close');
};

const isSelected = (item: HierarchyItem) => {
	if (!selectedPath.value) return false;
	// For root selection, check if path is empty and storage type matches
	if (selectedPath.value.path === '') {
		return false; // Root is handled separately with buttons
	}
	return item.id === selectedPath.value.path;
};

watch(() => props.show, (newVal) => {
	if (newVal) {
		loadHierarchies();
		selectedPath.value = null;
	}
}, { immediate: true });
</script>

<template>
	<Modal :show="show" title="Select Destination Folder" @close="handleCancel">
		<div class="flex flex-col gap-4 max-h-[60vh]">
			<div v-if="loading" class="text-center text-neutral-500 py-4">Loading folders...</div>
			<div v-else class="overflow-y-auto border border-neutral-200 rounded-md p-2">
				<!-- Shared Storage -->
				<div class="mb-4">
					<div class="text-sm font-semibold text-neutral-700 mb-2 px-2">Shared Storage</div>
					<button
						@click="handleRootClick('shared')"
						:class="[
							'w-full flex items-center gap-2 px-2 py-2 rounded-md mb-2 transition-colors text-left cursor-pointer',
							selectedPath?.path === '' && selectedPath?.storageType === 'shared'
								? 'bg-blue-50 text-blue-700'
								: 'hover:bg-neutral-100 text-neutral-700'
						]"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
						</svg>
						<span class="text-sm font-medium">Shared Storage (Root)</span>
					</button>
					<div v-if="sharedHierarchy.length === 0" class="text-sm text-neutral-500 px-2 py-1">No folders</div>
					<template v-else>
						<HierarchyNode
							v-for="item in sharedHierarchy"
							:key="item.id"
							:item="item"
							:level="0"
							:is-expanded="expandedIds.has(item.id)"
							:is-selected="isSelected(item)"
							:expanded-ids="expandedIds"
							:selected-id="selectedPath?.path"
							@toggle-expand="handleToggleExpand"
							@item-click="handleItemClick"
						/>
					</template>
				</div>
				
				<!-- Private Storage -->
				<div>
					<div class="text-sm font-semibold text-neutral-700 mb-2 px-2">Private Storage</div>
					<button
						@click="handleRootClick('private')"
						:class="[
							'w-full flex items-center gap-2 px-2 py-2 rounded-md mb-2 transition-colors text-left cursor-pointer',
							selectedPath?.path === '' && selectedPath?.storageType === 'private'
								? 'bg-blue-50 text-blue-700'
								: 'hover:bg-neutral-100 text-neutral-700'
						]"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
						</svg>
						<span class="text-sm font-medium">Private Storage (Root)</span>
					</button>
					<div v-if="privateHierarchy.length === 0" class="text-sm text-neutral-500 px-2 py-1">No folders</div>
					<template v-else>
						<HierarchyNode
							v-for="item in privateHierarchy"
							:key="item.id"
							:item="item"
							:level="0"
							:is-expanded="expandedIds.has(item.id)"
							:is-selected="isSelected(item)"
							:expanded-ids="expandedIds"
							:selected-id="selectedPath?.path"
							@toggle-expand="handleToggleExpand"
							@item-click="handleItemClick"
						/>
					</template>
				</div>
			</div>
			
			<div v-if="selectedPath" class="text-sm text-neutral-600 px-2">
				Selected: <span class="font-medium">{{ selectedPath.path || 'Root' }}</span>
			</div>
			
			<div class="flex justify-end gap-2">
				<button
					@click="handleCancel"
					class="px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100 rounded-md transition-colors cursor-pointer"
				>
					Cancel
				</button>
				<button
					@click="handleConfirm"
					:disabled="!selectedPath"
					class="px-4 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-md transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
				>
					Move Here
				</button>
			</div>
		</div>
	</Modal>
</template>
