<script setup lang="ts">
import { computed } from 'vue';
import type { HierarchyItem } from '@/types/hierarchy';
import FolderIcon from '@/assets/icons/folder-filled.svg';

interface Props {
	item: HierarchyItem;
	level: number;
	isExpanded: boolean;
	isSelected: boolean;
	expandedIds: Set<string>;
	selectedId?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
	'toggle-expand': [item: HierarchyItem];
	'item-click': [item: HierarchyItem];
}>();

const hasChildren = computed(() => {
	return props.item.type === 'folder' && props.item.children && props.item.children.length > 0;
});

const paddingLeft = computed(() => `calc(${props.level * 16}px + 12px)`);

const handleClick = () => {
	emit('item-click', props.item);
};

const handleExpandClick = (e: Event) => {
	e.stopPropagation();
	if (props.item.type === 'folder') {
		emit('toggle-expand', props.item);
	}
};

const isChildExpanded = (childId: string) => {
	return props.expandedIds.has(childId);
};

const isChildSelected = (childId: string) => {
	return props.selectedId === childId;
};
</script>

<template>
	<div>
		<div
			:class="[
				'flex items-center cursor-pointer rounded-md px-2 py-1 mx-2 transition-colors hover:bg-neutral-100',
				isSelected && 'bg-neutral-100',
			]"
			:style="{ paddingLeft }"
			@click="handleClick"
		>
			<!-- Expand/collapse triangle -->
			<div class="w-4 h-4 flex items-center justify-center mr-1" @click.stop="handleExpandClick">
				<svg
					v-if="item.type === 'folder' && hasChildren"
					:class="[
						'w-9 h-9 text-neutral-600 transition-transform duration-150',
						isExpanded ? 'rotate-90' : '',
					]"
					viewBox="0 0 24 24"
					fill="currentColor"
				>
					<path d="M9 7l8 5-8 5z" />
				</svg>
				<div v-else class="w-3 h-3"></div>
			</div>

			<!-- Folder icon -->
			<div v-if="item.type === 'folder'" class="w-5 h-5 mr-2 shrink-0">
				<FolderIcon class="w-full h-full text-secondary" />
			</div>

			<!-- Item name -->
			<span class="text-[14px] leading-6 text-neutral-800 select-none flex-1 truncate">
				{{ item.name }}
			</span>
		</div>

		<!-- Children (recursive) -->
		<template v-if="isExpanded && hasChildren && item.children">
			<HierarchyNode
				v-for="child in item.children"
				:key="child.id"
				:item="child"
				:level="level + 1"
				:is-expanded="isChildExpanded(child.id)"
				:is-selected="isChildSelected(child.id)"
				:expanded-ids="expandedIds"
				:selected-id="selectedId"
				@toggle-expand="$emit('toggle-expand', $event)"
				@item-click="$emit('item-click', $event)"
			/>
		</template>
	</div>
</template>

