<script setup lang="ts">
import { ref, onMounted } from 'vue';

const props = defineProps<{
	title: string;
	placeholder?: string;
	defaultValue?: string;
	buttonText?: string;
}>();

const emit = defineEmits<{
	confirm: [name: string];
	cancel: [];
}>();

const inputRef = ref<HTMLInputElement | null>(null);
const name = ref(props.defaultValue || '');

onMounted(() => {
	inputRef.value?.focus();
	inputRef.value?.select();
});

const handleSubmit = () => {
	const trimmed = name.value.trim();
	if (trimmed) {
		emit('confirm', trimmed);
	}
};

const handleCancel = () => {
	emit('cancel');
};

const handleKeyDown = (event: KeyboardEvent) => {
	if (event.key === 'Enter') {
		handleSubmit();
	} else if (event.key === 'Escape') {
		handleCancel();
	}
};
</script>

<template>
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 md:p-0" @click.self="handleCancel">
		<div class="bg-white rounded-lg shadow-lg p-4 md:p-6 min-w-0 md:min-w-80 max-w-md w-full">
			<h3 class="text-base md:text-lg font-semibold mb-3 md:mb-4 text-neutral-800">{{ title }}</h3>
			<input
				ref="inputRef"
				v-model="name"
				type="text"
				:placeholder="placeholder || 'Enter name'"
				class="w-full px-3 py-2 text-sm md:text-base border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				@keydown="handleKeyDown"
			/>
			<div class="flex justify-end gap-2 mt-3 md:mt-4">
				<button
					@click="handleCancel"
					class="px-3 md:px-4 py-2 text-xs md:text-sm text-neutral-700 hover:bg-neutral-100 rounded-md transition-colors cursor-pointer"
				>
					Cancel
				</button>
				<button
					@click="handleSubmit"
					class="px-3 md:px-4 py-2 text-xs md:text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-md transition-colors cursor-pointer"
				>
					{{ buttonText || 'Create' }}
				</button>
			</div>
		</div>
	</div>
</template>
