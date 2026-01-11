<script setup lang="ts">
import { ref, computed } from 'vue';
import ActionButton from "./ActionButton.vue";
import NamePrompt from "./NamePrompt.vue";
import UploadModal from "./UploadModal.vue";
import ProgressModal from "./ProgressModal.vue";
import DeleteConfirmModal from "./DeleteConfirmModal.vue";
import FolderPickerModal from "./FolderPickerModal.vue";
import ShareModal from "./ShareModal.vue";
import IconFileAdd from "@/assets/icons/file-add.svg";
import IconFolderAdd from "@/assets/icons/folder-add.svg";
import IconUpload from "@/assets/icons/upload.svg";
import IconCopy from "@/assets/icons/copy.svg";
import IconMove from "@/assets/icons/move.svg";
import IconDownload from "@/assets/icons/download.svg";
import IconRename from "@/assets/icons/rename.svg";
import IconDelete from "@/assets/icons/delete.svg";
import IconPaste from "@/assets/icons/paste.svg";
import { useAppContext, type StorageType } from "@/context/appContext";
import api from "@/services/api";
import { useNavigation } from "@/composables/useNavigation";

const { currentPath, triggerRefresh, triggerHierarchyRefresh, storageType, selectedFiles, selectedEntries, currentUsername, setSelectedFiles, viewedFile } = useAppContext();
const { navigateToFolder, navigateToFile, closeFileViewer } = useNavigation();

// Clipboard for copy/paste
const copiedFiles = ref<Array<{ path: string; name: string; storageType: StorageType }>>([]);

// Permission checking
const SHARED_WRITE_USERS = new Set(["Aharon", "Amit", "Yuval"]);

const hasWritePermission = computed(() => {
	const path = currentPath.value;
	const isShared = storageType.value === 'shared' || path === '' || path.startsWith('shared/');
	if (!isShared) return true; // Private folders always have write permission
	return currentUsername.value ? SHARED_WRITE_USERS.has(currentUsername.value) : false;
});

const selectedFilesArray = computed(() => {
	// If viewing a file, include it in the selection array
	if (viewedFile.value) {
		return [viewedFile.value];
	}
	return Array.from(selectedFiles.value);
});

const hasSelection = computed(() => selectedFiles.value.size > 0 || !!viewedFile.value);
const hasMultipleSelection = computed(() => selectedFiles.value.size > 1);
const isViewingFile = computed(() => !!viewedFile.value);
const hasCopiedFiles = computed(() => copiedFiles.value.length > 0);

// Share modal state
const showShareModal = ref(false);
const sharePath = ref('');
const shareIsFile = computed(() => {
	const pathToShare = viewedFile.value || (selectedFilesArray.value.length === 1 ? selectedFilesArray.value[0] : null);
	if (!pathToShare) return false;
	
	// Check if it's a file (has extension or is the viewed file)
	if (viewedFile.value) {
		const entry = selectedEntries.value.get(pathToShare);
		return entry ? !entry.is_dir : /\.\w+$/.test(pathToShare);
	}
	
	const entry = selectedEntries.value.get(pathToShare);
	return entry ? !entry.is_dir : false;
});

const handleShare = () => {
	if (!hasSelection.value && !isViewingFile.value) return;
	
	// Determine path to share
	if (isViewingFile.value && !hasSelection.value) {
		sharePath.value = viewedFile.value!;
	} else if (selectedFiles.value.size === 1) {
		sharePath.value = selectedFilesArray.value[0];
	} else {
		// Multiple files selected, use current path (must be a folder)
		sharePath.value = currentPath.value;
	}
	
	showShareModal.value = true;
};

const showFilePrompt = ref(false);
const showFolderPrompt = ref(false);
const showUploadModal = ref(false);
const showProgressModal = ref(false);
const uploadProgress = ref(0);
const uploadStatus = ref('');
const estimatedTimeRemaining = ref<number | undefined>(undefined);
const fileInputRef = ref<HTMLInputElement | null>(null);
const folderInputRef = ref<HTMLInputElement | null>(null);
const uploadStartTime = ref<number | null>(null);

const handleAddFile = () => {
	showFilePrompt.value = true;
};

const handleAddFolder = () => {
	showFolderPrompt.value = true;
};

const handleUpload = () => {
	showUploadModal.value = true;
};

const handleSelectFiles = () => {
	fileInputRef.value?.click();
};

const handleSelectFolders = () => {
	folderInputRef.value?.click();
};

