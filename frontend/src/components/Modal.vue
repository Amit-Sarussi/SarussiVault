<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';

defineProps<{
  show: boolean;
  title?: string;
  closable?: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const handleBackdropClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget) {
    emit('close');
  }
};

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    emit('close');
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleEscape);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape);
});
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click="closable !== false ? handleBackdropClick : undefined"
      >
        <div class="bg-white rounded-lg shadow-lg p-6 min-w-80 max-w-md w-full mx-4" @click.stop>
          <div v-if="title" class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-neutral-800">{{ title }}</h3>
            <button
              v-if="closable !== false"
              @click="emit('close')"
              class="text-neutral-400 hover:text-neutral-600 transition-colors cursor-pointer"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
