/**
 * QWebChannel Bridge 辅助模块
 * 
 * 提供统一的后端 API 调用封装，确保错误处理和参数验证的一致性
 * 
 * 使用方法:
 * import { bridge, callBackend } from './bridge_helper.js';
 * 
 * // 方式 1: 使用封装的方法
 * const result = await bridge.startLiveMode({ value: 5.0 });
 * 
 * // 方式 2: 使用通用调用
 * const result = await callBackend('findPeaks', spectrumJson, paramsJson);
 */

// ========== 全局状态 ==========
let pythonBackend = null;
let bridgeReady = false;
let bridgeInitPromise = null;

/**
 * 初始化 Bridge 连接
 * @returns {Promise<boolean>} 是否成功连接
 */
export function initBridge() {
    if (bridgeInitPromise) {
        return bridgeInitPromise;
    }

    bridgeInitPromise = new Promise((resolve, reject) => {
        // 检查 QWebChannel 是否可用
        if (typeof QWebChannel === 'undefined') {
            console.error('[Bridge] QWebChannel 未定义');
            resolve(false);
            return;
        }

        // 建立连接
        new QWebChannel(qt.webChannelTransport, (channel) => {
            try {
                pythonBackend = channel.objects.BridgeObject;
                bridgeReady = true;
                console.log('[Bridge] 连接成功');
                resolve(true);
            } catch (error) {
                console.error('[Bridge] 初始化失败:', error);
                bridgeReady = false;
                resolve(false);
            }
        });

        // 超时处理
        setTimeout(() => {
            if (!bridgeReady) {
                console.error('[Bridge] 连接超时');
                resolve(false);
            }
        }, 5000);
    });

    return bridgeInitPromise;
}

/**
 * 检查 Bridge 是否就绪
 * @returns {boolean}
 */
export function isBridgeReady() {
    return bridgeReady && pythonBackend !== null;
}

/**
 * 获取后端对象
 * @returns {object|null}
 */
export function getBackend() {
    return pythonBackend;
}

/**
 * 通用后端调用方法 - Promise 封装
 * 
 * @param {string} methodName - 要调用的后端方法名
 * @param  {...any} args - 方法参数
 * @returns {Promise<any>} 调用结果
 */
export async function callBackend(methodName, ...args) {
    return new Promise((resolve, reject) => {
        // 检查 Bridge 状态
        if (!bridgeReady || !pythonBackend) {
            reject(new Error('后端未连接，请检查 Bridge 初始化'));
            return;
        }

        // 检查方法是否存在
        if (typeof pythonBackend[methodName] !== 'function') {
            reject(new Error(`后端方法不存在：${methodName}`));
            return;
        }

        try {
            // 调用后端方法
            const result = pythonBackend[methodName](...args);
            
            // 尝试解析 JSON 结果
            try {
                const parsed = typeof result === 'string' ? JSON.parse(result) : result;
                resolve(parsed);
            } catch (e) {
                // 如果不是 JSON，直接返回原始结果
                resolve(result);
            }
        } catch (error) {
            reject(new Error(`调用 ${methodName} 失败：${error.message}`));
        }
    });
}

/**
 * 带回调的后端调用 (兼容旧代码)
 * 
 * @param {string} methodName - 要调用的后端方法名
 * @param {any[]} args - 方法参数数组
 * @param {function} callback - 回调函数
 */
export function callBackendWithCallback(methodName, args, callback) {
    if (!bridgeReady || !pythonBackend) {
        callback({ success: false, error: '后端未连接' });
        return;
    }

    if (typeof pythonBackend[methodName] !== 'function') {
        callback({ success: false, error: `方法不存在：${methodName}` });
        return;
    }

    try {
        const result = pythonBackend[methodName](...args);
        try {
            const parsed = typeof result === 'string' ? JSON.parse(result) : result;
            callback(parsed);
        } catch (e) {
            callback({ success: true, data: result });
        }
    } catch (error) {
        callback({ success: false, error: error.message });
    }
}

// ========== P0-1 实时采集 API ==========

