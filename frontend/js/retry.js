/**
 * 重试逻辑模块
 * @module retry
 *
 * 提供指数退避重试策略
 *
 * @example
 * // 使用指数退避重试
 * const result = await retryWithBackoff(
 *     () => callBackendApi(fn, 'test'),
 *     { maxRetries: 3, baseDelay: 1000 }
 * );
 */

import { addLog } from './utils.js';

/**
 * 默认配置
 */
const DEFAULT_OPTIONS = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    exponential: true,
    onRetry: null,
};

/**
 * 指数退避重试
 * @param {Function} fn - 要执行的异步函数
 * @param {Object} [options] - 配置选项
 * @param {number} [options.maxRetries=3] - 最大重试次数
 * @param {number} [options.baseDelay=1000] - 基础延迟（毫秒）
 * @param {number} [options.maxDelay=10000] - 最大延迟（毫秒）
 * @param {boolean} [options.exponential=true] - 是否使用指数退避
 * @param {Function} [options.onRetry] - 重试回调
 * @returns {Promise<any>} 执行结果
 */
export async function retryWithBackoff(fn, options = {}) {
    const config = { ...DEFAULT_OPTIONS, ...options };
    let lastError;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;

            // 已达最大重试次数
            if (attempt >= config.maxRetries) {
                break;
            }

            // 计算延迟时间
            const delay = config.exponential
                ? Math.min(config.baseDelay * Math.pow(2, attempt), config.maxDelay)
                : config.baseDelay;

            // 添加随机抖动（0-20%）
            const jitter = delay * 0.2 * Math.random();
            const finalDelay = delay + jitter;

            // 调用重试回调
            if (config.onRetry) {
                config.onRetry(error, attempt + 1, config.maxRetries, finalDelay);
            }

            // 等待
            await sleep(finalDelay);
        }
    }

    throw lastError;
}

/**
 * 简单重试（固定延迟）
 * @param {Function} fn - 要执行的异步函数
 * @param {number} maxRetries - 最大重试次数
 * @param {number} delay - 延迟（毫秒）
 * @returns {Promise<any>}
 */
export async function simpleRetry(fn, maxRetries = 3, delay = 1000) {
    return retryWithBackoff(fn, {
        maxRetries,
        baseDelay: delay,
        exponential: false,
    });
}

/**
 * 可配置的重试装饰器
 * @param {Object} options - 配置选项
 * @returns {Function} 装饰器函数
 */
export function withRetry(options = {}) {
    return function (target, propertyKey, descriptor) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args) {
            return retryWithBackoff(async () => originalMethod.apply(this, args), options);
        };

        return descriptor;
    };
}

/**
 * 睡眠函数
 * @param {number} ms - 毫秒数
 * @returns {Promise<void>}
 */
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 创建重试日志回调
 * @param {string} apiName - API 名称
 * @returns {Function} 日志回调
 */
export function createRetryLogger(apiName) {
    return (error, attempt, maxAttempts, delay) => {
        addLog(
            `${apiName} 失败（${error.message}），${attempt}/${maxAttempts} 重试中... (${Math.round(delay)}ms 后)`,
            'warning'
        );
    };
}

export default {
    retryWithBackoff,
    simpleRetry,
    withRetry,
    sleep,
    createRetryLogger,
};
