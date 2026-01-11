<script setup lang="ts">
import { computed, onMounted } from "vue";
import IconFolder from "@/assets/icons/folder.svg";
import IconFolderDarkGray from "@/assets/icons/folder-dark-gray.svg";
import { useAppContext, type StorageType } from "@/context/appContext";
import api from "@/services/api";

const { storageType, setStorageType, currentUsername, setCurrentUsername } = useAppContext();
const emit = defineEmits<{
	close: [];
}>();

// Fetch username on mount
onMounted(async () => {
	if (!currentUsername.value) {
		const username = await api.getCurrentUsername();
		setCurrentUsername(username);
	}
});

const isShared = computed(() => storageType.value === 'shared');
const isPrivate = computed(() => storageType.value === 'private');

const switchToShared = () => {
	setStorageType('shared');
	emit('close');
};

const switchToPrivate = () => {
	setStorageType('private');
	emit('close');
};

const storageLabel = computed(() => {
	if (currentUsername.value) {
		return `${currentUsername.value}'s Storage`;
	}
	return "My Storage";
});
</script>

<template>
	<div
		class="bg-neutral-100 w-64 md:w-54 h-full border-r-neutral-200 border-r p-2 md:p-2 flex flex-col gap-2 shadow-lg md:shadow-none">
		<button
			@click="switchToShared"
			:class="[
				'flex w-full justify-start items-center gap-3 py-2 px-4 rounded-lg cursor-pointer transition-colors',
				isShared ? 'bg-primary' : 'hover:bg-neutral-300'
			]">
			<component :is="isShared ? IconFolder : IconFolderDarkGray" class="w-5 h-5" :class="isShared ? 'text-white' : ''" />
			<span :class="['text-sm', isShared ? 'text-white' : 'text-neutral-700']">Shared Storage</span>
		</button>
		<button
			@click="switchToPrivate"
			:class="[
				'flex w-full justify-start items-center gap-3 py-2 px-4 rounded-lg cursor-pointer transition-colors',
				isPrivate ? 'bg-primary' : 'hover:bg-neutral-300'
			]">
			<component :is="isPrivate ? IconFolder : IconFolderDarkGray" class="w-5 h-5" :class="isPrivate ? 'text-white' : ''" />
			<span :class="['text-sm', isPrivate ? 'text-white' : 'text-neutral-700']">{{ storageLabel }}</span>
		</button>
	</div>
</template>
