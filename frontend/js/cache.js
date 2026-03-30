/**
 * 拉曼光谱边缘客户端 - API 请求缓存模块（SWR 模式）
 * @module cache
 * 
 * P11 改进：实现 SWR（Stale-While-Revalidate）缓存策略
 * - 优先返回缓存数据（stale）
 * - 后台重新验证（revalidate）
 * - 自动更新最新数据（fresh）
 * 
 * 适用于：校准状态、设备参数等不频繁变化但需要快速响应的数据
 */

import { addLog } from './utils.js';

/**
 * 缓存项结构
 * @typedef {Object} CacheItem
 * @property {*} data - 缓存的数据
 * @property {number} timestamp - 缓存时间戳
 * @property {number} ttl - 生存时间（毫秒）
 * @property {Promise|null} revalidatePromise - 正在进行的重新验证 Promise
 */

/**
 * 缓存存储
 * @type {Map<string, CacheItem>}
 */
const cacheStore = new Map();

/**
 * 默认 TTL 配置（毫秒）
 */
const DEFAULT_TTL = {
    short: 5000,      // 5 秒 - 频繁变化的数据
    medium: 30000,    // 30 秒 - 一般数据
    long: 300000,     // 5 分钟 - 不常变化的数据（如校准状态）
    forever: 0        // 永不过期
};

/**
 * 生成缓存键
 * @param {string} key - 基础键名
 * @param {Object} params - 参数对象
 * @returns {string} 缓存键
 */
export function generateCacheKey(key, params = {}) {
    if (Object.keys(params).length === 0) {
        return key;
    }
    const sortedParams = Object.keys(params).sort().map(k => `${k}=${params[k]}`);
    return `${key}:${sortedParams.join('&')}`;
}

/**
 * 检查缓存是否过期
 * @param {CacheItem} item - 缓存项
 * @returns {boolean} 是否过期
 */
function isExpired(item) {
    if (item.ttl === DEFAULT_TTL.forever) {
        return false;
    }
    return Date.now() - item.timestamp > item.ttl;
}

/**
 * 检查缓存是否可用（未过期或在宽限期内）
 * @param {CacheItem} item - 缓存项
 * @param {number} gracePeriod - 宽限期（毫秒），过期后仍可返回旧数据的时间
 * @returns {boolean} 是否可用
 */
function isCacheAvailable(item, gracePeriod = 5000) {
    if (!item) return false;
    const age = Date.now() - item.timestamp;
    return age < item.ttl + gracePeriod;
}

/**
 * 从缓存获取数据（SWR 模式）
 * 
 * P11 修复：
 * 1. forceRefresh 应该完全跳过缓存
 * 2. 缓存完全过期时应等待刷新，返回 stale=false
 * 
 * @param {string} key - 缓存键
 * @param {Function} fetcher - 获取数据的函数（返回 Promise）
 * @param {Object} options - 选项
 * @param {number} options.ttl - 生存时间（毫秒）
 * @param {number} options.gracePeriod - 宽限期（毫秒）
 * @param {boolean} options.forceRefresh - 是否强制刷新
 * @returns {Promise<{data: *, stale: boolean}>} 数据和是否来自缓存
 * 
 * @example
 * // 获取校准状态，缓存 5 分钟
 * const { data, stale } = await swr('calibration:status', getCalibrationStatus, { ttl: 300000 });
 * if (stale) {
 *     console.log('返回的是旧数据，后台正在刷新...');
 * }
 */
export async function swr(key, fetcher, options = {}) {
    const {
        ttl = DEFAULT_TTL.medium,
        gracePeriod = 5000,
        forceRefresh = false
    } = options;

    const cachedItem = cacheStore.get(key);

    // P11 修复：forceRefresh 完全跳过缓存
    if (forceRefresh) {
        try {
            const data = await fetcher();
            cacheStore.set(key, {
                data,
                timestamp: Date.now(),
                ttl,
                revalidatePromise: null
            });
            addLog(`[SWR] 强制刷新：${key}`, 'info');
            return { data, stale: false };
        } catch (error) {
            addLog(`[SWR] 强制刷新失败：${key} - ${error.message}`, 'error');
            throw error;
        }
    }

    // 无缓存，获取数据
    if (!cachedItem) {
        try {
            const data = await fetcher();
            cacheStore.set(key, {
                data,
                timestamp: Date.now(),
                ttl,
                revalidatePromise: null
            });
            addLog(`[SWR] 缓存已更新：${key}`, 'info');
            return { data, stale: false };
        } catch (error) {
            addLog(`[SWR] 获取数据失败：${key} - ${error.message}`, 'error');
            throw error;
        }
    }

    // 缓存未过期，返回新鲜数据
    if (!isExpired(cachedItem)) {
        addLog(`[SWR] 命中缓存（新鲜）：${key}`, 'info');
        return { data: cachedItem.data, stale: false };
    }

    // P11 修复：缓存已过期但在宽限期内，返回旧数据并后台刷新
    if (isCacheAvailable(cachedItem, gracePeriod)) {
        // 如果没有正在进行的重新验证，启动后台刷新
        if (!cachedItem.revalidatePromise) {
            cachedItem.revalidatePromise = fetcher()
                .then(data => {
                    cacheStore.set(key, {
                        data,
                        timestamp: Date.now(),
                        ttl,
                        revalidatePromise: null
                    });
                    addLog(`[SWR] 后台刷新成功：${key}`, 'info');
                })
                .catch(error => {
                    addLog(`[SWR] 后台刷新失败：${key} - ${error.message}`, 'warning');
                    cachedItem.revalidatePromise = null;
                });
        }

        addLog(`[SWR] 命中缓存（过期，宽限期内）：${key}`, 'info');
        return { data: cachedItem.data, stale: true };
    }

    // P11 修复：缓存完全过期，等待刷新后返回新数据
    try {
        const data = await fetcher();
        cacheStore.set(key, {
            data,
            timestamp: Date.now(),
            ttl,
            revalidatePromise: null
        });
        addLog(`[SWR] 缓存已刷新：${key}`, 'info');
        return { data, stale: false };  // ✅ 返回 stale=false
    } catch (error) {
        // 如果刷新失败但有旧数据，返回旧数据（降级）
        if (cachedItem.data !== undefined) {
            addLog(`[SWR] 刷新失败，返回旧数据：${key}`, 'warning');
            return { data: cachedItem.data, stale: true };
        }
        throw error;
    }
}

