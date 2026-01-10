<script setup lang="ts">
import PathButton from "./PathButton.vue";
import IconHome from "@/assets/icons/home.svg"
import IconArrow from "@/assets/icons/arrow.svg"
import IconRefresh from "@/assets/icons/refresh.svg"
import IconSearch from "@/assets/icons/search.svg"
import PathBar from "./PathBar.vue";

const props = withDefaults(defineProps<{
	mode?: 'path' | 'search';
	path?: string;
	placeholder?: string;
	searchQuery?: string;
	canGoHome?: boolean;
	canGoUp?: boolean;
	canGoBack?: boolean;
	canGoForward?: boolean;
}>(), {
	canGoHome: true,
	canGoUp: true,
	canGoBack: true,
	canGoForward: false,
});

const emit = defineEmits<{
	refresh: [];
	goUp: [];
	goHome: [];
	goBack: [];
	goForward: [];
	pathChange: [path: string];
	search: [query: string];
}>();

const handleRefresh = () => emit('refresh');
const handleGoUp = () => emit('goUp');
const handleGoHome = () => emit('goHome');
const handleGoBack = () => emit('goBack');
const handleGoForward = () => emit('goForward');

const handleSearchInput = (event: Event) => {
	const target = event.target as HTMLInputElement;
	emit('search', target.value);
};
</script>

<template>
	<div v-if="mode === 'path'" class="flex gap-2 items-stretch flex-1">
		<PathButton title="Main" :disabled="!canGoHome" @click="handleGoHome">
			<IconHome class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
		<PathButton :disabled="!canGoBack" @click="handleGoBack">
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 rotate-180 z-20" />
		</PathButton>
		<PathButton :disabled="!canGoForward" @click="handleGoForward">
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
		<PathButton :disabled="!canGoUp" @click="handleGoUp">
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 -rotate-90 z-20" />
		</PathButton>
		<PathButton @click="handleRefresh">
			<IconRefresh class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
		<PathBar :path="path || '/'" @path-change="(newPath) => emit('pathChange', newPath)" />
	</div>
	<div v-else-if="mode === 'search'" class="flex items-stretch">
		<div class="flex flex-row items-center gap-3 border-gray-300 border pl-2 rounded-lg w-full min-w-64">
			<IconSearch class="w-5 h-5 stroke-gray-500 stroke-2 z-20" />
			<input 
				type="text" 
				:value="searchQuery || ''"
				:placeholder="placeholder || 'Search...'" 
				class="text-text-secondary text-sm font-normal w-full bg-transparent outline-none"
				@input="handleSearchInput"
			/>
		</div>
	</div>
</template>

