import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path' // Keep the standard path import

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // This is the definitive, documented, and correct way to set up the alias.
      // It resolves the current directory and appends 'src'.
      '@': path.resolve(__dirname, './src'),
    }
  }
})