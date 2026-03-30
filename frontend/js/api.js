/**
 * API 封装模块
 * @module api
 *
 * 封装所有后端 API 调用，统一使用 CircuitBreaker 和 Retry 机制
 *
 * @example
 * // 调用后端 API
 * const result = await api.connect();
 *
 * // 获取校准状态（带缓存）
 * const status = await api.getCalibrationStatus();
 */

import { getBackend, isBackendAvailable } from './communication.js';
import { backendBreaker } from './circuit-breaker.js';
import { retryWithBackoff, createRetryLogger } from './retry.js';
import { swr, SWRConfig } from './cache.js';
import { parseApiResponse, isResponseSuccess } from './types.js';
import { addLog } from './utils.js';

/**
 * API 调用配置
 */
const API_CONFIG = {
    retry: {
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 5000,
    },
    timeout: {
        normal: 5000,
        calibration: 30000,
    },
};

/**
 * 解析 API 响应
 * @param {any} result - 后端返回结果
 * @param {string} apiName - API 名称
 * @returns {Object} 解析后的响应
 */
function parseResponse(result, apiName) {
    try {
        const response = parseApiResponse(result);

        if (!isResponseSuccess(response)) {
            const errorMsg = response.message || `${apiName} 失败`;
            throw new Error(errorMsg);
        }

        return response;
    } catch (e) {
        throw new Error(`${apiName} 响应解析失败：${e.message}`);
    }
}

/**
 * 调用后端 API，带熔断和重试保护
 * @param {Function} callFn - 调用函数
 * @param {string} apiName - API 名称
 * @returns {Promise<Object>}
 */
async function callBackendApi(callFn, apiName) {
    return backendBreaker.execute(
        () => retryWithBackoff(
            () => new Promise((resolve, reject) => {
                try {
                    callFn((result) => {
                        try {
                            const response = parseResponse(result, apiName);
                            resolve(response);
                        } catch (e) {
                            reject(e);
                        }
                    });
                } catch (e) {
                    reject(e);
                }
            }),
            {
                ...API_CONFIG.retry,
                onRetry: createRetryLogger(apiName),
            }
        ),
        { recordStats: true }
    );
}

/**
 * API 封装类
 */
export class BackendApi {
    constructor() {
        this._initialized = false;
    }

    /**
     * 初始化 API
     */
    init() {
        this._initialized = isBackendAvailable();
    }

    /**
     * 检查是否已初始化
     * @returns {boolean}
     */
    isInitialized() {
        return this._initialized;
    }

    // ==================== 设备控制 ====================

    /**
     * 连接设备
     * @returns {Promise<Object>}
     */
    async connect() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.connect(callback),
            'connect'
        );
    }

    /**
     * 断开设备
     * @returns {Promise<void>}
     */
    async disconnect() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            () => backend.disconnect(),
            'disconnect'
        );
    }

    /**
     * 开始采集
     * @returns {Promise<Object>}
     */
    async startAcquisition() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.startAcquisition(callback),
            'startAcquisition'
        );
    }

    /**
     * 停止采集
     * @returns {Promise<void>}
     */
    async stopAcquisition() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            () => backend.stopAcquisition(),
            'stopAcquisition'
        );
    }

    // ==================== 参数设置 ====================

    /**
     * 设置积分时间
     * @param {number} time - 积分时间（ms）
     * @returns {Promise<Object>}
     */
    async setIntegrationTime(time) {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.setIntegrationTime(time, callback),
            'setIntegrationTime'
        );
    }

    /**
     * 设置累加次数
     * @param {number} count - 累加次数
     * @returns {Promise<Object>}
     */
    async setAccumulationCount(count) {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.setAccumulationCount(count, callback),
            'setAccumulationCount'
        );
    }

    /**
     * 设置平滑窗口
     * @param {number} window - 平滑窗口
     * @returns {Promise<Object>}
     */
    async setSmoothingWindow(window) {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.setSmoothingWindow(window, callback),
            'setSmoothingWindow'
        );
    }

    /**
     * 设置噪声水平
     * @param {number} level - 噪声水平
     * @returns {Promise<Object>}
     */
    async setNoiseLevel(level) {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.setNoiseLevel(level, callback),
            'setNoiseLevel'
        );
    }

    // ==================== 状态获取 ====================

    /**
     * 获取设备状态
     * @returns {Promise<Object>}
     */
    async getStatus() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.getStatus(callback),
            'getStatus'
        );
    }

    /**
     * 获取积分时间
     * @returns {Promise<number>}
     */
    async getIntegrationTime() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.getIntegrationTime(callback),
            'getIntegrationTime'
        );
    }

    /**
     * 获取累加次数
     * @returns {Promise<number>}
     */
    async getAccumulationCount() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.getAccumulationCount(callback),
            'getAccumulationCount'
        );
    }

    // ==================== 校准功能 ====================

    /**
     * 波长校准
     * @returns {Promise<Object>}
     */
    async calibrateWavelength() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.calibrateWavelength(callback),
            'calibrateWavelength'
        );
    }

    /**
     * 强度校准
     * @returns {Promise<Object>}
     */
    async calibrateIntensity() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.calibrateIntensity(callback),
            'calibrateIntensity'
        );
    }

    /**
     * 自动曝光
     * @returns {Promise<Object>}
     */
    async autoExposure() {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            (callback) => backend.autoExposure(callback),
            'autoExposure'
        );
    }

    /**
     * 设置自动曝光启用状态
     * @param {boolean} enabled - 是否启用
     * @returns {Promise<void>}
     */
    async setAutoExposureEnabled(enabled) {
        const backend = getBackend();
        if (!backend) {
            throw new Error('后端未连接');
        }

        return callBackendApi(
            () => backend.setAutoExposureEnabled(enabled),
            'setAutoExposureEnabled'
        );
    }

    // ==================== 缓存方法（使用 SWR） ====================

    /**
     * 获取校准状态（带缓存）
     * @returns {Promise<Object>}
     */
    async getCalibrationStatus() {
        const config = SWRConfig.calibrationStatus;

        return swr(
            config.key,
            async () => {
                const backend = getBackend();
                if (!backend) {
                    throw new Error('后端未连接');
                }

                return callBackendApi(
                    (callback) => backend.getCalibrationStatus(callback),
                    'getCalibrationStatus'
                );
            },
            { ttl: config.ttl, gracePeriod: config.gracePeriod }
        );
    }

    /**
     * 获取波长数据（带缓存）
     * @returns {Promise<number[]>}
     */
    async getWavelengths() {
        const config = SWRConfig.wavelengths;

        return swr(
            config.key,
            async () => {
                const backend = getBackend();
                if (!backend) {
                    throw new Error('后端未连接');
                }

                return new Promise((resolve, reject) => {
                    backend.getWavelengths((data) => {
                        try {
                            resolve(JSON.parse(data));
                        } catch (e) {
                            reject(e);
                        }
                    });
                });
            },
            { ttl: config.ttl }
        );
    }
}

/**
 * 创建 API 实例
 */
export const api = new BackendApi();

export default api;
