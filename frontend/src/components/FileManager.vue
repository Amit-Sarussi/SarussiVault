<script setup lang="ts">
import ActionsTab from "./ActionsTab.vue";
import TextField from "./TextField.vue";
import PathButton from "./PathButton.vue";
import IconMenu from "@/assets/icons/menu.svg";
import FileHierarchy from "./FileHierarchy.vue";
import FileList from "./FileList.vue";

const handleMenuClick = () => {
	// Handle menu click
};
</script>

<template>
	<div class="w-full h-full">
		<ActionsTab />
		<div class="flex items-stretch gap-2 p-3 border-b border-b-neutral-200">
			<TextField mode="path" path="/Documents/Subfolder/" />
			<TextField mode="search" placeholder="Search..." />
			<PathButton @click="handleMenuClick">
				<IconMenu class="w-6 h-6 text-text-secondary stroke-2 z-20" />
			</PathButton>
		</div>
		<div class="flex flex-row w-full h-full">
			<FileHierarchy />
			<FileList />
		</div>
	</div>
</template>
