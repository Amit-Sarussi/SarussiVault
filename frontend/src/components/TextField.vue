<script setup lang="ts">
import PathButton from "./PathButton.vue";
import IconHome from "@/assets/icons/home.svg"
import IconArrow from "@/assets/icons/arrow.svg"
import IconRefresh from "@/assets/icons/refresh.svg"
import IconMenu from "@/assets/icons/menu.svg"
import IconSearch from "@/assets/icons/search.svg"
import PathBar from "./PathBar.vue";

defineProps<{
	mode?: 'path' | 'search';
	path?: string;
	placeholder?: string;
}>();

const emit = defineEmits<{
	menuClick: [];
}>();

const handleMenuClick = () => {
	emit('menuClick');
};
</script>

<template>
	<div v-if="mode === 'path'" class="flex gap-2 items-stretch flex-1">
		<PathButton title="Main">
			<IconHome class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
		<PathButton>
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 rotate-180 z-20" />
		</PathButton>
		<PathButton>
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
		<PathButton>
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 -rotate-90 z-20" />
		</PathButton>
		<PathButton>
			<IconRefresh class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
		<PathBar :path="path || '/Documents/Subfolder/'" />
	</div>
	<div v-else-if="mode === 'search'" class="flex items-stretch">
		<div class="flex flex-row items-center gap-3 border-gray-300 border pl-2 rounded-lg w-full min-w-64">
			<IconSearch class="w-5 h-5 stroke-gray-500 stroke-2 z-20" />
			<input 
				type="text" 
				:placeholder="placeholder || 'Search...'" 
				class="text-text-secondary text-sm font-normal w-full bg-transparent outline-none"
			/>
		</div>
	</div>
</template>

