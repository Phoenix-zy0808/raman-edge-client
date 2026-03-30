/**
 * 应用生命周期管理模块
 * @module app-lifecycle
 *
 * 负责应用的初始化、启动、停止等生命周期管理
 */

import { initChart, resizeChart } from './chart.js';
import { initChannel, isBackendAvailable, api } from './bridge.js';
import { initUI, initKeyboardShortcuts, checkFirstRun, showLoading } from './ui.js';
import { addLog, createEventCleanup, createTimerManager, debounce } from './utils.js';
import { createVirtualLog, setVirtualLogInstance } from './virtual-scroll.js';
import { getThemeManager, createThemeSelector } from './theme.js';
import { hideAllSkeletons, showChartSkeleton } from './skeleton.js';
import { setState } from './state.js';
import { events, EventTypes, createEventManager } from './event-bus.js';
import { initFocusTraps } from './event-handlers.js';

// 应用状态
let appState = {
    initialized: false,
    started: false,
    stopped: false,
};

// 管理器实例
let virtualLog = null;
let themeManager = null;
let eventManager = null;

/**
 * 应用初始化
 */
export function initApp() {
    if (appState.initialized) {
        console.warn('[App] 应用已初始化，跳过');
        return;
    }

    addLog('应用初始化开始...');

    // 初始化状态
    setState('isConnected', false);
    setState('isAcquiring', false);
    setState('spectrumData', []);
    setState('wavelengthData', []);

    // 显示加载动画
    showLoading(true);

    // 创建事件管理器
    eventManager = createEventManager();

    // 初始化图表
    initChart();

    // 初始化虚拟滚动日志
    try {
        virtualLog = createVirtualLog('#log-panel', {
            itemHeight: 24,
            maxItems: 1000,
            bufferSize: 5,
        });
        setVirtualLogInstance(virtualLog);
        addLog('虚拟滚动日志初始化成功');
    } catch (error) {
        console.warn('[App] 虚拟滚动初始化失败，使用传统日志模式:', error);
    }

    // 初始化主题管理器
    try {
        themeManager = getThemeManager();
        const themeSelectorContainer = document.getElementById('theme-selector-container');
        if (themeSelectorContainer) {
            createThemeSelector('#theme-selector-container', themeManager);
        }
        addLog('主题管理器初始化成功');
    } catch (error) {
        console.warn('[App] 主题管理器初始化失败:', error);
    }

    // 初始化 UI 控件
    initUI();

    // 初始化键盘快捷键
    initKeyboardShortcuts();

    // 初始化焦点陷阱（A11y）
    initFocusTraps();

    // 检查是否首次运行
    checkFirstRun();

    // 初始化桥接
    initChannel(onBridgeReady);

    // 设置窗口大小变化监听
    setupResizeListener();

    // 设置 FPS 计数器
    setupFpsCounter();

    appState.initialized = true;
    addLog('应用初始化完成');
}

/**
 * 桥接就绪回调
 * @param {Object} backend - 后端对象
 */
function onBridgeReady(backend) {
    addLog('后端桥接已就绪', 'success');

    // 隐藏加载动画
    setTimeout(() => {
        showLoading(false);
        hideAllSkeletons();
    }, 500);

    // 启用高级控件
    enableAdvancedControls();

    // 设置桥接就绪状态
    window.__BRIDGE_READY__ = true;

    // 触发应用启动事件
    events.emit(EventTypes.DEVICE_CONNECTED, { backend });

    appState.started = true;
}

/**
 * 启用高级控件
 */
function enableAdvancedControls() {
    // 启用所有控制按钮
    const buttons = document.querySelectorAll('button[disabled]');
    buttons.forEach(btn => {
        btn.disabled = false;
    });

    addLog('高级控件已启用');
}

/**
 * 设置窗口大小变化监听
 */
function setupResizeListener() {
    const pageEventCleanup = createEventCleanup();

    const throttledResize = debounce(() => {
        resizeChart();
    }, 200);

    pageEventCleanup.add(window, 'resize', throttledResize);

    // 页面卸载时清理
    window.addEventListener('beforeunload', () => {
        pageEventCleanup.removeAll();
    });
}

/**
 * 设置 FPS 计数器
 */
function setupFpsCounter() {
    let frameCount = 0;
    let lastFpsTime = Date.now();

    function updateFps() {
        frameCount++;
        const now = Date.now();
        const elapsed = now - lastFpsTime;

        if (elapsed >= 1000) {
            const fps = Math.round((frameCount * 1000) / elapsed);
            const fpsElement = document.getElementById('fps-counter');
            if (fpsElement) {
                fpsElement.textContent = `FPS: ${fps}`;
            }
            frameCount = 0;
            lastFpsTime = now;
        }

        if (!appState.stopped) {
            requestAnimationFrame(updateFps);
        }
    }

    requestAnimationFrame(updateFps);
}

/**
 * 获取应用状态
 * @returns {Object} 应用状态
 */
export function getAppState() {
    return { ...appState };
}

/**
 * 获取虚拟日志实例
 * @returns {Object} 虚拟日志实例
 */
export function getVirtualLog() {
    return virtualLog;
}

/**
 * 获取主题管理器
 * @returns {Object} 主题管理器
 */
export function getThemeManagerInstance() {
    return themeManager;
}

/**
 * 获取事件管理器
 * @returns {Object} 事件管理器
 */
export function getEventManager() {
    return eventManager;
}

/**
 * 停止应用
 */
export function stopApp() {
    if (appState.stopped) {
        return;
    }

    addLog('应用停止中...');

    appState.stopped = true;

    // 清理事件管理器
    if (eventManager) {
        eventManager.cleanup();
    }

    addLog('应用已停止');
}

export default {
    initApp,
    stopApp,
    getAppState,
    getVirtualLog,
    getThemeManagerInstance,
    getEventManager,
};
