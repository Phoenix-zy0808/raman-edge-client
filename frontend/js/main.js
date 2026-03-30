/**
 * 拉曼光谱边缘客户端 - 主入口
 * @module main
 *
 * P12 重构：拆分为 app-lifecycle.js、event-handlers.js
 * 此文件仅作为应用入口，保持精简（<100 行）
 */

import { initApp } from './app-lifecycle.js';
import { initGlobalEventHandlers, setupStatusBarUpdates } from './event-handlers.js';
import { initAIAnalysis } from './ai-analysis.js';
import { initDemoLoader } from './demo-loader.js';
import { events, EventTypes } from './event-bus.js';
import { api } from './bridge.js';

/**
 * 应用入口点
 */
function main() {
    // 初始化全局事件处理
    initGlobalEventHandlers();

    // 初始化应用
    initApp();

    // 初始化 AI 分析模块
    initAIAnalysis();

    // 初始化演示数据加载器（延迟确保 DOM 已加载）
    setTimeout(() => {
        initDemoLoader();
        console.log('[Main] 演示数据加载器已初始化');
    }, 100);

    // 设置状态栏更新
    setupStatusBarUpdates();

    // 初始化 API
    api.init();

    // 监听应用事件
    events.on(EventTypes.ERROR_OCCURRED, (error) => {
        console.error('[App] 错误:', error);
    });

    events.on(EventTypes.LOG_ADDED, (log) => {
        console.log('[Log]', log);
    });

    // 导出到全局（仅用于调试）
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.__APP__ = {
            events,
            EventTypes,
            api,
        };
    }
}

// 启动应用
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', main);
} else {
    main();
}

export { events, EventTypes, api };
export default { main, events, EventTypes, api };
