import type { App } from 'vue';
import { inject, provide, readonly, ref } from 'vue';

const appContextKey = Symbol('app-context');

export type StorageType = 'shared' | 'private';

export interface AppContext {
	currentPath: Readonly<{ value: string }>;
	setCurrentPath: (path: string) => void;
	refreshSeq: Readonly<{ value: number }>;
	triggerRefresh: () => void;
	hierarchyRefreshSeq: Readonly<{ value: number }>;
	triggerHierarchyRefresh: () => void;
	viewedFile: Readonly<{ value: string | null }>;
	setViewedFile: (path: string | null) => void;
	storageType: Readonly<{ value: StorageType }>;
	setStorageType: (type: StorageType) => void;
	currentUsername: Readonly<{ value: string | null }>;
	setCurrentUsername: (username: string | null) => void;
	selectedFiles: Readonly<{ value: Set<string> }>;
	setSelectedFiles: (files: Set<string>) => void;
	selectedEntries: Readonly<{ value: Map<string, { name: string; is_dir: boolean }> }>;
	setSelectedEntries: (entries: Map<string, { name: string; is_dir: boolean }>) => void;
}

export function createAppContext(): AppContext {
	const currentPath = ref<string>('');
	const refreshSeq = ref<number>(0);
	const hierarchyRefreshSeq = ref<number>(0);
	const viewedFile = ref<string | null>(null);
	const storageType = ref<StorageType>('shared'); // Default to shared
	const currentUsername = ref<string | null>(null);
	const selectedFiles = ref<Set<string>>(new Set());
	const selectedEntries = ref<Map<string, { name: string; is_dir: boolean }>>(new Map());
	
	// Store paths per storage type to preserve location when switching
	const storagePaths = ref<Map<StorageType, string>>(new Map());
	const storageViewedFiles = ref<Map<StorageType, string | null>>(new Map());

	// Normalize path separators to forward slashes
	const normalizePath = (path: string): string => {
		return path.replace(/\\/g, '/');
	};

	const setCurrentPath = (path: string) => {
		currentPath.value = normalizePath(path);
		// Update stored path for current storage type
		storagePaths.value.set(storageType.value, currentPath.value);
		// Only clear viewed file if we're navigating to a different directory
		// (not when setting parent directory for a viewed file)
		// The MainScreen component will handle clearing viewedFile when appropriate
	};

	const triggerRefresh = () => {
		refreshSeq.value += 1;
	};

	const triggerHierarchyRefresh = () => {
		hierarchyRefreshSeq.value += 1;
	};

	const setViewedFile = (path: string | null) => {
		viewedFile.value = path ? normalizePath(path) : null;
		// Update stored viewed file for current storage type
		storageViewedFiles.value.set(storageType.value, viewedFile.value);
	};

	const setStorageType = (type: StorageType) => {
		// Save current path and viewed file for the current storage type
		const previousStorageType = storageType.value;
		storagePaths.value.set(previousStorageType, currentPath.value);
		storageViewedFiles.value.set(previousStorageType, viewedFile.value);
		
		// Switch to new storage type
		storageType.value = type;
		
		// Restore path and viewed file for the new storage type, or use empty if not set
		currentPath.value = storagePaths.value.get(type) || '';
		viewedFile.value = storageViewedFiles.value.get(type) || null;
		
		triggerRefresh();
		triggerHierarchyRefresh();
	};

	const setCurrentUsername = (username: string | null) => {
		currentUsername.value = username;
	};

	const setSelectedFiles = (files: Set<string>) => {
		selectedFiles.value = files;
	};

	const setSelectedEntries = (entries: Map<string, { name: string; is_dir: boolean }>) => {
		selectedEntries.value = entries;
	};

	return {
		currentPath: readonly(currentPath),
		setCurrentPath,
		refreshSeq: readonly(refreshSeq),
		triggerRefresh,
		hierarchyRefreshSeq: readonly(hierarchyRefreshSeq),
		triggerHierarchyRefresh,
		viewedFile: readonly(viewedFile),
		setViewedFile,
		storageType: readonly(storageType),
		setStorageType,
		currentUsername: readonly(currentUsername),
		setCurrentUsername,
		selectedFiles: readonly(selectedFiles),
		setSelectedFiles,
		selectedEntries: readonly(selectedEntries),
		setSelectedEntries,
	};
}

export function installAppContext(app: App): AppContext {
	const context = createAppContext();
	app.provide(appContextKey, context);
	return context;
}

export function useAppContext(): AppContext {
	const context = inject<AppContext>(appContextKey);
	if (!context) {
		throw new Error('App context is not available. Did you forget to call installAppContext?');
	}
	return context;
}
