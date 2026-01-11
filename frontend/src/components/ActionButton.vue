<script setup lang="ts">
defineProps<{
  title: string;
  disabled?: boolean;
}>();

defineEmits<{
  click: [];
}>();
</script>

<template>
  <button 
    class="flex items-center gap-1 py-2 px-2 hover:bg-neutral-200/70 rounded-lg transition-all duration-150 cursor-pointer shrink-0"
    :class="{ 'cursor-not-allowed opacity-50': disabled }"
    :disabled="disabled"
    @click="$emit('click')"
    :title="title"
  >
    <slot name="icon" />
    <span class="text-text-secondary hidden sm:inline">{{ title }}</span>
  </button>
</template>
