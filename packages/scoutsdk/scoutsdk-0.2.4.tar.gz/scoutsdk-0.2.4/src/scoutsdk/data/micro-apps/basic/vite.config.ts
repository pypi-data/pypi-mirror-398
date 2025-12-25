import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import svgr from 'vite-plugin-svgr';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), svgr()],
  build: {
    assetsInlineLimit: 100000000, // Set to a very high number to inline all assets (eg.: images) (base64) rather than load them as separate files
  },
  server: {
    port: 5173, // We force the port to 5173 because this port is whitelisted to develop micro apps in Scout
    strictPort: true,
  },
});
