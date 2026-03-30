/**
 * 全局事件处理模块
 * @module event-handlers
 *
 * 处理全局事件和回调，使用事件总线替代全局耦合
 */

import { events, EventTypes } from './event-bus.js';
import { addLog, createEventCleanup } from './utils.js';
import { updateConnectionStatus, updateAcquisitionStatus, updateCalibrationStatus } from './ui.js';
import { createFocusTrap, focusTrapManager } from './focus-trap.js';

// 页面级事件监听器管理器
const pageEventCleanup = createEventCleanup();

/**
 * 初始化全局事件处理
 */
export function initGlobalEventHandlers() {
    setupMessageListener();
    setupErrorHandlers();
    setupVisibilityHandler();
}

/**
 * 设置 postMessage 监听器（带源验证）
 */
function setupMessageListener() {
    const TARGET_ORIGIN = window.location.origin;

    window.addEventListener('message', (event) => {
        // ✅ 验证消息源
        if (event.origin !== TARGET_ORIGIN) {
            console.warn('[Security] 拒绝来自未知源的消息:', event.origin);
            return;
        }

        // 处理消息
        handleMessage(event.data);
    });
}

/**
 * 处理消息
 * @param {any} data - 消息数据
 */
function handleMessage(data) {
    if (!data || typeof data !== 'object') {
        return;
    }

    const { type, payload } = data;

    switch (type) {
        case 'spectrum-update':
            events.emit(EventTypes.SPECTRUM_READY, payload);
            break;
        case 'status-change':
            if (payload.connected !== undefined) {
                updateConnectionStatus(payload.connected);
            }
            if (payload.acquiring !== undefined) {
                updateAcquisitionStatus(payload.acquiring);
            }
            break;
        case 'calibration-result':
            if (payload.type === 'wavelength') {
                if (payload.success) {
                    events.emit(EventTypes.CALIBRATION_WAVELENGTH_SUCCESS, payload.data);
                } else {
                    events.emit(EventTypes.CALIBRATION_WAVELENGTH_FAILED, payload.error);
                }
            } else if (payload.type === 'intensity') {
                if (payload.success) {
                    events.emit(EventTypes.CALIBRATION_INTENSITY_SUCCESS, payload.data);
                } else {
                    events.emit(EventTypes.CALIBRATION_INTENSITY_FAILED, payload.error);
                }
            }
            break;
        default:
            console.log('[Message] 未知消息类型:', type);
    }
}

/**
 * 设置错误处理
 */
function setupErrorHandlers() {
    // 全局错误处理
    window.addEventListener('error', (event) => {
        console.error('[Global Error]', event.error);
        addLog(`全局错误：${event.error?.message || '未知错误'}`, 'error');
        events.emit(EventTypes.ERROR_OCCURRED, {
            message: event.error?.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
        });
    });

    // 未捕获的 Promise 错误
    window.addEventListener('unhandledrejection', (event) => {
        console.error('[Unhandled Rejection]', event.reason);
        addLog(`未处理的 Promise 错误：${event.reason?.message || '未知错误'}`, 'error');
        events.emit(EventTypes.ERROR_OCCURRED, {
            message: event.reason?.message,
            type: 'unhandledrejection',
        });
    });
}

/**
 * 设置页面可见性处理
 */
function setupVisibilityHandler() {
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            addLog('页面已隐藏，降低更新频率', 'info');
            events.emit('app:visibility-changed', { hidden: true });
        } else {
            addLog('页面已显示，恢复正常更新', 'info');
            events.emit('app:visibility-changed', { hidden: false });
        }
    });
}

/**
 * 初始化焦点陷阱（A11y 合规）
 */
export function initFocusTraps() {
    // 注册对话框焦点陷阱
    const dialogs = [
        { id: 'theme-panel', name: 'theme' },
        { id: 'library-panel', name: 'library' },
        { id: 'peak-area-panel', name: 'peakArea' },
    ];

    dialogs.forEach(({ id, name }) => {
        const dialog = document.getElementById(id);
        if (dialog) {
            focusTrapManager.register(name, dialog, {
                escapeDeactivates: true,
                initialFocus: 'first',
            });
        }
    });

    // 监听面板打开事件，激活焦点陷阱
    events.on(EventTypes.PANEL_OPENED, (panelName) => {
        if (panelName) {
            focusTrapManager.activate(panelName);
        }
    });

    // 监听面板关闭事件，停用焦点陷阱
    events.on(EventTypes.PANEL_CLOSED, (panelName) => {
        if (panelName) {
            focusTrapManager.deactivate(panelName);
        }
    });
}

/**
 * 设置状态栏更新
 */
export function setupStatusBarUpdates() {
    // 监听设备连接事件
    events.on(EventTypes.DEVICE_CONNECTED, () => {
        updateConnectionStatus(true);
        updateCalibrationStatus('disconnected');
    });

    events.on(EventTypes.DEVICE_DISCONNECTED, () => {
        updateConnectionStatus(false);
        updateAcquisitionStatus(false);
    });

    events.on(EventTypes.DEVICE_CONNECT_FAILED, (error) => {
        updateConnectionStatus(false);
        addLog(`设备连接失败：${error}`, 'error');
    });

    // 监听采集事件
    events.on(EventTypes.ACQUISITION_STARTED, () => {
        updateAcquisitionStatus(true);
    });

    events.on(EventTypes.ACQUISITION_STOPPED, () => {
        updateAcquisitionStatus(false);
    });

    events.on(EventTypes.ACQUISITION_ERROR, (error) => {
        updateAcquisitionStatus(false);
        addLog(`采集错误：${error}`, 'error');
    });
}

/**
 * 清理所有事件监听器
 */
export function cleanupEventHandlers() {
    pageEventCleanup.removeAll();
    focusTrapManager.cleanup();
}

export default {
    initGlobalEventHandlers,
    initFocusTraps,
    setupStatusBarUpdates,
    cleanupEventHandlers,
};
