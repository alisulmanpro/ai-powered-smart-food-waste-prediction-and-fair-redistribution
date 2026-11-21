import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on 0.0.0.0 so it also works inside Docker
    port: 5173,
    strictPort: true,
    // Bind mounts on Windows/macOS Docker do not deliver file events -> poll instead.
    watch: { usePolling: process.env.CHOKIDAR_USEPOLLING === 'true' },
  },
})
