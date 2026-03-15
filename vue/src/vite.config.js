import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  // Load .env.development / .env.production into `env` so we can use
  // VITE_BACKEND_URL inside the config itself (not just in component code).
  const env = loadEnv(mode, process.cwd(), '')
  const BACKEND = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],

    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },

    server: {
      port: 3000,

      proxy: {
        // ── Django REST API ────────────────────────────────────────────────
        '/api': { target: BACKEND, changeOrigin: true },

        // ── Django Admin ───────────────────────────────────────────────────
        '/admin': { target: BACKEND, changeOrigin: true },

        // ── allauth account pages (password reset, email confirm, etc.) ───
        '/accounts': { target: BACKEND, changeOrigin: true },

        // ── OAuth (allauth) ────────────────────────────────────────────────
        // Proxy every /oauth/* path to Django EXCEPT /oauth/callback.
        // /oauth/callback is a Vue Router route — it must be handled
        // client-side so OAuthCallbackView.vue can read the JWT from the URL.
        '^/oauth/(?!callback($|\\?))': { target: BACKEND, changeOrigin: true },

        // ── Uploaded media files ───────────────────────────────────────────
        '/media': { target: BACKEND, changeOrigin: true },
      },
    },
  }
})
