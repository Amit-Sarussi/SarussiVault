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
      deleteCookie('jwt_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
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
  
  // Upload multiple files (supports folders via webkitdirectory)
  async uploadFiles(path, files, storageType = 'shared', onProgress) {
    const prefixedPath = this._prefixPath(path, storageType);
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }
    
    const config = {
      params: { path: prefixedPath },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };
    
    // Add progress tracking if callback provided
    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted, progressEvent.loaded, progressEvent.total);
        }
      };
    }
    
    const response = await api.post('/upload-multiple', formData, config);
    return response.data;
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
};