const handleFilePromptConfirm = async (name: string) => {
	try {
		await api.createFile(currentPath.value, name, storageType.value);
		triggerRefresh();
		triggerHierarchyRefresh();
		showFilePrompt.value = false;
	} catch (error) {
		console.error('Failed to create file', error);
		alert('Failed to create file. It may already exist.');
	}
};

const handleFilePromptCancel = () => {
	showFilePrompt.value = false;
};

const handleFolderPromptConfirm = async (name: string) => {
	try {
		await api.createDirectory(currentPath.value, name, storageType.value);
		triggerRefresh();
		triggerHierarchyRefresh();
		showFolderPrompt.value = false;
	} catch (error) {
		console.error('Failed to create folder', error);
		alert('Failed to create folder. It may already exist.');
	}
};

const handleFolderPromptCancel = () => {
	showFolderPrompt.value = false;
};

const calculateEstimatedTime = (progress: number, elapsed: number) => {
	if (progress <= 0 || elapsed <= 0) return undefined;
	// Calculate total time based on current progress
	const totalTime = (elapsed / progress) * 100;
	const remaining = totalTime - elapsed;
	return remaining > 0 ? remaining : 0; // Already in seconds
};

const handleFileInputChange = async (event: Event) => {
	const target = event.target as HTMLInputElement;
	const files = target.files;
	if (!files || files.length === 0) return;

	// Show progress modal
	showProgressModal.value = true;
	uploadProgress.value = 0;
	uploadStatus.value = `Uploading ${files.length} file${files.length > 1 ? 's' : ''}...`;
	uploadStartTime.value = Date.now();
	estimatedTimeRemaining.value = undefined;

	try {
		await api.uploadFiles(
			currentPath.value,
			Array.from(files),
			storageType.value,
			(progress, loaded, total) => {
				uploadProgress.value = progress;
				if (uploadStartTime.value) {
					const elapsed = (Date.now() - uploadStartTime.value) / 1000; // seconds
					estimatedTimeRemaining.value = calculateEstimatedTime(progress, elapsed);
				}
				if (total) {
					const loadedMB = (loaded / (1024 * 1024)).toFixed(1);
					const totalMB = (total / (1024 * 1024)).toFixed(1);
					uploadStatus.value = `Uploading ${files.length} file${files.length > 1 ? 's' : ''}... ${loadedMB}MB / ${totalMB}MB`;
				}
			}
		);
		
		// Complete
		uploadProgress.value = 100;
		uploadStatus.value = 'Upload complete!';
		
		// Wait a moment to show completion, then close
		setTimeout(() => {
			showProgressModal.value = false;
			triggerRefresh();
			triggerHierarchyRefresh();
		}, 500);
	} catch (error) {
		console.error('Failed to upload files', error);
		uploadStatus.value = 'Upload failed. Some files may already exist.';
		setTimeout(() => {
			showProgressModal.value = false;
		}, 2000);
	}

	// Reset input
	target.value = '';
	uploadStartTime.value = null;
};

const handleFolderInputChange = async (event: Event) => {
	const target = event.target as HTMLInputElement;
	const files = target.files;
	if (!files || files.length === 0) return;

	// Show progress modal
	showProgressModal.value = true;
	uploadProgress.value = 0;
	uploadStatus.value = `Uploading folder${files.length > 1 ? 's' : ''}...`;
	uploadStartTime.value = Date.now();
	estimatedTimeRemaining.value = undefined;

	try {
		await api.uploadFiles(
			currentPath.value,
			Array.from(files),
			storageType.value,
			(progress, loaded, total) => {
				uploadProgress.value = progress;
				if (uploadStartTime.value) {
					const elapsed = (Date.now() - uploadStartTime.value) / 1000; // seconds
					estimatedTimeRemaining.value = calculateEstimatedTime(progress, elapsed);
				}
				if (total) {
					const loadedMB = (loaded / (1024 * 1024)).toFixed(1);
					const totalMB = (total / (1024 * 1024)).toFixed(1);
					uploadStatus.value = `Uploading folder${files.length > 1 ? 's' : ''}... ${loadedMB}MB / ${totalMB}MB`;
				}
			}
		);
		
		// Complete
		uploadProgress.value = 100;
		uploadStatus.value = 'Upload complete!';
		
		// Wait a moment to show completion, then close
		setTimeout(() => {
			showProgressModal.value = false;
			triggerRefresh();
			triggerHierarchyRefresh();
		}, 500);
	} catch (error) {
		console.error('Failed to upload folders', error);
		uploadStatus.value = 'Upload failed. Some files may already exist.';
		setTimeout(() => {
			showProgressModal.value = false;
		}, 2000);
	}

	// Reset input
	target.value = '';
	uploadStartTime.value = null;
};

