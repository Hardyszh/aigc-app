import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // 👇 下面是新增的代理配置 👇
  server: {
    proxy: {
      '/api': {
        // ⚠️ 注意：这里的端口号 8000 需要换成你 Python 后端实际运行的端口
        // 可能是 8000 (FastAPI/Django), 5000 (Flask), 或 3000 等
        target: 'http://127.0.0.1:8000', 
        changeOrigin: true,
        // 如果你的后端接口本身没有 /api 前缀，需要加上下面这行重写路径
        // rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  }
})