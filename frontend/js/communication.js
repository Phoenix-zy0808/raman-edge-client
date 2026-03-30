/**
 * QWebChannel 通信模块
 * @module communication
 *
 * 负责 QWebChannel 连接和通信，不包含重试、缓存等逻辑
 */

import { addLog } from './utils.js';

/** @type {any} QWebChannel 代理对象 */
let pythonBackend = null;

/**
 * QWebChannel 连接回调
 * @type {Function|null}
 */
let onConnectedCallback = null;

/**
 * 是否已连接
 * @type {boolean}
 */
let isConnected = false;

/**
 * 初始化 QWebChannel 连接
 * @param {Function} onReady - 连接成功回调
 */
export function initChannel(onReady) {
    onConnectedCallback = onReady;

    // 检查是否在 Qt 环境中
    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
        addLog('检测到 Qt 环境，初始化 QWebChannel...');
        initQtChannel();
    } else {
        // 浏览器环境，使用模拟后端
        addLog('浏览器环境，使用模拟后端', 'warning');
        initMockBackend();
    }
}

/**
 * 初始化 Qt QWebChannel
 */
function initQtChannel() {
    // 动态导入 QWebChannel
    const loadQWebChannel = () => {
        if (typeof QWebChannel === 'undefined') {
            addLog('QWebChannel 未定义，尝试从 qrc 加载...', 'warning');
            // 在 HTML 中应该已经引入了 qrc:///qtwebchannel/qwebchannel.js
            setTimeout(loadQWebChannel, 100);
            return;
        }

        new QWebChannel(qt.webChannelTransport, (channel) => {
            pythonBackend = channel.objects.pythonBackend;

            if (!pythonBackend) {
                addLog('无法获取 pythonBackend 对象', 'error');
                return;
            }

            isConnected = true;
            addLog('QWebChannel 连接成功');

            if (onConnectedCallback) {
                onConnectedCallback(pythonBackend);
            }
        });
    };

    loadQWebChannel();
}

/**
 * 初始化模拟后端（用于浏览器开发）
 */
function initMockBackend() {
    pythonBackend = createMockBackend();
    isConnected = true;

    if (onConnectedCallback) {
        onConnectedCallback(pythonBackend);
    }
}

/**
 * 创建模拟后端对象
 * @returns {Object} 模拟后端
 */
function createMockBackend() {
    const mockSignals = {};

    return {
        // 模拟方法
        connect: (callback) => callback(true),
        disconnect: () => {},
        startAcquisition: (callback) => callback(true),
        stopAcquisition: () => {},
        setIntegrationTime: (time, callback) => callback(true),
        setAccumulationCount: (count, callback) => callback(true),
        setSmoothingWindow: (window, callback) => callback(true),
        setNoiseLevel: (level, callback) => callback(true),
        getIntegrationTime: (callback) => callback(100),
        getAccumulationCount: (callback) => callback(1),
        getSmoothingWindow: (callback) => callback(5),
        getNoiseLevel: (callback) => callback(0.02),
        getStatus: (callback) => callback(JSON.stringify({
            connected: true,
            acquiring: false,
            integration_time: 100,
        })),
        calibrateWavelength: (callback) => callback(JSON.stringify({
            success: true,
            data: { correction: 0.5 },
        })),
        calibrateIntensity: (callback) => callback(JSON.stringify({
            success: true,
            data: { curve: [] },
        })),
        autoExposure: (callback) => callback(JSON.stringify({
            success: true,
            data: { final_integration_time: 500 },
        })),

        // 模拟信号
        connected: { connect: (fn) => registerSignal(mockSignals, 'connected', fn) },
        connectFailed: { connect: (fn) => registerSignal(mockSignals, 'connectFailed', fn) },
        disconnected: { connect: (fn) => registerSignal(mockSignals, 'disconnected', fn) },
        acquisitionStarted: { connect: (fn) => registerSignal(mockSignals, 'acquisitionStarted', fn) },
        acquisitionStopped: { connect: (fn) => registerSignal(mockSignals, 'acquisitionStopped', fn) },
        spectrumReady: { connect: (fn) => registerSignal(mockSignals, 'spectrumReady', fn) },
        errorOccurred: { connect: (fn) => registerSignal(mockSignals, 'errorOccurred', fn) },
    };
}

/**
 * 注册模拟信号
 */
function registerSignal(signals, name, fn) {
    if (!signals[name]) {
        signals[name] = [];
    }
    signals[name].push(fn);
}

/**
 * 获取后端对象
 * @returns {any} 后端对象
 */
export function getBackend() {
    return pythonBackend;
}

/**
 * 检查后端是否可用
 * @returns {boolean}
 */
export function isBackendAvailable() {
    return pythonBackend !== null && isConnected;
}

/**
 * 检查是否在 Qt 环境中
 * @returns {boolean}
 */
export function isQtEnvironment() {
    return typeof qt !== 'undefined' && qt.webChannelTransport;
}

export default {
    initChannel,
    getBackend,
    isBackendAvailable,
    isQtEnvironment,
};
