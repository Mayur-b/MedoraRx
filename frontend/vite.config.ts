import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// MedoraRx frontend dev server. The backend runs at http://127.0.0.1:8000.
// CORS is enabled server-side, but we also proxy /api during dev for cleanliness.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
