import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

const apiUrl = process.env.VITE_API_URL || 'http://127.0.0.1:8000';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        proxy: {
            '/api': {
                target: apiUrl,
                changeOrigin: true,
            },
            '/auth': {
                target: apiUrl,
                changeOrigin: true,
            }
        }
    }
});
