<script setup lang="ts">
import { ref, watch } from 'vue';
import IconFolder from "@/assets/icons/folder.svg";
import IconArrow from "@/assets/icons/arrow.svg";
import PathButton from "./PathButton.vue";

const props = defineProps<{
	path: string;
}>();

const emit = defineEmits<{
	'path-change': [path: string];
}>();

const inputValue = ref(props.path);
const isEditing = ref(false);

// Update input value when prop changes (but not while editing)
watch(() => props.path, (newPath) => {
	if (!isEditing.value) {
		inputValue.value = newPath;
	}
});

const handleInput = (event: Event) => {
	const target = event.target as HTMLInputElement;
	inputValue.value = target.value;
};

const handleKeyDown = async (event: KeyboardEvent) => {
	if (event.key === 'Enter') {
		event.preventDefault();
		await handleSubmit();
	} else if (event.key === 'Escape') {
		// Cancel editing and revert to original path
		inputValue.value = props.path;
		isEditing.value = false;
		(event.target as HTMLInputElement).blur();
	}
};

const handleSubmit = async () => {
	const trimmedPath = inputValue.value.trim();
	// Emit the path change - validation will happen in parent
	emit('path-change', trimmedPath);
	isEditing.value = false;
	(event.target as HTMLInputElement)?.blur();
};

const handleFocus = () => {
	isEditing.value = true;
};

const handleBlur = () => {
	// Small delay to allow click events to fire first
	setTimeout(() => {
		isEditing.value = false;
		// Revert to original if not submitted
		if (inputValue.value !== props.path) {
			inputValue.value = props.path;
		}
	}, 200);
};
</script>

<template>
	<div
		class="flex flex-row items-center gap-3 border-gray-300 border pl-2 rounded-lg w-full">
		<IconFolder class="w-5 h-5 stroke-gray-500 stroke-2 z-20 shrink-0" />
		<input
			v-model="inputValue"
			type="text"
			class="text-text-secondary text-sm font-normal w-full bg-transparent outline-none border-none"
			@input="handleInput"
			@keydown="handleKeyDown"
			@focus="handleFocus"
			@blur="handleBlur"
		/>
		<PathButton nav @click="handleSubmit">
			<IconArrow class="w-6 h-6 text-text-secondary stroke-2 z-20" />
		</PathButton>
	</div>
</template>
