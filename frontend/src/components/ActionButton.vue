<script setup lang="ts">
defineProps<{
  title: string;
}>();
</script>

<template>
  <button class="flex items-center gap-1 py-2 px-2 hover:bg-neutral-200/70 rounded-lg transition-all duration-150 cursor-pointer">
    <slot name="icon" />
    <span class="text-text-secondary">{{ title }}</span>
  </button>
</template>
