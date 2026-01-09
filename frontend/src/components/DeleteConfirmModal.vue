<script setup lang="ts">
import Modal from './Modal.vue';

const props = defineProps<{
	show: boolean;
	count: number;
}>();

const emit = defineEmits<{
	confirm: [];
	cancel: [];
}>();

const handleConfirm = () => {
	emit('confirm');
};

const handleCancel = () => {
	emit('cancel');
};
</script>

<template>
	<Modal :show="show" title="Delete Items" @close="handleCancel">
		<div class="flex flex-col gap-4">
			<p class="text-neutral-700">
				Are you sure you want to delete {{ count }} item{{ count > 1 ? 's' : '' }}? This action cannot be undone.
			</p>
			<div class="flex justify-end gap-2">
				<button
					@click="handleCancel"
					class="px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100 rounded-md transition-colors cursor-pointer"
				>
					Cancel
				</button>
				<button
					@click="handleConfirm"
					class="px-4 py-2 text-sm bg-red-600 text-white hover:bg-red-700 rounded-md transition-colors cursor-pointer"
				>
					Delete
				</button>
			</div>
		</div>
	</Modal>
</template>