// New action handlers
const showRenamePrompt = ref(false);
const showMovePrompt = ref(false);
const showDeleteModal = ref(false);
const renameNewName = ref('');
const fileToRename = ref<string | null>(null);

const handleCopy = () => {
	if (!hasSelection.value && !isViewingFile.value) return;
	
	const files: Array<{ path: string; name: string; storageType: StorageType }> = [];
	selectedFilesArray.value.forEach((fullPath) => {
		const parts = fullPath.split('/');
		const name = parts[parts.length - 1];
		files.push({ path: fullPath, name, storageType: storageType.value });
	});
	copiedFiles.value = files;
};

const handlePaste = async () => {
	if (copiedFiles.value.length === 0) return;
	
	// Check write permission for destination
	if (!hasWritePermission.value) {
		alert('You do not have permission to write to this location.');
		return;
	}
	
	try {
		for (const file of copiedFiles.value) {
			const srcPath = file.path;
			const fileName = file.name;
			const srcStorageType = file.storageType;
			// Generate destination path in current folder
			const dstPath = currentPath.value ? `${currentPath.value}/${fileName}` : fileName;
			
			// Handle cross-storage copy: ensure paths have proper prefixes
			const fullSrcPath = srcStorageType === 'shared' ? (srcPath.startsWith('shared/') ? srcPath : `shared/${srcPath}`) : (srcPath.startsWith('private/') ? srcPath : `private/${srcPath}`);
			const fullDstPath = storageType.value === 'shared' ? (dstPath.startsWith('shared/') ? dstPath : `shared/${dstPath}`) : (dstPath.startsWith('private/') ? dstPath : `private/${dstPath}`);
			
			// Use the API with proper prefixed paths
			await api.copyPath(fullSrcPath, fullDstPath, storageType.value);
		}
		triggerRefresh();
		triggerHierarchyRefresh();
		copiedFiles.value = []; // Clear clipboard after paste
	} catch (error: any) {
		console.error('Failed to paste files', error);
		const message = error.response?.data?.detail || 'Failed to paste files. They may already exist.';
		alert(message);
	}
};

const handleDiscardCopy = () => {
	copiedFiles.value = [];
};

const filesToMove = ref<string[]>([]);

const handleMove = () => {
	if (!hasSelection.value && !isViewingFile.value) return;
	// Capture the file paths at the time of opening the modal
	filesToMove.value = [...selectedFilesArray.value];
	showMovePrompt.value = true;
};

const handleMoveConfirm = async (destinationPath: string, destinationStorageType: StorageType) => {
	if (filesToMove.value.length === 0) return;
	
	try {
		// Use the captured file paths
		for (const srcPath of filesToMove.value) {
			const parts = srcPath.split('/');
			const fileName = parts[parts.length - 1];
			const dstPath = destinationPath ? `${destinationPath}/${fileName}` : fileName;
			// Ensure paths have proper prefixes
			const fullSrcPath = storageType.value === 'shared' ? (srcPath.startsWith('shared/') ? srcPath : `shared/${srcPath}`) : (srcPath.startsWith('private/') ? srcPath : `private/${srcPath}`);
			const fullDstPath = destinationStorageType === 'shared' ? (dstPath.startsWith('shared/') ? dstPath : `shared/${dstPath}`) : (dstPath.startsWith('private/') ? dstPath : `private/${dstPath}`);
			await api.movePath(fullSrcPath, fullDstPath, destinationStorageType);
		}
		triggerRefresh();
		triggerHierarchyRefresh();
		showMovePrompt.value = false;
		setSelectedFiles(new Set()); // Clear selection
		filesToMove.value = []; // Clear captured paths
	} catch (error: any) {
		console.error('Failed to move files', error);
		const message = error.response?.data?.detail || 'Failed to move files.';
		alert(message);
		filesToMove.value = []; // Clear captured paths on error
	}
};

const handleMoveCancel = () => {
	showMovePrompt.value = false;
	filesToMove.value = []; // Clear captured paths
};

const handleDownload = async () => {
	if (!hasSelection.value && !isViewingFile.value) return;
	
	try {
		// For viewed file, always use single file download
		if (isViewingFile.value && !hasSelection.value) {
			api.downloadFile(viewedFile.value!, storageType.value);
			return;
		}
		
		// Check if any selected item is a directory or if multiple files
		const hasDirectory = selectedFilesArray.value.some(path => {
			const entry = selectedEntries.value.get(path);
			return entry?.is_dir === true;
		});
		
		// Use zip if multiple files or any directory
		if (selectedFilesArray.value.length > 1 || hasDirectory) {
			await api.downloadAsZip(selectedFilesArray.value, storageType.value);
		} else {
			// Single file - use regular download
			api.downloadFile(selectedFilesArray.value[0], storageType.value);
		}
	} catch (error) {
		console.error('Failed to download files', error);
		alert('Failed to download files.');
	}
};

