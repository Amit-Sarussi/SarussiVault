<script setup lang="ts">
import ActionButton from "./ActionButton.vue";
import IconFileAdd from "@/assets/icons/file-add.svg";
import IconFolderAdd from "@/assets/icons/folder-add.svg";
import IconUpload from "@/assets/icons/upload.svg";
</script>

<template>
	<div class="w-full flex items-center p-2 border-b-neutral-200 border-b">
		<ActionButton title="Add file">
			<template #icon>
				<IconFileAdd class="w-5 h-5 text-text-secondary" />
			</template>
		</ActionButton>
		<ActionButton title="Add folder">
			<template #icon>
				<IconFolderAdd class="w-5 h-5 text-text-secondary" />
			</template>
		</ActionButton>
		<ActionButton title="Upload">
			<template #icon>
				<IconUpload class="w-5 h-5 text-text-secondary" />
			</template>
		</ActionButton>
	</div>
</template>

<style scoped>
.icon-secondary {
	filter: brightness(0) saturate(100%) invert(33%) sepia(4%) saturate(879%)
		hue-rotate(208deg) brightness(94%) contrast(88%);
}
</style>
