<script setup lang="ts">
import IconFolder from "@/assets/icons/folder.svg";
import IconArrow from "@/assets/icons/arrow.svg";
import PathButton from "./PathButton.vue";

defineProps<{
	path: string;
}>();
</script>

<template>
	<div
		class="flex flex-row items-center gap-3 border-gray-300 border pl-2 rounded-lg w-full">
		<IconFolder class="w-5 h-5 stroke-gray-500 stroke-2 z-20" />
		<span class="text-text-secondary text-sm font-normal w-full truncate">{{ path }}</span>
    <PathButton nav>
      <IconArrow class="w-6 h-6 text-text-secondary stroke-2 z-20" />
    </PathButton>
	</div>
</template>