const handleRename = () => {
	// Allow rename if viewing a single file or if exactly one file is selected
	if (isViewingFile.value && !hasSelection.value) {
		fileToRename.value = viewedFile.value!;
	} else if (selectedFiles.value.size === 1) {
		fileToRename.value = selectedFilesArray.value[0];
	} else {
		return;
	}
	
	const parts = fileToRename.value.split('/');
	renameNewName.value = parts[parts.length - 1];
	showRenamePrompt.value = true;
};

const handleRenameConfirm = async (newName: string) => {
	if (!fileToRename.value) return;
	
	try {
		const srcPath = fileToRename.value;
		const parts = srcPath.split('/');
		parts.pop(); // Remove old name
		const parentPath = parts.join('/');
		const dstPath = parentPath ? `${parentPath}/${newName}` : newName;
		await api.movePath(srcPath, dstPath, storageType.value);
		triggerRefresh();
		triggerHierarchyRefresh();
		showRenamePrompt.value = false;
		setSelectedFiles(new Set()); // Clear selection
		fileToRename.value = null; // Clear captured path
		// If we renamed the viewed file, navigate to the new path
		if (viewedFile.value === srcPath) {
			navigateToFile(dstPath);
		}
	} catch (error: any) {
		console.error('Failed to rename file', error);
		const message = error.response?.data?.detail || 'Failed to rename file. It may already exist.';
		alert(message);
		fileToRename.value = null; // Clear captured path on error
	}
};

const handleRenameCancel = () => {
	showRenamePrompt.value = false;
	fileToRename.value = null; // Clear captured path
};

const deleteCount = ref(0);
const filesToDelete = ref<string[]>([]);

const handleDelete = () => {
	if (!hasSelection.value && !isViewingFile.value) return;
	// Capture the count and file paths at the time of opening the modal
	deleteCount.value = selectedFilesArray.value.length;
	filesToDelete.value = [...selectedFilesArray.value];
	showDeleteModal.value = true;
};

const handleDeleteConfirm = async () => {
	try {
		// Check if we're deleting the viewed file
		const deletingViewedFile = viewedFile.value && filesToDelete.value.includes(viewedFile.value);
		
		// Use the captured file paths
		for (const filePath of filesToDelete.value) {
			await api.deletePath(filePath, storageType.value);
		}
		triggerRefresh();
		triggerHierarchyRefresh();
		setSelectedFiles(new Set()); // Clear selection
		showDeleteModal.value = false;
		filesToDelete.value = []; // Clear captured paths
		deleteCount.value = 0;
		
		// If we deleted the viewed file, close the viewer and navigate to parent folder
		if (deletingViewedFile && viewedFile.value) {
			closeFileViewer();
		}
	} catch (error: any) {
		console.error('Failed to delete files', error);
		const message = error.response?.data?.detail || 'Failed to delete files.';
		alert(message);
		showDeleteModal.value = false;
		filesToDelete.value = []; // Clear captured paths
		deleteCount.value = 0;
	}
};

const handleDeleteCancel = () => {
	showDeleteModal.value = false;
	filesToDelete.value = []; // Clear captured paths
	deleteCount.value = 0;
};
</script>

