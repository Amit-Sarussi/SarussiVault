<script setup lang="ts">
import Logo from "@/assets/logo.svg";
import IconSettings from "@/assets/icons/settings.svg";
</script>

<template>
	<div
		class="w-full h-16 border-b-neutral-200 border-b flex flex-row items-center p-2 px-6 justify-between">
		<div class="flex gap-3 items-center">
			<Logo class="w-8" :draggable="false" />
			<h1 class="font-medium tracking-tight text-3xl">
				sarussi's <span class="text-neutral-400">vault</span>
			</h1>
		</div>
		<button
			class="p-2 rounded-lg hover:bg-gray-200/70 transition-all duration-100 cursor-pointer">
			<IconSettings class="w-6 h-6" />
		</button>
	</div>
</template>
