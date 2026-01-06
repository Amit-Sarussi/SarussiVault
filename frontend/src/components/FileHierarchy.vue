<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import HierarchyNode from './HierarchyNode.vue';
import type { HierarchyItem } from '@/types/hierarchy';

interface Props {
	items?: HierarchyItem[];
	selectedId?: string;
}

const props = withDefaults(defineProps<Props>(), {
	items: () => [],
	selectedId: undefined,
});

const emit = defineEmits<{
	itemSelected: [id: string, item: HierarchyItem];
}>();

// Track expanded state for each folder
const expandedIds = ref<Set<string>>(new Set());

// Default sample data matching the design
const defaultItems: HierarchyItem[] = [
	{
		id: '1',
		name: 'Folder name',
		type: 'folder',
		children: [
			{
				id: '2',
				name: 'scripts',
				type: 'folder',
				children: [],
			},
			{
				id: '3',
				name: 'front-end',
				type: 'folder',
				children: [],
			},
			{
				id: '4',
				name: 'Web assets',
				type: 'folder',
				children: [
					{
						id: '5',
						name: 'logs',
						type: 'folder',
						children: [],
					},
					{
						id: '6',
						name: 'testfolder',
						type: 'folder',
						children: [],
					},
					{
						id: '7',
						name: 'public_html',
						type: 'folder',
						children: [],
					},
				],
			},
			{
				id: '8',
				name: 'backup_files',
				type: 'folder',
				children: [],
			},
			{
				id: '9',
				name: 'others',
				type: 'folder',
				children: [],
			},
			{
				id: '10',
				name: 'New folder',
				type: 'folder',
				children: [],
			},
		],
	},
];

const hierarchyItems = computed(() => props.items.length > 0 ? props.items : defaultItems);

// Initialize expanded state
const initializeExpandedState = () => {
	if (hierarchyItems.value.length > 0 && hierarchyItems.value[0].type === 'folder') {
		expandedIds.value.add(hierarchyItems.value[0].id);
		// Expand "Web assets" by default to match the design
		const webAssets = hierarchyItems.value[0].children?.find(child => child.name === 'Web assets');
		if (webAssets) {
			expandedIds.value.add(webAssets.id);
		}
	}
};

// Initialize on mount and watch for changes
onMounted(() => {
	initializeExpandedState();
});

watch(hierarchyItems, () => {
	if (expandedIds.value.size === 0) {
		initializeExpandedState();
	}
}, { immediate: true });

const toggleExpand = (item: HierarchyItem) => {
	if (item.type === 'folder') {
		if (expandedIds.value.has(item.id)) {
			expandedIds.value.delete(item.id);
		} else {
			expandedIds.value.add(item.id);
		}
	}
};

const isExpanded = (id: string) => expandedIds.value.has(id);

const handleItemClick = (item: HierarchyItem) => {
	emit('itemSelected', item.id, item);
	if (item.type === 'folder') {
		toggleExpand(item);
	}
};
</script>

<template>
	<div class="h-full w-64 overflow-y-auto border-r border-r-neutral-200 bg-white py-2">
		<HierarchyNode
			v-for="item in hierarchyItems"
			:key="item.id"
			:item="item"
			:level="0"
			:is-expanded="isExpanded(item.id)"
			:is-selected="selectedId === item.id"
			:expanded-ids="expandedIds"
			:selected-id="selectedId"
			@toggle-expand="toggleExpand"
			@item-click="handleItemClick"
		/>
	</div>
</template>
