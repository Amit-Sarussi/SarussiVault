<script setup lang="ts">
import IconFolder from "@/assets/icons/folder.svg"
</script>

<template>
	<div
		class="bg-neutral-100 w-54 h-full border-r-neutral-200 border-r p-2 flex flex-col gap-2">
		<button class="flex w-full justify-start items-center gap-3 py-2 px-4 rounded-lg bg-primary cursor-pointer">
			<IconFolder class="w-5 h-5" />
      <span class="text-white text-sm">File manager</span>
		</button>
	</div>
</template>
