/**
 * 拉曼光谱边缘客户端 - QWebChannel 通信桥接模块
 * @module bridge
 *
 * P12 重构：拆分为 communication.js、retry.js、circuit-breaker.js、api.js
 * 此文件作为兼容层，保留原有导出接口
 */

// 重新导出所有新模块
export { initChannel, getBackend, isBackendAvailable, isQtEnvironment } from './communication.js';
export { api, BackendApi } from './api.js';
export { backendBreaker, channelBreaker, CircuitBreaker, CircuitState } from './circuit-breaker.js';
export { retryWithBackoff, simpleRetry, createRetryLogger, sleep } from './retry.js';
export { swr, setCache, getCache, deleteCache, SWRConfig } from './cache.js';

// 重新导出类型工具
export { parseApiResponse, isResponseSuccess, isRetryableError, ErrorCode, getErrorDescription } from './types.js';

// 重新导出工具函数
export { addLog, showToast } from './utils.js';

// 重新导出状态管理
export { setState, getState } from './state.js';

// 重新导出事件总线
export { events, EventEmitter, EventTypes, createEventManager } from './event-bus.js';

/**
 * 初始化桥接（兼容旧接口）
 * @param {Function} onReady - 桥接就绪回调
 * @deprecated 已迁移至 communication.js
 */
export function initBridge(onReady) {
    // 静默迁移，不产生警告
    initChannel(onReady);
}

/**
 * 获取后端实例（兼容旧接口）
 * @returns {any} 后端对象
 * @deprecated 已迁移至 communication.js
 */
export function getBackendInstance() {
    // 静默迁移，不产生警告
    return getBackend();
}

/**
 * 检查后端是否可用（兼容旧接口）
 * @returns {boolean}
 * @deprecated 已迁移至 communication.js
 */
export function checkBackendAvailable() {
    // 静默迁移，不产生警告
    return isBackendAvailable();
}

// ==================== 校准功能（快捷方法） ====================

/**
 * 波长校准（快捷方法）
 * @returns {Promise<Object>}
 */
export async function calibrateWavelength() {
    return api.calibrateWavelength();
}

/**
 * 强度校准（快捷方法）
 * @returns {Promise<Object>}
 */
export async function calibrateIntensity() {
    return api.calibrateIntensity();
}

/**
 * 自动曝光（快捷方法）
 * @returns {Promise<Object>}
 */
export async function autoExposure() {
    return api.autoExposure();
}

/**
 * 设置自动曝光启用状态（快捷方法）
 * @param {boolean} enabled - 是否启用
 * @returns {Promise<void>}
 */
export async function setAutoExposureEnabled(enabled) {
    return api.setAutoExposureEnabled(enabled);
}

// ==================== 默认导出 ====================

export default {
    initChannel,
    initBridge,
    getBackend,
    getBackendInstance,
    isBackendAvailable,
    checkBackendAvailable,
    api,
    calibrateWavelength,
    calibrateIntensity,
    autoExposure,
    setAutoExposureEnabled,
    // 重新导出
    CircuitBreaker,
    CircuitState,
    backendBreaker,
    channelBreaker,
    events,
    EventTypes,
};
