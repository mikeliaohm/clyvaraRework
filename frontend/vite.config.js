import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

//frontend runs on 8001
//backend runs on 8000

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8001,
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
        // Don't rewrite - keep /api in the path since backend expects it
      },
    },
  },
});
