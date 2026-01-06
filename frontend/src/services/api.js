import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: '/api', // Triggers the Vite proxy
});

// Add a request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fb_token');
  if (token) {
    // FileBrowser expects the token in the X-Auth header
    config.headers['X-Auth'] = token;
  }
  return config;
});

export default {
  // Login function
  async login(username, password) {
    const response = await api.post('/login', { username, password });
    // FileBrowser returns the token directly as a string
    const token = response.data;
    localStorage.setItem('fb_token', token);
    return token;
  },

  // Get files for a specific path
  async getFiles(path = '') {
    // /resources/ is the endpoint for listing files
    const response = await api.get(`/resources/${path}`);
    return response.data;
  }
};