/**
 * 启动实时采集模式
 * @param {number} refreshRate - 刷新率 (Hz)
 * @returns {Promise<object>} 启动结果
 */
export async function startLiveMode(refreshRate) {
    return callBackend('startLiveMode', JSON.stringify({ value: refreshRate }));
}

/**
 * 暂停/继续实时采集
 * @param {boolean} paused - 是否暂停
 * @returns {Promise<object>} 操作结果
 */
export async function pauseLiveMode(paused) {
    return callBackend('pauseLiveMode', JSON.stringify({ paused }));
}

/**
 * 停止实时采集
 * @returns {Promise<object>} 停止结果
 */
export async function stopLiveMode() {
    return callBackend('stopLiveMode');
}

/**
 * 设置刷新率
 * @param {number} refreshRate - 刷新率 (Hz)
 * @returns {Promise<object>} 设置结果
 */
export async function setRefreshRate(refreshRate) {
    return callBackend('setRefreshRate', JSON.stringify({ value: refreshRate }));
}

// ========== P0-2 峰值识别 API ==========

/**
 * 自动寻峰
 * @param {number[]|Float32Array} spectrum - 光谱数据
 * @param {object} params - 寻峰参数
 * @param {number} params.sensitivity - 灵敏度 (0-1)
 * @param {number} params.minSnr - 最小信噪比
 * @param {number} params.minDistance - 最小峰间距
 * @returns {Promise<object>} 寻峰结果
 */
export async function findPeaks(spectrum, params = {}) {
    const spectrumJson = JSON.stringify(Array.from(spectrum));
    const paramsJson = JSON.stringify({
        sensitivity: params.sensitivity || 0.5,
        minSnr: params.minSnr || 3.0,
        minDistance: params.minDistance || 5
    });
    return callBackend('findPeaks', spectrumJson, paramsJson);
}

/**
 * 峰值拟合
 * @param {number[]|Float32Array} spectrum - 光谱数据
 * @param {object} position - 峰值位置 {index, wavelength}
 * @param {string} fitType - 拟合类型 'gaussian' | 'lorentzian' | 'voigt'
 * @returns {Promise<object>} 拟合结果
 */
export async function fitPeak(spectrum, position, fitType = 'gaussian') {
    const spectrumJson = JSON.stringify(Array.from(spectrum));
    const positionJson = JSON.stringify(position);
    const fitTypeJson = JSON.stringify({ type: fitType });
    return callBackend('fitPeak', spectrumJson, positionJson, fitTypeJson);
}

// ========== P0-3 预处理 API ==========

/**
 * 谱图预处理
 * @param {number[]|Float32Array} spectrum - 光谱数据
 * @param {array} tools - 预处理工具列表
 * @returns {Promise<object>} 处理结果
 */
export async function preprocess(spectrum, tools = []) {
    const spectrumJson = JSON.stringify(Array.from(spectrum));
    const paramsJson = JSON.stringify({ tools });
    return callBackend('preprocess', spectrumJson, paramsJson);
}

// ========== P0-4 差谱运算 API ==========

/**
 * 差谱运算
 * @param {number[]|Float32Array} spectrum1 - 参考光谱
 * @param {number[]|Float32Array} spectrum2 - 待减光谱
 * @param {number} coefficient - 减数系数
 * @returns {Promise<object>} 差谱结果
 */
export async function subtractSpectra(spectrum1, spectrum2, coefficient = 1.0) {
    const spectrum1Json = JSON.stringify(Array.from(spectrum1));
    const spectrum2Json = JSON.stringify(Array.from(spectrum2));
    const coefficientJson = JSON.stringify({ value: coefficient });
    return callBackend('subtractSpectra', spectrum1Json, spectrum2Json, coefficientJson);
}

// ========== 工具方法 ==========

/**
 * 获取 Bridge 状态
 * @returns {Promise<object>} 状态信息
 */
export async function getBridgeStatus() {
    return callBackend('getBridgeStatus');
}

/**
 * 等待 Bridge 就绪
 * @param {number} timeout - 超时时间 (ms)
 * @returns {Promise<boolean>}
 */
