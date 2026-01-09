import { useAppContext } from '@/context/appContext';

/**
 * Normalize path separators to forward slashes
 */
const normalizePath = (path: string): string => {
	return path.replace(/\\/g, '/');
};

/**
 * Centralized navigation composable
 * Handles all navigation (files and folders) consistently
 */
export function useNavigation() {
	const { currentPath, setCurrentPath, viewedFile, setViewedFile } = useAppContext();

	/**
	 * Navigate to a folder
	 * @param path - The folder path to navigate to
	 */
	const navigateToFolder = (path: string) => {
		setViewedFile(null);
		setCurrentPath(normalizePath(path));
	};

	/**
	 * Navigate to a file (view it)
	 * @param path - The file path to view
	 */
	const navigateToFile = (path: string) => {
		const normalizedPath = normalizePath(path);
		setViewedFile(normalizedPath);
		// Set current path to the file's parent directory
		const pathParts = normalizedPath.split('/').filter(Boolean);
		if (pathParts.length > 1) {
			pathParts.pop();
			setCurrentPath(pathParts.join('/'));
		} else {
			setCurrentPath('');
		}
	};

	/**
	 * Navigate to a path (automatically detects if it's a file or folder)
	 * @param path - The path to navigate to
	 * @param isFile - Optional: explicitly specify if it's a file
	 */
	const navigateTo = (path: string, isFile?: boolean) => {
		const normalizedPath = normalizePath(path);
		if (isFile === undefined) {
			// Auto-detect: if path has an extension, treat as file
			isFile = /\.\w+$/.test(normalizedPath);
		}
		
		if (isFile) {
			navigateToFile(normalizedPath);
		} else {
			navigateToFolder(normalizedPath);
		}
	};

	/**
	 * Navigate to parent directory
	 */
	const navigateUp = () => {
		if (viewedFile.value) {
			// If viewing a file, go to its parent directory
			const pathParts = viewedFile.value.split('/').filter(Boolean);
			if (pathParts.length > 1) {
				pathParts.pop();
				navigateToFolder(pathParts.join('/'));
			} else {
				navigateToFolder('');
			}
		} else {
			// Normal directory navigation
			const pathParts = currentPath.value.split('/').filter(Boolean);
			if (pathParts.length === 0) {
				navigateToFolder('');
				return;
			}
			pathParts.pop();
			navigateToFolder(pathParts.join('/'));
		}
	};

	/**
	 * Navigate to home (root)
	 */
	const navigateHome = () => {
		navigateToFolder('');
	};

	/**
	 * Close file viewer (go back to folder view)
	 */
	const closeFileViewer = () => {
		setViewedFile(null);
	};

	return {
		navigateToFolder,
		navigateToFile,
		navigateTo,
		navigateUp,
		navigateHome,
		closeFileViewer,
	};
}
