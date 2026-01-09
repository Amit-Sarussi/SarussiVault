<script setup lang="ts">
import { watch, ref, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import Header from "./Header.vue";
import Sidebar from "./Sidebar.vue";
import FileManager from "./FileManager.vue";
import { useAppContext } from "@/context/appContext";
import { getViewType } from "@/utils/fileTypes";
import api from "@/services/api";

const route = useRoute();
const router = useRouter();
const { currentPath, setCurrentPath, viewedFile, setViewedFile, setCurrentUsername, storageType, setStorageType } = useAppContext();
const isInitialLoad = ref(true);
const hasSyncedFromRoute = ref(false);

// Fetch username on mount
onMounted(async () => {
	const username = await api.getCurrentUsername();
	if (username) {
		setCurrentUsername(username);
	}
});

const normalizeRoutePath = (value: unknown): string => {
	if (Array.isArray(value)) {
		return value.map((part) => decodeURIComponent(String(part))).join("/");
	}
	if (typeof value === "string") {
		return decodeURIComponent(value);
	}
	return "";
};

const encodePathForRoute = (path: string, storage: string): string => {
	// Normalize path separators to forward slashes (handle Windows backslashes)
	const normalizedPath = path ? path.replace(/\\/g, '/') : '';
	// Split by forward slashes, encode each segment, then join with forward slashes
	const encodedPath = normalizedPath
		.split("/")
		.filter(Boolean) // Remove empty segments
		.map((segment) => encodeURIComponent(segment))
		.join("/");
	
	// Return with storage type prefix
	return `/${storage}${encodedPath ? '/' + encodedPath : ''}`;
};

// Check if a path is likely a file (has extension and is not empty)
const isLikelyFile = (path: string): boolean => {
	if (!path) return false;
	// Check if path has a file extension (contains a dot followed by at least one character)
	const hasExtension = /\.\w+$/.test(path);
	return hasExtension;
};

// Sync route -> context
// Extract storage type and path from URL
watch(
	() => route.path,
	(routePath) => {
		// Parse URL: /shared/path/to/file or /private/path/to/file
		const routePathStr = Array.isArray(routePath) ? routePath.join('/') : String(routePath);
		const segments = routePathStr.split('/').filter(Boolean);
		
		// Extract storage type (first segment should be 'shared' or 'private')
		let routeStorageType: 'shared' | 'private' = 'shared';
		let pathFromRoute = '';
		
		if (segments.length > 0) {
			const firstSegment = segments[0];
			if (firstSegment === 'shared' || firstSegment === 'private') {
				routeStorageType = firstSegment;
				// Get path from params.pathMatch if available, otherwise from segments
				const pathMatch = route.params.pathMatch;
				if (pathMatch) {
					// pathMatch can be a string or array
					if (Array.isArray(pathMatch)) {
						pathFromRoute = pathMatch
							.filter(Boolean)
							.map(segment => decodeURIComponent(String(segment)))
							.join('/');
					} else {
						pathFromRoute = decodeURIComponent(String(pathMatch));
					}
				} else if (segments.length > 1) {
					// Fallback: parse from segments
					pathFromRoute = segments.slice(1)
						.map(segment => decodeURIComponent(segment))
						.join('/');
				}
			} else {
				// Legacy URL without storage type - default to shared and treat first segment as path
				routeStorageType = 'shared';
				pathFromRoute = segments.map(segment => decodeURIComponent(segment)).join('/');
			}
		}
		
		// Normalize any backslashes to forward slashes
		pathFromRoute = pathFromRoute.replace(/\\/g, '/');
		
		// Update storage type if it changed
		// This will trigger context -> route watcher, but it should be safe because
		// the watcher checks if the route path matches before updating
		if (storageType.value !== routeStorageType) {
			setStorageType(routeStorageType);
		}
		
		// Check if this is a file path
		if (isLikelyFile(pathFromRoute)) {
			// It's a file - set as viewed file and set current path to parent directory
			setViewedFile(pathFromRoute);
			const pathParts = pathFromRoute.split("/").filter(Boolean);
			if (pathParts.length > 1) {
				pathParts.pop();
				setCurrentPath(pathParts.join("/"));
			} else {
				setCurrentPath("");
			}
		} else {
			// It's a directory
			setViewedFile(null);
			if (pathFromRoute !== currentPath.value) {
				setCurrentPath(pathFromRoute);
			}
		}
		
		// Mark that we've synced from route and allow context -> route sync
		hasSyncedFromRoute.value = true;
		
		// Mark initial load as complete after first sync
		// Use a small timeout to ensure route -> context sync completes before context -> route can run
		if (isInitialLoad.value) {
			setTimeout(() => {
				isInitialLoad.value = false;
			}, 0);
		}
	},
	{ immediate: true }
);

// Sync context -> route (prioritize viewedFile over currentPath)
// Only sync after we've synced from route to prevent overwriting the URL on page refresh
watch(
	() => [viewedFile.value, currentPath.value, storageType.value],
	([filePath, dirPath, storage]) => {
		// Skip until we've synced from route - let route -> context sync happen first
		if (!hasSyncedFromRoute.value || isInitialLoad.value) {
			return;
		}
		
		const targetPath = filePath || dirPath || '';
		const encodedPath = encodePathForRoute(targetPath, storage);
		const currentRoutePath = router.currentRoute.value.path;
		
		// Normalize both paths for comparison (remove trailing slashes, handle empty paths)
		const normalizedEncoded = encodedPath === '/' ? '/' : encodedPath.replace(/\/$/, '');
		const normalizedCurrent = currentRoutePath === '/' ? '/' : currentRoutePath.replace(/\/$/, '');
		
		// Compare paths (not fullPath, to avoid query/hash issues)
		// Only update route if it's different
		if (normalizedCurrent !== normalizedEncoded) {
			router.push(encodedPath);
		}
	}
);
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
