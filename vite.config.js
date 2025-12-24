import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy /search and /song to the Flask backend running on 5000
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/search': 'http://127.0.0.1:5000',
      '/song': 'http://127.0.0.1:5000'
    }
  }
})
