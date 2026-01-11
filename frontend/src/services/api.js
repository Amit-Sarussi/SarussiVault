import axios from 'axios';

// Helper functions for cookie management
function setCookie(name, value, days = 3650) {
  // Set cookie to expire in 10 years (effectively never expires)
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
}

function getCookie(name) {
  const nameEQ = name + '=';
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

function deleteCookie(name) {
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
}

// Axios client for the FastAPI backend. In dev, you can set VITE_API_BASE=http://localhost:8000.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  withCredentials: true, // Enable cookies
});

// Add request interceptor to include JWT token in Authorization header
api.interceptors.request.use(
  (config) => {
    const token = getCookie('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear cookie and redirect to login
      // But don't redirect if we're on a guest route (/open/)
      const isGuestRoute = window.location.pathname.startsWith('/open/');
      if (!isGuestRoute) {
        deleteCookie('jwt_token');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default {
  // Login and store JWT token in cookie
  async login(username, password) {
    const response = await api.post('/login', { username, password });
    const token = response.data.access_token;
    setCookie('jwt_token', token);
    return response.data;
  },

  // Logout (clear token)
  logout() {
    deleteCookie('jwt_token');
  },

  // Check if user is authenticated
  // Checks if JWT token cookie exists (cookie is readable since httponly=false)
  isAuthenticated() {
    const token = getCookie('jwt_token');
    return token !== null && token !== undefined && token !== '';
  },

  // Get current username from token
  async getCurrentUsername() {
    try {
      const response = await api.get('/verify');
      return response.data.username;
    } catch (error) {
      return null;
    }
  },

  // Helper to prefix path with storage type
  _prefixPath(path, storageType) {
    const normalizedPath = path.replace(/\\/g, '/').replace(/^\/+/, '');
    if (normalizedPath.startsWith('shared/') || normalizedPath.startsWith('private/')) {
      return normalizedPath;
    }
    const prefix = storageType === 'shared' ? 'shared' : 'private';
    if (normalizedPath === '') {
      return prefix;
    }
    return `${prefix}/${normalizedPath}`;
  },

  // List directory entries at the given path
  async listDirectory(path = '', storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.get('/list', { params: { path: prefixedPath } });
    return response.data;
  },
  
  // Get full directory hierarchy (recursive)
  async getHierarchy(path = '', storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.get('/hierarchy', { params: { path: prefixedPath } });
    return response.data;
  },
  
  // Search for files and folders matching query within the given path
  async searchFiles(path = '', query = '', storageType = 'shared') {
    if (!query || !query.trim()) {
      return [];
    }
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.get('/search', { 
      params: { path: prefixedPath, query: query.trim() } 
    });
    return response.data;
  },
  
  // Get file URL for viewing (images, videos, PDFs, etc.)
  getFileUrl(path, storageType = 'shared') {
    const baseURL = api.defaults.baseURL || '/api';
    const base = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
    const prefixedPath = this._prefixPath(path, storageType);
    const params = new URLSearchParams({ path: prefixedPath });
    return `${base}/file?${params.toString()}`;
  },
  
  // Get file content as text (for text files, code, etc.)
  async getFileContent(path, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.get('/file', { 
      params: { path: prefixedPath },
      responseType: 'text'
    });
    return response.data;
  },
  
  // Save file content
  async saveFileContent(path, content, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.put('/file', {
      path: prefixedPath,
      content: content
    });
    return response.data;
  },
  
  // Save file content
  async saveFileContent(path, content, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.put('/file', {
      path: prefixedPath,
      content: content
    });
    return response.data;
  },
  
  // Check if a path exists (returns true if path exists, false otherwise)
  async pathExists(path, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    try {
      // Try to list the directory - if it succeeds, it's a directory
      await api.get('/list', { params: { path: prefixedPath } });
      return true;
    } catch (listError) {
      // If 404 or 400 (not a directory), try checking if it's a file
      if (listError.response?.status === 404 || listError.response?.status === 400) {
        try {
          // Try to get the file - use HEAD to avoid downloading
          await api.request({
            method: 'HEAD',
            url: '/file',
            params: { path: prefixedPath }
          });
          return true;
        } catch (fileError) {
          // Both failed, path doesn't exist
          return false;
        }
      }
      // For other errors, assume it doesn't exist
      return false;
    }
  },
  
  // Create an empty file
  async createFile(path, name, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.post('/create-file', { path: prefixedPath, name });
    return response.data;
  },
  
  // Create a directory
  async createDirectory(path, name, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.post('/mkdir', { path: prefixedPath, name });
    return response.data;
  },
  
  // Chunk size for uploads (1MB to stay well under 1.4MB limit)
  CHUNK_SIZE: 1024 * 1024, // 1MB

  // Check if file needs chunked upload (larger than chunk size)
  _needsChunkedUpload(file) {
    return file.size > this.CHUNK_SIZE;
  },

  // Upload a single file using chunked upload
  async _uploadFileChunked(path, file, relativePath, storageType = 'shared', onProgress) {
    const prefixedPath = this._prefixPath(path, storageType);
    const filename = file.name;
    const totalSize = file.size;
    const totalChunks = Math.ceil(totalSize / this.CHUNK_SIZE);
    
    // Initialize chunked upload
    const initResponse = await api.post('/upload-chunk-init', {
      path: prefixedPath,
      filename: filename,
      total_size: totalSize,
      total_chunks: totalChunks,
      relative_path: relativePath || null,
    });
    
    const uploadId = initResponse.data.upload_id;
    let uploadedBytes = 0;
    
    try {
      // Upload each chunk
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * this.CHUNK_SIZE;
        const end = Math.min(start + this.CHUNK_SIZE, totalSize);
        const chunkBlob = file.slice(start, end);
        
        const chunkFormData = new FormData();
        chunkFormData.append('chunk', chunkBlob, `chunk_${chunkIndex}`);
        
        // Use query params for upload_id and chunk_index, chunk file in form data
        const response = await api.post(
          `/upload-chunk?upload_id=${uploadId}&chunk_index=${chunkIndex}`,
          chunkFormData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );
        
        uploadedBytes = end;
        
        // Update progress
        if (onProgress) {
          const progress = Math.round((uploadedBytes * 100) / totalSize);
          onProgress(progress, uploadedBytes, totalSize);
        }
      }
      
      // Finalize upload
      await api.post('/upload-chunk-finalize', {
        upload_id: uploadId,
      });
      
      return { success: true };
    } catch (error) {
      // Cleanup on error - try to finalize which will cleanup, or let server timeout handle it
      console.error('Chunked upload failed:', error);
      throw error;
    }
  },

  // Upload multiple files (supports folders via webkitdirectory)
  // Automatically uses chunked upload for files > CHUNK_SIZE
  // Batches small files but keeps batches under 1MB to respect Cloudflare tunnel limit
  async uploadFiles(path, files, storageType = 'shared', onProgress) {
    const prefixedPath = this._prefixPath(path, storageType);
    let totalBytes = 0;
    
    // Calculate total size
    for (const file of files) {
      totalBytes += file.size;
    }
    
    let processedBytes = 0;
    const BATCH_SIZE_LIMIT = 1024 * 1024; // 1MB batch limit to stay under 1.4MB
    
    try {
      // Separate files into those that need chunked upload and those that can be batched
      const largeFiles = [];
      const smallFiles = [];
      
      for (const file of files) {
        if (this._needsChunkedUpload(file)) {
          largeFiles.push(file);
        } else {
          smallFiles.push(file);
        }
      }
      
      // Process large files with chunked upload
      for (const file of largeFiles) {
        const relativePath = file.webkitRelativePath || file.relativePath || null;
        
        const fileOnProgress = (progress, loaded, total) => {
          // Calculate overall progress
          const fileStartBytes = processedBytes;
          const fileUploadedBytes = loaded;
          const overallUploaded = fileStartBytes + fileUploadedBytes;
          
          if (onProgress && totalBytes > 0) {
            const overallProgress = Math.round((overallUploaded * 100) / totalBytes);
            onProgress(overallProgress, overallUploaded, totalBytes);
          }
        };
        
        await this._uploadFileChunked(path, file, relativePath, storageType, fileOnProgress);
        processedBytes += file.size;
      }
      
      // Process small files in batches
      if (smallFiles.length > 0) {
        let currentBatch = [];
        let currentBatchSize = 0;
        
        for (const file of smallFiles) {
          // If adding this file would exceed batch limit, upload current batch first
          if (currentBatch.length > 0 && currentBatchSize + file.size > BATCH_SIZE_LIMIT) {
            // Upload current batch
            const formData = new FormData();
            for (const batchFile of currentBatch) {
              formData.append('files', batchFile);
            }
            
            const config = {
              params: { path: prefixedPath },
              headers: {
                'Content-Type': 'multipart/form-data',
              },
            };
            
            if (onProgress) {
              config.onUploadProgress = (progressEvent) => {
                if (progressEvent.total) {
                  const batchStartBytes = processedBytes - currentBatchSize;
                  const batchLoadedBytes = progressEvent.loaded;
                  const overallUploaded = batchStartBytes + batchLoadedBytes;
                  const overallProgress = Math.round((overallUploaded * 100) / totalBytes);
                  onProgress(overallProgress, overallUploaded, totalBytes);
                }
              };
            }
            
            await api.post('/upload-multiple', formData, config);
            processedBytes += currentBatchSize;
            
            // Update progress after batch
            if (onProgress && totalBytes > 0) {
              const overallProgress = Math.round((processedBytes * 100) / totalBytes);
              onProgress(overallProgress, processedBytes, totalBytes);
            }
            
            // Start new batch
            currentBatch = [];
            currentBatchSize = 0;
          }
          
          // Add file to current batch
          currentBatch.push(file);
          currentBatchSize += file.size;
        }
        
        // Upload remaining batch
        if (currentBatch.length > 0) {
          const formData = new FormData();
          for (const batchFile of currentBatch) {
            formData.append('files', batchFile);
          }
          
          const config = {
            params: { path: prefixedPath },
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          };
          
          if (onProgress) {
            config.onUploadProgress = (progressEvent) => {
              if (progressEvent.total) {
                const batchStartBytes = processedBytes;
                const batchLoadedBytes = progressEvent.loaded;
                const overallUploaded = batchStartBytes + batchLoadedBytes;
                const overallProgress = Math.round((overallUploaded * 100) / totalBytes);
                onProgress(overallProgress, overallUploaded, totalBytes);
              }
            };
          }
          
          await api.post('/upload-multiple', formData, config);
          processedBytes += currentBatchSize;
        }
      }
      
      // Final progress update
      if (onProgress && totalBytes > 0) {
        onProgress(100, totalBytes, totalBytes);
      }
      
      return { success: true, detail: `${files.length} file(s) uploaded` };
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  },
  
  // Delete a file or folder
  async deletePath(path, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.delete('/delete', { params: { path: prefixedPath } });
    return response.data;
  },
  
  // Move a file or folder
  async movePath(src, dst, storageType = 'shared') {
    const prefixedSrc = this._prefixPath(src, storageType);
    const prefixedDst = this._prefixPath(dst, storageType);
    const response = await api.post('/move', { src: prefixedSrc, dst: prefixedDst });
    return response.data;
  },
  
  // Copy a file or folder
  async copyPath(src, dst, storageType = 'shared') {
    const prefixedSrc = this._prefixPath(src, storageType);
    const prefixedDst = this._prefixPath(dst, storageType);
    const response = await api.post('/copy', { src: prefixedSrc, dst: prefixedDst });
    return response.data;
  },
  
  // Download a file (triggers browser download)
  downloadFile(path, storageType = 'shared') {
    const prefixedPath = this._prefixPath(path, storageType);
    const fileUrl = this.getFileUrl(path, storageType);
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = path.split('/').pop() || 'file';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
  
  // Download multiple files/folders as zip
  async downloadAsZip(paths, storageType = 'shared') {
    const prefixedPaths = paths.map(path => this._prefixPath(path, storageType));
    const response = await api.post('/download-zip', { paths: prefixedPaths }, {
      responseType: 'blob'
    });
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/zip' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Determine filename
    const filename = paths.length === 1 
      ? `${paths[0].split('/').pop() || 'download'}.zip`
      : 'download.zip';
    link.download = filename;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
  
  // Share endpoints
  async createShare(path, storageType, permissions = 'read', expiresAt = null) {
    const prefixedPath = this._prefixPath(path, storageType);
    const response = await api.post('/share', {
      path: prefixedPath,
      storage_type: storageType,
      permissions: permissions,
      expires_at: expiresAt
    });
    return response.data;
  },
  
  async getShareInfo(shareId) {
    const response = await api.get(`/share/${shareId}`);
    return response.data;
  },
  
  // Guest access endpoints (for shared links)
  async listSharedDirectory(shareId, path = '') {
    const response = await api.get(`/open/${shareId}/list`, { params: { path } });
    return response.data;
  },
  
  async getSharedFile(shareId, path = '') {
    return this.getFileUrl(path, 'shared', shareId);
  },
  
  getSharedFileUrl(shareId, path = '') {
    const baseURL = api.defaults.baseURL || '/api';
    const base = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
    const params = new URLSearchParams({ path });
    return `${base}/open/${shareId}/file?${params.toString()}`;
  },
  
  async getSharedFileContent(shareId, path = '') {
    const response = await api.get(`/open/${shareId}/file`, { 
      params: { path },
      responseType: 'text'
    });
    return response.data;
  },
  
  async saveSharedFileContent(shareId, path, content) {
    const response = await api.put(`/open/${shareId}/file`, {
      path: path,
      content: content
    });
    return response.data;
  },
  
  async getSharedHierarchy(shareId, path = '') {
    const response = await api.get(`/open/${shareId}/hierarchy`, { params: { path } });
    return response.data;
  },
  
  async searchSharedFiles(shareId, path = '', query = '') {
    if (!query || !query.trim()) {
      return [];
    }
    const response = await api.get(`/open/${shareId}/search`, { 
      params: { path, query: query.trim() } 
    });
    return response.data;
  },
  
  async createSharedDirectory(shareId, path, name) {
    const response = await api.post(`/open/${shareId}/mkdir`, { path, name });
    return response.data;
  },
  
  async createSharedFile(shareId, path, name) {
    const response = await api.post(`/open/${shareId}/create-file`, { path, name });
    return response.data;
  },
  
  async deleteSharedPath(shareId, path) {
    const response = await api.delete(`/open/${shareId}/delete`, { params: { path } });
    return response.data;
  },
  
  async moveSharedPath(shareId, src, dst) {
    const response = await api.post(`/open/${shareId}/move`, { src, dst });
    return response.data;
  },
  
  async copySharedPath(shareId, src, dst) {
    const response = await api.post(`/open/${shareId}/copy`, { src, dst });
    return response.data;
  },
  
  async uploadSharedFiles(shareId, path, files, onProgress) {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }
    
    const config = {
      params: { path },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };
    
    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress, progressEvent.loaded, progressEvent.total);
        }
      };
    }
    
    const response = await api.post(`/open/${shareId}/upload-multiple`, formData, config);
    return response.data;
  },
  
  async downloadSharedAsZip(shareId, paths) {
    const response = await api.post(`/open/${shareId}/download-zip`, { paths }, {
      responseType: 'blob'
    });
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/zip' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Determine filename
    const filename = paths.length === 1 
      ? `${paths[0].split('/').pop() || 'download'}.zip`
      : 'download.zip';
    link.download = filename;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
  
  downloadSharedFile(shareId, path) {
    const fileUrl = this.getSharedFileUrl(shareId, path);
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = path.split('/').pop() || 'file';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
};
