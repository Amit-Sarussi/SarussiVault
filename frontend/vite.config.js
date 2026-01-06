import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import svgLoader from "vite-svg-loader"

export default defineConfig({
  plugins: [vue(), tailwindcss(), svgLoader()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      // Capture any request starting with /api
      '/api': {
        target: 'http://127.0.0.1:8080', // Your Windows FileBrowser instance
        changeOrigin: true,
        secure: false,
      }
    }
  }
})