<template>
	<div class="w-full flex items-center p-2 border-b-neutral-200 border-b gap-1 overflow-x-auto md:overflow-x-visible scrollbar-hide">
		<ActionButton 
			title="Add file" 
			@click="handleAddFile"
			:disabled="!hasWritePermission"
		>
			<template #icon>
				<IconFileAdd class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
			</template>
		</ActionButton>
		<ActionButton 
			title="Add folder" 
			@click="handleAddFolder"
			:disabled="!hasWritePermission"
		>
			<template #icon>
				<IconFolderAdd class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
			</template>
		</ActionButton>
		<ActionButton 
			title="Upload" 
			@click="handleUpload"
			:disabled="!hasWritePermission"
		>
			<template #icon>
				<IconUpload class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
			</template>
		</ActionButton>
		
		<!-- Separator -->
		<div v-if="hasSelection || hasCopiedFiles || isViewingFile" class="h-6 w-px bg-neutral-300 mx-1"></div>
		
		<!-- Selection-based actions - always show when viewing file or has selection -->
		<template v-if="hasSelection || isViewingFile">
			<ActionButton 
				title="Copy" 
				@click="handleCopy"
				:disabled="!hasWritePermission"
			>
				<template #icon>
					<IconCopy class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
				</template>
			</ActionButton>
			<ActionButton 
				title="Move" 
				@click="handleMove"
				:disabled="!hasWritePermission"
			>
				<template #icon>
					<IconMove class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
				</template>
			</ActionButton>
			<ActionButton 
				title="Download" 
				@click="handleDownload"
			>
				<template #icon>
					<IconDownload class="w-5 h-5 text-text-secondary" />
				</template>
			</ActionButton>
			<ActionButton 
				title="Rename" 
				@click="handleRename"
				:disabled="hasMultipleSelection || !hasWritePermission"
			>
				<template #icon>
					<IconRename class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': hasMultipleSelection || !hasWritePermission }" />
				</template>
			</ActionButton>
			<ActionButton 
				title="Delete" 
				@click="handleDelete"
				:disabled="!hasWritePermission"
			>
				<template #icon>
					<IconDelete class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
				</template>
			</ActionButton>
			
			<!-- Separator -->
			<div class="h-6 w-px bg-neutral-300 mx-1"></div>
			
			<ActionButton 
				title="Share" 
				@click="handleShare"
			>
				<template #icon>
					<svg class="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
					</svg>
				</template>
			</ActionButton>
		</template>
		
		<!-- Paste button (shows when files are copied) -->
		<template v-if="hasCopiedFiles">
			<ActionButton 
				title="Paste" 
				@click="handlePaste"
				:disabled="!hasWritePermission"
			>
				<template #icon>
					<IconPaste class="w-5 h-5 text-text-secondary" :class="{ 'opacity-50': !hasWritePermission }" />
				</template>
			</ActionButton>
			<button
				@click="handleDiscardCopy"
				title="Discard copy"
				class="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-neutral-200/70 transition-colors text-text-secondary hover:text-neutral-800 cursor-pointer"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</template>
		
		<!-- Hidden file input for file uploads -->
		<input
			ref="fileInputRef"
			type="file"
			multiple
			class="hidden"
			@change="handleFileInputChange"
		/>
		
		<!-- Hidden file input for folder uploads -->
		<input
			ref="folderInputRef"
			type="file"
			multiple
			webkitdirectory
			directory
			class="hidden"
			@change="handleFolderInputChange"
		/>

		<!-- Upload Modal -->
		<UploadModal
			v-if="showUploadModal"
			@select-files="handleSelectFiles"
			@select-folders="handleSelectFolders"
			@close="showUploadModal = false"
		/>

		<!-- Progress Modal -->
		<ProgressModal
			:show="showProgressModal"
			:progress="uploadProgress"
			:status="uploadStatus"
			:estimated-time="estimatedTimeRemaining"
		/>

		<!-- Name prompts -->
		<NamePrompt
			v-if="showFilePrompt"
			title="Create New File"
			placeholder="Enter file name"
			@confirm="handleFilePromptConfirm"
			@cancel="handleFilePromptCancel"
		/>
		<NamePrompt
			v-if="showFolderPrompt"
			title="Create New Folder"
			placeholder="Enter folder name"
			@confirm="handleFolderPromptConfirm"
			@cancel="handleFolderPromptCancel"
		/>
		<NamePrompt
			v-if="showRenamePrompt"
			title="Rename"
			placeholder="Enter new name"
			:default-value="renameNewName"
			button-text="Save"
			@confirm="handleRenameConfirm"
			@cancel="handleRenameCancel"
		/>
		<FolderPickerModal
			v-if="showMovePrompt"
			:show="showMovePrompt"
			:current-storage-type="storageType"
			:current-username="currentUsername"
			@select="handleMoveConfirm"
			@close="handleMoveCancel"
		/>
		<DeleteConfirmModal
			:show="showDeleteModal"
			:count="deleteCount"
			@confirm="handleDeleteConfirm"
			@cancel="handleDeleteCancel"
		/>
		<ShareModal
			:show="showShareModal"
			:path="sharePath"
			:storage-type="storageType"
			:is-file="shareIsFile"
			@close="showShareModal = false"
		/>
	</div>
</template>

<style scoped>
.icon-secondary {
	filter: brightness(0) saturate(100%) invert(33%) sepia(4%) saturate(879%)
		hue-rotate(208deg) brightness(94%) contrast(88%);
}
</style>
