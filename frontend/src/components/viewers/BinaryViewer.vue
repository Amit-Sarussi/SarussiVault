<script setup lang="ts">
const props = defineProps<{
  filePath: string;
}>();
</script>

<template>
  <div class="h-full w-full bg-white flex items-center justify-center">
    <div class="text-center text-neutral-500">
      <p class="text-lg mb-2">Binary File</p>
      <p class="text-sm">This file type cannot be previewed in the browser.</p>
      <p class="text-sm mt-2">{{ filePath }}</p>
    </div>
  </div>
</template>
