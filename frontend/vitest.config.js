import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  test: {
    // 使用 jsdom 模拟浏览器环境
    environment: 'jsdom',

    // 测试文件匹配模式
    include: ['tests/**/*.test.{js,ts}'],

    // 排除模式
    exclude: ['**/node_modules/**', '**/dist/**', '**/build/**', '**/.git/**'],

    // 测试超时时间（毫秒）
    testTimeout: 10000,

    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['js/**/*.js'],
      exclude: ['js/**/*.min.js'],
      threshold: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70
      }
    },

    // 全局测试设置
    setupFiles: ['./tests/setup.js'],

    // 全局测试钩子
    globalSetup: ['./tests/global-setup.js'],

    // 并发测试
    pool: 'threads',

    // 报告器
    reporters: ['default', 'html']
  },

  // 路径别名 - Vite 配置
  resolve: {
    alias: {
      '@': resolve(__dirname, './js'),
    }
  }
});
