import type { StorageType } from '@/context/appContext';

/**
 * Prefix a path with the storage type (shared/private)
 */
export function prefixStoragePath(path: string, storageType: StorageType): string {
  // Normalize path
  const normalizedPath = path.replace(/\\/g, '/').replace(/^\/+/, '');
  
  // If path already has a storage prefix, return as is
  if (normalizedPath.startsWith('shared/') || normalizedPath.startsWith('private/')) {
    return normalizedPath;
  }
  
  // Add storage prefix
  const prefix = storageType === 'shared' ? 'shared' : 'private';
  if (normalizedPath === '') {
    return prefix;
  }
  return `${prefix}/${normalizedPath}`;
}

/**
 * Remove storage prefix from a path (for display purposes)
 */
export function removeStoragePrefix(path: string): string {
  if (path.startsWith('shared/')) {
    return path.substring(7); // Remove "shared/"
  }
  if (path.startsWith('private/')) {
    return path.substring(8); // Remove "private/"
  }
  return path;
}
