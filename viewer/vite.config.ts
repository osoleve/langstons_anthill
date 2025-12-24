import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/events': 'http://localhost:5000',
      '/state': 'http://localhost:5000',
      '/bless': 'http://localhost:5000',
      '/blessings': 'http://localhost:5000',
      '/decisions': 'http://localhost:5000'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