/**
 * 获取缓存数据（不刷新）
 * @param {string} key - 缓存键
 * @param {number} maxAge - 最大年龄（毫秒），超过此值认为缓存无效
 * @returns {*|null} 缓存数据，不存在或过期返回 null
 */
export function getCache(key, maxAge = DEFAULT_TTL.medium) {
    const item = cacheStore.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > maxAge) {
        return null;
    }
    
    return item.data;
}

/**
 * 设置缓存
 * @param {string} key - 缓存键
 * @param {*} data - 数据
 * @param {number} ttl - 生存时间（毫秒）
 */
export function setCache(key, data, ttl = DEFAULT_TTL.medium) {
    cacheStore.set(key, {
        data,
        timestamp: Date.now(),
        ttl,
        revalidatePromise: null
    });
    addLog(`[SWR] 缓存已设置：${key}`, 'info');
}

/**
 * 删除缓存
 * @param {string} key - 缓存键
 * @returns {boolean} 是否删除成功
 */
export function deleteCache(key) {
    return cacheStore.delete(key);
}

/**
 * 清除所有缓存
 */
export function clearCache() {
    cacheStore.clear();
    addLog('[SWR] 缓存已清空', 'info');
}

/**
 * 清除过期缓存
 * @returns {number} 清除的缓存数量
 */
export function cleanupExpiredCache() {
    let count = 0;
    for (const [key, item] of cacheStore.entries()) {
        if (isExpired(item)) {
            cacheStore.delete(key);
            count++;
        }
    }
    if (count > 0) {
        addLog(`[SWR] 清理了 ${count} 个过期缓存`, 'info');
    }
    return count;
}

/**
 * 获取缓存统计信息
 * @returns {{total: number, expired: number, fresh: number}}
 */
export function getCacheStats() {
    const now = Date.now();
    let expired = 0;
    let fresh = 0;

    for (const item of cacheStore.values()) {
        if (isExpired(item)) {
            expired++;
        } else {
            fresh++;
        }
    }

    return {
        total: cacheStore.size,
        expired,
        fresh
    };
}

/**
 * 预取数据（放入缓存但不返回）
 * @param {string} key - 缓存键
 * @param {Function} fetcher - 获取数据的函数
 * @param {number} ttl - 生存时间（毫秒）
 * @returns {Promise<void>}
 */
export async function prefetch(key, fetcher, ttl = DEFAULT_TTL.medium) {
    if (cacheStore.has(key) && !isExpired(cacheStore.get(key))) {
        return; // 已有有效缓存，不重复获取
    }

    try {
        const data = await fetcher();
        setCache(key, data, ttl);
    } catch (error) {
        addLog(`[SWR] 预取失败：${key} - ${error.message}`, 'warning');
    }
}

/**
 * SWR 配置对象
 */
export const SWRConfig = {
    /**
     * 校准状态缓存配置
     */
    calibrationStatus: {
        key: 'calibration:status',
        ttl: DEFAULT_TTL.long,  // 5 分钟
        gracePeriod: 10000       // 10 秒宽限期
    },

    /**
     * 设备参数缓存配置
     */
    deviceParams: {
        key: 'device:params',
        ttl: DEFAULT_TTL.short,  // 5 秒
        gracePeriod: 2000        // 2 秒宽限期
    },

    /**
     * 波长数据缓存配置
     */
    wavelengths: {
        key: 'device:wavelengths',
        ttl: DEFAULT_TTL.long,   // 5 分钟（波长通常不变）
        gracePeriod: 10000
    }
};

// 定时清理过期缓存（每 1 分钟）
// P11 修复：在测试环境中禁用
if (typeof window !== 'undefined' && process?.env?.NODE_ENV !== 'test') {
    setInterval(() => {
        cleanupExpiredCache();
    }, 60000);
}
