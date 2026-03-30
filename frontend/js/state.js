/**
 * 拉曼光谱边缘客户端 - 状态管理模块
 * @module state
 * 
 * P11 修复：统一状态管理，解决全局变量分散问题
 */

// ==================== 应用状态 ====================

/**
 * 应用全局状态
 */
const AppState = {
    // 设备状态
    isConnected: false,
    isAcquiring: false,
    
    // 光谱数据
    spectrumData: [],
    wavelengthData: [],
    
    // 校准状态
    calibration: {
        wavelength: {
            calibrated: false,
            correction: 0
        },
        intensity: {
            calibrated: false
        }
    },
    
    // 自动曝光状态
    autoExposure: {
        enabled: false,
        targetIntensity: 0.7
    },
    
    // 采集参数
    parameters: {
        integrationTime: 100,
        accumulationCount: 1,
        smoothingWindow: 0,
        noiseLevel: 0.02
    },
    
    // UI 状态
    ui: {
        showPeakLabels: true,
        showMultiSpectrum: false,
        theme: 'dark'
    },
    
    // 历史光谱（多谱对比）
    historySpectra: []
};

// ==================== 状态监听器 ====================

/**
 * 状态变化监听器列表
 */
const listeners = [];

/**
 * 添加状态变化监听器
 * @param {Function} listener - 监听函数，接收 (state, path) 参数
 */
export function subscribe(listener) {
    listeners.push(listener);
    return () => {
        const index = listeners.indexOf(listener);
        if (index > -1) {
            listeners.splice(index, 1);
        }
    };
}

/**
 * 通知所有监听器状态已变化
 * @param {string} path - 状态变化的路径，如 'calibration.wavelength'
 */
function notifyListeners(path) {
    listeners.forEach(listener => {
        try {
            listener(AppState, path);
        } catch (e) {
            console.error('状态监听器执行失败:', e);
        }
    });
}

// ==================== 状态更新函数 ====================

/**
 * 更新设备连接状态
 * @param {boolean} connected - 是否已连接
 */
export function setConnected(connected) {
    AppState.isConnected = connected;
    if (!connected) {
        AppState.isAcquiring = false;
    }
    notifyListeners('isConnected');
}

/**
 * 更新采集状态
 * @param {boolean} acquiring - 是否正在采集
 */
export function setAcquiring(acquiring) {
    AppState.isAcquiring = acquiring;
    notifyListeners('isAcquiring');
}

/**
 * 更新光谱数据
 * @param {number[]} spectrum - 光谱强度数据
 * @param {number[]} wavelength - 波长数据
 */
export function setSpectrumData(spectrum, wavelength) {
    AppState.spectrumData = spectrum;
    AppState.wavelengthData = wavelength || [];
    notifyListeners('spectrumData');
}

/**
 * 更新波长校准状态
 * @param {boolean} calibrated - 是否已校准
 * @param {number} correction - 校正值
 */
export function setWavelengthCalibration(calibrated, correction = 0) {
    AppState.calibration.wavelength.calibrated = calibrated;
    AppState.calibration.wavelength.correction = correction;
    notifyListeners('calibration.wavelength');
}

/**
 * 更新强度校准状态
 * @param {boolean} calibrated - 是否已校准
 */
export function setIntensityCalibration(calibrated) {
    AppState.calibration.intensity.calibrated = calibrated;
    notifyListeners('calibration.intensity');
}

/**
 * 获取校准状态
 */
export function getCalibrationStatus() {
    return {
        wavelength: AppState.calibration.wavelength,
        intensity: AppState.calibration.intensity
    };
}

/**
 * 更新自动曝光状态
 * @param {boolean} enabled - 是否启用
 * @param {number} targetIntensity - 目标强度
 */
export function setAutoExposure(enabled, targetIntensity = AppState.autoExposure.targetIntensity) {
    AppState.autoExposure.enabled = enabled;
    AppState.autoExposure.targetIntensity = targetIntensity;
    notifyListeners('autoExposure');
}

/**
 * 更新采集参数
 * @param {string} key - 参数名
 * @param {number} value - 参数值
 */
export function setParameter(key, value) {
    if (key in AppState.parameters) {
        AppState.parameters[key] = value;
        notifyListeners(`parameters.${key}`);
    }
}

/**
 * 获取采集参数
 */
export function getParameters() {
    return { ...AppState.parameters };
}

/**
 * 更新 UI 状态
 * @param {string} key - UI 状态名
 * @param {any} value - 状态值
 */
export function setUIState(key, value) {
    if (key in AppState.ui) {
        AppState.ui[key] = value;
        notifyListeners(`ui.${key}`);
    }
}

/**
 * 获取 UI 状态
 */
export function getUIState() {
    return { ...AppState.ui };
}

/**
 * 添加历史光谱
 * @param {Object} spectrum - 光谱对象 {name, data, color}
 */
export function addHistorySpectrum(spectrum) {
    AppState.historySpectra.push(spectrum);
    notifyListeners('historySpectra');
}

/**
 * 清除历史光谱
 */
export function clearHistorySpectra() {
    AppState.historySpectra = [];
    notifyListeners('historySpectra');
}

/**
 * 获取历史光谱
 */
export function getHistorySpectra() {
    return [...AppState.historySpectra];
}

/**
 * 获取完整状态（用于调试）
 */
export function getState() {
    return { ...AppState };
}

/**
 * 根据 key 获取状态值（支持点号分隔）
 * @param {string} key - 状态键，如 'isConnected' 或 'calibration.wavelength'
 */
export function getStateValue(key) {
    const keys = key.split('.');
    let value = AppState;
    for (const k of keys) {
        value = value?.[k];
    }
    return value;
}

/**
 * 根据 key 设置状态值（支持点号分隔）并触发通知
 * @param {string} key - 状态键，如 'isConnected' 或 'calibration.wavelength.calibrated'
 * @param {any} value - 状态值
 */
export function setStateValue(key, value) {
    const keys = key.split('.');
    let target = AppState;
    for (let i = 0; i < keys.length - 1; i++) {
        target = target[keys[i]];
    }
    const lastKey = keys[keys.length - 1];
    target[lastKey] = value;
    notifyListeners(key);
}

// ==================== 导出到全局（用于调试） ====================

if (typeof window !== 'undefined') {
    window.appState = AppState;
    window.getState = getState;
}

// ==================== 便捷导出（别名） ====================

// 导出 setState 和 getState 作为 setStateValue 和 getStateValue 的别名
export const setState = setStateValue;
export const getState = getStateValue;
