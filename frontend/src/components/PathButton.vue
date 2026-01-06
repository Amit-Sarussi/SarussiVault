<script setup lang="ts">
defineProps<{
	title?: string;
	nav?: boolean;
}>();
</script>

<template>
	<button
		:class="`relative flex gap-1 border border-gray-300 py-1 cursor-pointer ${nav ? 'rounded-md rounded-l-none border-0 border-l' : 'rounded-md'} ${
			title ? 'px-2' : 'px-1 aspect-square shrink-0'
		} items-center justify-center bg-linear-to-t from-gray-100/70 to-white overflow-hidden transition-all duration-100 before:absolute before:inset-0 before:bg-linear-to-t before:from-gray-200 before:to-gray-100 before:opacity-0 hover:before:opacity-100 before:transition-opacity before:duration-200`">
		<slot />
		<span v-if="title" class="text-text-secondary z-20">{{ title }}</span>
	</button>
</template>
