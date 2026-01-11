<script setup lang="ts">
import Logo from "@/assets/logo.svg";
import IconSettings from "@/assets/icons/settings.svg";
import IconMenu from "@/assets/icons/menu.svg";

const emit = defineEmits<{
	toggleSidebar: [];
}>();
</script>

<template>
	<div
		class="w-full h-16 md:h-16 border-b-neutral-200 border-b flex flex-row items-center p-2 px-3 md:px-6 justify-between shrink-0">
		<div class="flex gap-2 md:gap-3 items-center">
			<!-- Mobile menu button -->
			<button
				@click="emit('toggleSidebar')"
				class="md:hidden p-2 rounded-lg hover:bg-gray-200/70 transition-all duration-100 cursor-pointer"
				aria-label="Toggle menu"
			>
				<IconMenu class="w-5 h-5 md:w-6 md:h-6" />
			</button>
			<Logo class="w-6 h-6 md:w-8" :draggable="false" />
			<h1 class="font-medium tracking-tight text-lg md:text-3xl">
				sarussi's <span class="text-neutral-400">vault</span>
			</h1>
		</div>
		<button
			class="p-2 rounded-lg hover:bg-gray-200/70 transition-all duration-100 cursor-pointer">
			<IconSettings class="w-5 h-5 md:w-6 md:h-6" />
		</button>
	</div>
</template>
