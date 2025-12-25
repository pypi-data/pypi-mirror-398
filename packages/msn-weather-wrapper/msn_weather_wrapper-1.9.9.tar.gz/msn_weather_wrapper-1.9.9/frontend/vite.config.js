import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['frontend-srv', 'localhost'],
    proxy: {
      '/api': {
        target: process.env.NODE_ENV === 'development' && process.env.DOCKER_ENV
          ? 'http://api:5000'
          : 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
