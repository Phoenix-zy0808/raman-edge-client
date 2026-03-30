/**
 * 全局测试设置
 */
import { afterEach } from 'vitest';

// 模拟 window 对象
global.window = global.window || {};
global.document = global.document || {};

// 模拟 localStorage
const localStorageMock = {
  store: {},
  getItem(key) {
    return this.store[key] || null;
  },
  setItem(key, value) {
    this.store[key] = String(value);
  },
  removeItem(key) {
    delete this.store[key];
  },
  clear() {
    this.store = {};
  }
};

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock
});

// 模拟 QWebChannel
global.QWebChannel = function(transport, callback) {
  callback({
    objects: {
      BridgeObject: null
    }
  });
};

// 模拟 ECharts
global.echarts = {
  init: () => ({
    setOption: () => {},
    resize: () => {},
    dispose: () => {},
    clear: () => {}
  })
};

// 每个测试后清理 DOM（使用 vitest 内置清理）
afterEach(() => {
  if (document.body) {
    document.body.innerHTML = '';
  }
});
