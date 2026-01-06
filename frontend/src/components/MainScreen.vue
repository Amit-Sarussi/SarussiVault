<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import Header from "./Header.vue";
import Sidebar from "./Sidebar.vue";
import FileManager from "./FileManager.vue";

const router = useRouter();
const files = ref([]);
const currentPath = ref("");

onMounted(async () => {
	// Check if user is logged in
	if (!localStorage.getItem("fb_token")) {
		router.push("/login");
		return;
	}
	loadFiles();
});

const loadFiles = async (path = "") => {
	try {
		const data = await api.getFiles(path);
		files.value = data.items; // FileBrowser returns { items: [], ... }
		currentPath.value = path;
	} catch (err) {
		console.error(err);
		// If unauthorized, redirect to login
		if (err.response?.status === 401) {
			router.push("/login");
		}
	}
};
</script>

<template>
	<div class="w-full h-screen flex flex-col">
		<Header />
    <div class="w-full flex flex-row flex-1 overflow-hidden">
      <Sidebar />
      <FileManager />
    </div>
	</div>
</template>