export async function waitForBridge(timeout = 5000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
        if (bridgeReady && pythonBackend) {
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    return false;
}

// ========== 事件监听封装 ==========

/**
 * 监听实时光谱更新
 * @param {function} callback - 回调函数 (spectrum, frameCount)
 */
export function onLiveSpectrumUpdated(callback) {
    if (!pythonBackend) return;
    
    pythonBackend.liveSpectrumUpdated.connect((dataJson) => {
        const data = JSON.parse(dataJson);
        callback(data.spectrum, data.frame_count);
    });
}

/**
 * 监听峰值检测结果
 * @param {function} callback - 回调函数 (result)
 */
export function onPeaksDetected(callback) {
    if (!pythonBackend) return;
    
    pythonBackend.peaksDetected.connect((dataJson) => {
        const data = JSON.parse(dataJson);
        callback(data);
    });
}

/**
 * 监听峰值拟合结果
 * @param {function} callback - 回调函数 (result)
 */
export function onPeakFitted(callback) {
    if (!pythonBackend) return;
    
    pythonBackend.peakFitted.connect((dataJson) => {
        const data = JSON.parse(dataJson);
        callback(data);
    });
}

/**
 * 监听谱图处理结果
 * @param {function} callback - 回调函数 (result)
 */
export function onSpectrumProcessed(callback) {
    if (!pythonBackend) return;
    
    pythonBackend.spectrumProcessed.connect((dataJson) => {
        const data = JSON.parse(dataJson);
        callback(data);
    });
}

/**
 * 监听差谱计算结果
 * @param {function} callback - 回调函数 (result)
 */
export function onDifferenceCalculated(callback) {
    if (!pythonBackend) return;

    pythonBackend.differenceCalculated.connect((dataJson) => {
        const data = JSON.parse(dataJson);
        callback(data);
    });
}

// ========== 按功能分组导出 ==========

/**
 * 核心桥接 API
 */
export const bridgeCore = {
    initBridge,
    isBridgeReady,
    getBackend,
    callBackend,
    callBackendWithCallback,
    getBridgeStatus,
    waitForBridge
};

/**
 * P0-1 实时采集 API
 */
export const liveAcquisition = {
    startLiveMode,
    pauseLiveMode,
    stopLiveMode,
    setRefreshRate,
    onLiveSpectrumUpdated
};

/**
 * P0-2 峰值分析 API
 */
export const peakAnalysis = {
    findPeaks,
    fitPeak,
    onPeaksDetected,
    onPeakFitted
};

/**
 * P0-3 预处理 API
 */
export const preprocessing = {
    preprocess,
    onSpectrumProcessed
};

/**
 * P0-4 差谱运算 API
 */
export const difference = {
    subtractSpectra,
    onDifferenceCalculated
};

/**
 * 便捷导出（向后兼容）
 * 推荐在新代码中使用分组导出
 */
export {
    initBridge,
    isBridgeReady,
    getBackend,
    callBackend,
    startLiveMode,
    pauseLiveMode,
    stopLiveMode,
    setRefreshRate,
    findPeaks,
    fitPeak,
    preprocess,
    subtractSpectra,
    onLiveSpectrumUpdated,
    onPeaksDetected,
    onPeakFitted,
    onSpectrumProcessed,
    onDifferenceCalculated,
    pythonBackend,
    bridgeReady
};

// ========== 统一默认导出 ==========
/**
 * 默认导出 - 包含所有 API
 * 使用方式：import bridge from './bridge_helper.js'
 */
const bridge = {
    // 核心
    ...bridgeCore,
    // P0 功能
    ...liveAcquisition,
    ...peakAnalysis,
    ...preprocessing,
    ...difference
};

export default bridge;

// ========== 安全地挂载到 window ==========
/**
 * 确保 DOM 加载完成后再挂载到 window
 * 防止 onclick 在模块加载前访问 window.bridge
 */
function mountToWindow() {
    if (typeof window !== 'undefined') {
        window.bridge = bridge;
        console.log('[Bridge] 已挂载到 window.bridge');
    }
}

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountToWindow);
    } else {
        mountToWindow();
    }
} else {
    mountToWindow();
}
