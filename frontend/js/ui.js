/**
 * 拉曼光谱边缘客户端 - UI 控制模块
 * @module ui
 * 
 * P11 改进：使用防抖/节流优化性能，统一事件监听器管理
 */

import { addLog, showToast, validateIntegrationTime, validateNoiseLevel,
         validateAccumulationCount, validateSmoothingWindow,
         debounce, throttle, createEventCleanup, createTimerManager } from './utils.js';
import { getChart, updateSpectrum, addToHistory, clearHistory, toggleMultiSpectrum,
         togglePeakLabels, isMultiSpectrumEnabled, isPeakLabelsEnabled,
         updateChartTheme, resizeChart } from './chart.js';
import { getBackend, isBackendAvailable, connectDevice, disconnectDevice,
         startAcquisition, stopAcquisition, setIntegrationTime, setNoiseLevel,
         setAccumulationCount, setSmoothingWindow, setDeviceState,
         exportData, exportBatchData, loadData, applyBaselineCorrection,
         calculatePeakArea, matchLibrary,
         calibrateWavelength, calibrateIntensity, autoExposure,
         setAutoExposureEnabled } from './bridge.js';
import { createFocusTrap, focusTrapManager } from './focus-trap.js';
import { events, EventTypes } from './event-bus.js';

// 桥接就绪状态
let bridgeReady = false;

/**
 * 设置桥接就绪状态
 * @param {boolean} ready
 */
export function setBridgeReady(ready) {
    bridgeReady = ready;
    if (ready) {
        events.emit(EventTypes.BRIDGE_READY);
    }
}

/**
 * 检查桥接是否就绪
 * @returns {boolean}
 */
export function isBridgeReady() {
    return bridgeReady;
}

// 当前主题
let currentTheme = 'dark';

// P11 新增：事件监听器管理器（用于防止内存泄漏）
const eventCleanup = createEventCleanup();

// P11 新增：定时器管理器
const timerManager = createTimerManager();

// P11 新增：焦点陷阱（用于对话框）
let themeFocusTrap = null;
let libraryFocusTrap = null;
let peakAreaFocusTrap = null;

/**
 * 初始化所有 UI 控件
 */
export function initUI() {
    bindControlEvents();
    addLog('UI 控件初始化完成', 'info');
}

/**
 * 绑定控件事件
 * P11 改进：使用事件监听器管理器统一管理
 */
function bindControlEvents() {
    // 设备控制
    const btnConnect = document.getElementById('btn-connect');
    if (btnConnect) {
        eventCleanup.add(btnConnect, 'click', handleConnect);
    }

    const btnStart = document.getElementById('btn-start');
    if (btnStart) {
        eventCleanup.add(btnStart, 'click', handleAcquisition);
    }

    // 数据导出
    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        eventCleanup.add(btnExport, 'click', () => exportData('json'));
    }

    const btnExportBatch = document.getElementById('btn-export-batch');
    if (btnExportBatch) {
        eventCleanup.add(btnExportBatch, 'click', exportBatchData);
    }

    // 峰值标注
    const btnPeakLabel = document.getElementById('btn-peak-label');
    if (btnPeakLabel) {
        eventCleanup.add(btnPeakLabel, 'click', handlePeakLabels);
    }

    // 主题切换
    const btnTheme = document.getElementById('btn-theme');
    if (btnTheme) {
        eventCleanup.add(btnTheme, 'click', handleThemeToggle);
    }

    // 基线校正
    const btnBaseline = document.getElementById('btn-baseline');
    if (btnBaseline) {
        eventCleanup.add(btnBaseline, 'click', () => applyBaselineCorrection());
    }

    // 峰面积计算
    const btnPeakArea = document.getElementById('btn-peak-area');
    if (btnPeakArea) {
        eventCleanup.add(btnPeakArea, 'click', () => calculatePeakArea(520));
    }

    // 谱库匹配
    const btnLibrary = document.getElementById('btn-library-match');
    if (btnLibrary) {
        eventCleanup.add(btnLibrary, 'click', () => matchLibrary(5));
    }

    // 导入数据
    const btnImport = document.getElementById('btn-import');
    if (btnImport) {
        eventCleanup.add(btnImport, 'click', loadData);
    }

    // 多光谱对比
    const btnHistoryAdd = document.getElementById('btn-history-add');
    if (btnHistoryAdd) {
        eventCleanup.add(btnHistoryAdd, 'click', handleAddToHistory);
    }

    const btnHistoryClear = document.getElementById('btn-history-clear');
    if (btnHistoryClear) {
        eventCleanup.add(btnHistoryClear, 'click', handleClearHistory);
    }

    const btnMultiSpectrum = document.getElementById('btn-multi-spectrum');
    if (btnMultiSpectrum) {
        eventCleanup.add(btnMultiSpectrum, 'click', handleMultiSpectrum);
    }

    // P11 新增：自动曝光和校准按钮
    bindAdvancedControls();

    // 参数输入控件
    bindParameterControls();
}

/**
 * 绑定高级控制按钮（自动曝光、校准等）
 * P11 改进：使用事件监听器管理器统一管理
 */
function bindAdvancedControls() {
    // 自动曝光开关
    const autoExposureToggle = document.getElementById('auto-exposure-toggle');
    if (autoExposureToggle) {
        eventCleanup.add(autoExposureToggle, 'change', handleAutoExposureToggle);
    }

    // 自动曝光目标强度滑块
    const autoExposureTarget = document.getElementById('auto-exposure-target');
    if (autoExposureTarget) {
        eventCleanup.add(autoExposureTarget, 'input', handleAutoExposureTargetChange);
    }

    // 执行自动曝光按钮 - 初始禁用，桥接就绪后启用
    const btnAutoExposureRun = document.getElementById('btn-auto-exposure-run');
    if (btnAutoExposureRun) {
        eventCleanup.add(btnAutoExposureRun, 'click', () => {
            if (window.RamanApp && window.RamanApp.runAutoExposure) {
                window.RamanApp.runAutoExposure();
            }
        });
        btnAutoExposureRun.disabled = true;
        btnAutoExposureRun.title = '系统初始化中...';
    }

    // 波长校准按钮 - 初始禁用，桥接就绪后启用
    const btnWavelengthCalibrate = document.getElementById('btn-wavelength-calibrate');
    if (btnWavelengthCalibrate) {
        eventCleanup.add(btnWavelengthCalibrate, 'click', () => {
            if (window.RamanApp && window.RamanApp.calibrateWavelengthUI) {
                window.RamanApp.calibrateWavelengthUI();
            }
        });
        btnWavelengthCalibrate.disabled = true;
        btnWavelengthCalibrate.title = '系统初始化中...';
    }

    // 强度校准按钮 - 初始禁用，桥接就绪后启用
    const btnIntensityCalibrate = document.getElementById('btn-intensity-calibrate');
    if (btnIntensityCalibrate) {
        eventCleanup.add(btnIntensityCalibrate, 'click', () => {
            if (window.RamanApp && window.RamanApp.calibrateIntensityUI) {
                window.RamanApp.calibrateIntensityUI();
            }
        });
        btnIntensityCalibrate.disabled = true;
        btnIntensityCalibrate.title = '系统初始化中...';
    }

    // 谱库面板关闭按钮
    const btnLibraryClose = document.getElementById('btn-library-close');
    if (btnLibraryClose) {
        eventCleanup.add(btnLibraryClose, 'click', closeLibraryPanel);
    }

    // 峰面积面板关闭按钮
    const btnPeakAreaClose = document.getElementById('btn-peak-area-close');
    if (btnPeakAreaClose) {
        eventCleanup.add(btnPeakAreaClose, 'click', closePeakAreaPanel);
    }
}

/**
 * 启用高级控制按钮（桥接就绪后调用）
 */
export function enableAdvancedControls() {
    const btnAutoExposureRun = document.getElementById('btn-auto-exposure-run');
    const btnWavelengthCalibrate = document.getElementById('btn-wavelength-calibrate');
    const btnIntensityCalibrate = document.getElementById('btn-intensity-calibrate');

    if (btnAutoExposureRun) {
        btnAutoExposureRun.disabled = false;
        btnAutoExposureRun.title = '执行自动曝光';
    }
    if (btnWavelengthCalibrate) {
        btnWavelengthCalibrate.disabled = false;
        btnWavelengthCalibrate.title = '波长校准';
    }
    if (btnIntensityCalibrate) {
        btnIntensityCalibrate.disabled = false;
        btnIntensityCalibrate.title = '强度校准';
    }

    addLog('高级控制按钮已启用', 'info');
}

/**
 * 绑定参数输入控件
 * P11 改进：为频繁触发的输入添加防抖
 */
function bindParameterControls() {
    // 积分时间 - 使用防抖（300ms）
    const integrationTimeInput = document.getElementById('integration-time');
    if (integrationTimeInput) {
        // P11 修复：使用防抖避免每次输入都调用后端
        const debouncedIntegrationTimeChange = debounce(handleIntegrationTimeChange, 300);
        eventCleanup.add(integrationTimeInput, 'input', debouncedIntegrationTimeChange);
    }

    // 噪声水平 - 使用节流（100ms）
    const noiseSlider = document.getElementById('noise-slider');
    if (noiseSlider) {
        const throttledNoiseLevelChange = throttle(handleNoiseLevelChange, 100);
        eventCleanup.add(noiseSlider, 'input', throttledNoiseLevelChange);
    }

    // 累加平均次数 - 使用防抖（300ms）
    const accumulationInput = document.getElementById('accumulation-count');
    if (accumulationInput) {
        const debouncedAccumulationCountChange = debounce(handleAccumulationCountChange, 300);
        eventCleanup.add(accumulationInput, 'input', debouncedAccumulationCountChange);
    }

    // 平滑窗口 - 使用防抖（300ms）
    const smoothingInput = document.getElementById('smoothing-window');
    if (smoothingInput) {
        const debouncedSmoothingWindowChange = debounce(handleSmoothingWindowChange, 300);
        eventCleanup.add(smoothingInput, 'input', debouncedSmoothingWindowChange);
    }

    // 设备状态
    const deviceStateSelect = document.getElementById('device-state');
    if (deviceStateSelect) {
        eventCleanup.add(deviceStateSelect, 'change', handleDeviceStateChange);
    }
}

// ==================== 事件处理函数 ====================
function handleConnect() {
    if (isBackendAvailable()) {
        if (window.isConnected) {
            disconnectDevice();
            updateConnectionStatus(false);
            events.emit(EventTypes.DEVICE_DISCONNECTED);
        } else {
            connectDevice();
            // 连接成功事件由 event-handlers.js 处理
        }
    } else {
        addLog('后端未连接', 'error');
    }
}

function handleAcquisition() {
    if (isBackendAvailable()) {
        if (window.isAcquiring) {
            stopAcquisition();
            updateAcquisitionStatus(false);
            events.emit(EventTypes.ACQUISITION_STOPPED);
        } else {
            startAcquisition();
            events.emit(EventTypes.ACQUISITION_STARTED);
        }
    }
}

function handlePeakLabels() {
    const newState = togglePeakLabels();
    const btn = document.getElementById('btn-peak-label');
    if (btn) {
        btn.textContent = `峰值标注：${newState ? '开' : '关'}`;
    }
    addLog(`峰值标注已${newState ? '开启' : '关闭'}`, 'info');
}

function handleThemeToggle() {
    // P11 改进：使用主题管理器切换主题（暗色/亮色）
    const { getThemeManager } = import('./theme.js');
    
    getThemeManager().then(({ getThemeManager }) => {
        const themeManager = getThemeManager();
        const current = themeManager.getCurrentTheme();
        
        // 在暗色和亮色之间切换
        const newTheme = current.key === 'dark' ? 'light' : 'dark';
        themeManager.setPresetTheme(newTheme);
        
        // 更新按钮文本
        const btn = document.getElementById('btn-theme');
        if (btn) {
            btn.textContent = `主题：${newTheme === 'dark' ? '暗色' : '亮色'}`;
        }
        
        // 更新图表主题
        updateChartTheme(newTheme);
        
        addLog(`主题已切换为${newTheme === 'dark' ? '暗色' : '亮色'}`, 'info');
    }).catch(error => {
        console.warn('[UI] 主题管理器加载失败:', error);
        // 降级到简单切换
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        updateCSSTheme(currentTheme);
    });
}

function handleAddToHistory() {
    const chart = getChart();
    if (!chart) return;

    // 从全局变量获取数据（由 main.js 提供）
    if (window.spectrumData && window.spectrumData.length > 0) {
        const success = addToHistory(window.spectrumData);
        if (success) {
            addLog(`已添加对比光谱`, 'success');
        } else {
            showToast('无法添加光谱（可能已达上限）', 'warning');
        }
    } else {
        showToast('没有可保存的光谱数据', 'error');
    }
}

function handleClearHistory() {
    clearHistory();
    addLog('已清除所有历史对比光谱', 'info');
}

function handleMultiSpectrum() {
    const newState = toggleMultiSpectrum();

    const btn = document.getElementById('btn-multi-spectrum');
    if (btn) {
        btn.textContent = `多谱对比：${newState ? '开' : '关'}`;
    }

    // 更新图表显示
    if (window.spectrumData) {
        updateSpectrum(window.spectrumData);
    }

    addLog(`多光谱对比已${newState ? '开启' : '关闭'}`, 'info');
}

// ==================== P11 新增：高级控件事件处理 ====================

/**
 * 自动曝光开关切换 - P11 修复：统一使用 RamanApp 命名空间
 */
async function handleAutoExposureToggle() {
    const checkbox = document.getElementById('auto-exposure-toggle');
    const enabled = checkbox.checked;

    try {
        if (window.RamanApp && window.RamanApp.toggleAutoExposure) {
            await window.RamanApp.toggleAutoExposure();
        }
    } catch (error) {
        checkbox.checked = !enabled;
        addLog(`自动曝光设置失败：${error.message}`, 'error');
        showToast(`自动曝光设置失败：${error.message}`, 'error', 5000);
    }
}

/**
 * 自动曝光目标强度变化 - P11 修复：统一使用 RamanApp 命名空间
 */
function handleAutoExposureTargetChange() {
    if (window.RamanApp && window.RamanApp.updateAutoExposureTarget) {
        const targetInput = document.getElementById('auto-exposure-target');
        window.RamanApp.updateAutoExposureTarget(targetInput ? parseFloat(targetInput.value) : 0.7);
    }
}

/**
 * 积分时间变化
 */
function handleIntegrationTimeChange() {
    const input = document.getElementById('integration-time');
    if (!input) return;
    const result = validateIntegrationTime(input.value);
    if (!result.valid) {
        showToast(result.message, 'error');
        input.value = result.value;
    }
    const valueSpan = document.getElementById('integration-time-value');
    if (valueSpan) valueSpan.textContent = result.value;
    setIntegrationTime(result.value);
    addLog(`积分时间设置为：${result.value}ms`, 'info');
}

/**
 * 噪声水平变化
 */
function handleNoiseLevelChange() {
    const slider = document.getElementById('noise-slider');
    if (!slider) return;
    const result = validateNoiseLevel(slider.value);
    if (!result.valid) {
        showToast(result.message, 'error');
        slider.value = result.value;
    }
    const valueSpan = document.getElementById('noise-value');
    if (valueSpan) valueSpan.textContent = result.value.toFixed(2);
    setNoiseLevel(result.value);
}

/**
 * 累加平均次数变化
 */
function handleAccumulationCountChange() {
    const input = document.getElementById('accumulation-count');
    if (!input) return;
    const result = validateAccumulationCount(input.value);
    if (!result.valid) {
        showToast(result.message, 'error');
        input.value = result.value;
    }
    const valueSpan = document.getElementById('accumulation-count-value');
    if (valueSpan) valueSpan.textContent = result.value;
    setAccumulationCount(result.value);
    addLog(`累加平均次数设置为：${result.value}`, 'info');
}

/**
 * 平滑窗口变化
 */
function handleSmoothingWindowChange() {
    const input = document.getElementById('smoothing-window');
    if (!input) return;
    const result = validateSmoothingWindow(input.value);
    if (!result.valid) {
        showToast(result.message, 'error');
        input.value = result.value;
    }
    const valueSpan = document.getElementById('smoothing-window-value');
    if (valueSpan) valueSpan.textContent = result.value;
    setSmoothingWindow(result.value);
    if (result.message) {
        addLog(result.message, 'info');
    }
    addLog(`平滑窗口设置为：${result.value}`, 'info');
}

/**
 * 设备状态变化
 */
function handleDeviceStateChange() {
    const select = document.getElementById('device-state');
    if (!select) return;
    setDeviceState(select.value);
    addLog(`设备状态切换为：${select.value}`, 'warning');
}

/**
 * 更新 CSS 主题变量
 * @param {'dark'|'light'} theme
 */
function updateCSSTheme(theme) {
    const root = document.documentElement;
    if (theme === 'light') {
        root.style.setProperty('--bg-primary', '#f5f5f5');
        root.style.setProperty('--bg-secondary', '#ffffff');
        root.style.setProperty('--bg-tertiary', '#e0e0e0');
        root.style.setProperty('--text-primary', '#333333');
        root.style.setProperty('--text-secondary', '#666666');
        root.style.setProperty('--border-color', '#dddddd');
        root.style.setProperty('--accent-color', '#0099cc');
    } else {
        root.style.setProperty('--bg-primary', '#1a1a2e');
        root.style.setProperty('--bg-secondary', '#16213e');
        root.style.setProperty('--bg-tertiary', '#0d0d1a');
        root.style.setProperty('--text-primary', '#eeeeee');
        root.style.setProperty('--text-secondary', '#aaaaaa');
        root.style.setProperty('--border-color', '#333333');
        root.style.setProperty('--accent-color', '#00d9ff');
    }
}

// ==================== 面板控制 ====================
/**
 * 关闭谱库匹配面板
 */
export function closeLibraryPanel() {
    const panel = document.getElementById('library-panel');
    if (panel) {
        panel.style.display = 'none';
    }
}

/**
 * 关闭峰面积面板
 */
export function closePeakAreaPanel() {
    const panel = document.getElementById('peak-area-panel');
    if (panel) {
        panel.style.display = 'none';
    }
}

// ==================== 状态更新 ====================
/**
 * 更新设备连接状态 UI
 * @param {boolean} connected
 */
export function updateConnectionStatus(connected) {
    const btn = document.getElementById('btn-connect');
    const statusIndicator = document.getElementById('device-status');
    const statusText = document.getElementById('device-status-text');
    const btnStart = document.getElementById('btn-start');
    const btnExport = document.getElementById('btn-export');
    const btnExportBatch = document.getElementById('btn-export-batch');

    if (btn) {
        btn.textContent = connected ? '断开连接' : '连接设备';
    }
    if (statusIndicator) {
        statusIndicator.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
    }
    if (statusText) {
        statusText.textContent = connected ? '已连接' : '未连接';
    }
    if (btnStart) {
        btnStart.disabled = !connected;
    }
    if (btnExport) {
        btnExport.disabled = !connected;
    }
    if (btnExportBatch) {
        btnExportBatch.disabled = !connected;
    }
}

/**
 * 更新采集状态 UI
 * @param {boolean} acquiring
 */
export function updateAcquisitionStatus(acquiring) {
    const btn = document.getElementById('btn-start');
    const statusIndicator = document.getElementById('acquisition-status');
    const statusText = document.getElementById('acquisition-status-text');

    if (btn) {
        btn.textContent = acquiring ? '停止采集' : '开始采集';
    }
    if (statusIndicator) {
        statusIndicator.className = `status-indicator ${acquiring ? 'connected' : 'disconnected'}`;
    }
    if (statusText) {
        statusText.textContent = acquiring ? '采集中' : '停止';
    }
}

/**
 * P11 新增：更新校准状态 UI
 * @param {Object} status - 校准状态对象
 * @param {Object} status.wavelength - 波长校准状态
 * @param {Object} status.intensity - 强度校准状态
 */
export function updateCalibrationStatus(status) {
    // 更新波长校准状态
    if (status && status.wavelength) {
        const wlStatusIndicator = document.getElementById('wavelength-calibration-status');
        const wlStatusText = document.getElementById('wavelength-calibration-text');
        
        if (wlStatusIndicator) {
            wlStatusIndicator.className = `status-indicator ${status.wavelength.calibrated ? 'connected' : 'disconnected'}`;
            wlStatusIndicator.title = status.wavelength.calibrated ? '波长已校准' : '波长未校准';
        }
        if (wlStatusText) {
            if (status.wavelength.calibrated) {
                wlStatusText.textContent = `已校准 (${status.wavelength.correction?.toFixed(3) || 0} cm⁻¹)`;
            } else {
                wlStatusText.textContent = '未校准';
            }
        }
    }

    // 更新强度校准状态
    if (status && status.intensity) {
        const intStatusIndicator = document.getElementById('intensity-calibration-status');
        const intStatusText = document.getElementById('intensity-calibration-text');

        if (intStatusIndicator) {
            intStatusIndicator.className = `status-indicator ${status.intensity.calibrated ? 'connected' : 'disconnected'}`;
            intStatusIndicator.title = status.intensity.calibrated ? '强度已校准' : '强度未校准';
        }
        if (intStatusText) {
            intStatusText.textContent = status.intensity.calibrated ? '已校准' : '未校准';
        }
    }
}

// ==================== P11 修复：键盘快捷键支持 ====================

/**
 * 初始化键盘快捷键
 * P11 改进：使用事件监听器管理器管理键盘事件
 */
export function initKeyboardShortcuts() {
    const handleKeyDown = (e) => {
        // 空格 = 开始/停止采集
        if (e.code === 'Space' && window.isConnected) {
            e.preventDefault();
            const btn = document.getElementById('btn-start');
            if (btn) btn.click();
        }
        // C = 连接/断开
        if (e.code === 'KeyC') {
            e.preventDefault();
            const btn = document.getElementById('btn-connect');
            if (btn) btn.click();
        }
        // E = 导出数据
        if (e.code === 'KeyE' && window.isConnected) {
            e.preventDefault();
            const btn = document.getElementById('btn-export');
            if (btn) btn.click();
        }
        // P = 切换峰值标注
        if (e.code === 'KeyP') {
            e.preventDefault();
            const btn = document.getElementById('btn-peak-label');
            if (btn) btn.click();
        }
        // T = 切换主题面板
        if (e.code === 'KeyT') {
            e.preventDefault();
            const themePanel = document.getElementById('theme-panel');
            if (themePanel) {
                const isHidden = themePanel.style.display === 'none' || !themePanel.style.display;
                themePanel.style.display = isHidden ? 'block' : 'none';
                if (isHidden) {
                    // ✅ 启用焦点陷阱
                    if (themeFocusTrap) {
                        themeFocusTrap.destroy();
                    }
                    themeFocusTrap = createFocusTrap(themePanel);
                } else {
                    // ✅ 禁用焦点陷阱
                    if (themeFocusTrap) {
                        themeFocusTrap.destroy();
                        themeFocusTrap = null;
                    }
                }
            }
        }
        // ESC = 关闭所有面板
        if (e.code === 'Escape') {
            // 关闭谱库面板
            const libraryPanel = document.getElementById('library-panel');
            if (libraryPanel && libraryPanel.style.display !== 'none') {
                libraryPanel.style.display = 'none';
                if (libraryFocusTrap) {
                    libraryFocusTrap.destroy();
                    libraryFocusTrap = null;
                }
            }
            // 关闭峰面积面板
            const peakAreaPanel = document.getElementById('peak-area-panel');
            if (peakAreaPanel && peakAreaPanel.style.display !== 'none') {
                peakAreaPanel.style.display = 'none';
                if (peakAreaFocusTrap) {
                    peakAreaFocusTrap.destroy();
                    peakAreaFocusTrap = null;
                }
            }
            // 关闭主题面板
            const themePanel = document.getElementById('theme-panel');
            if (themePanel && themePanel.style.display !== 'none') {
                themePanel.style.display = 'none';
                if (themeFocusTrap) {
                    themeFocusTrap.destroy();
                    themeFocusTrap = null;
                }
            }
        }
    };

    // 使用事件监听器管理器注册
    eventCleanup.add(document, 'keydown', handleKeyDown);
}

/**
 * P11 新增：清理所有事件监听器（防止内存泄漏）
 * 在页面卸载或重新初始化时调用
 */
export function cleanupEventListeners() {
    eventCleanup.removeAll();
    timerManager.clearAll();
    addLog('事件监听器和定时器已清理', 'info');
}

/**
 * 检查是否首次运行并显示免责声明
 */
export function checkFirstRun() {
    const hasSeenDisclaimer = localStorage.getItem('hasSeenDisclaimer');
    if (!hasSeenDisclaimer) {
        showDisclaimerModal();
        localStorage.setItem('hasSeenDisclaimer', 'true');
    }
}

/**
 * 显示免责声明弹窗
 */
export function showDisclaimerModal() {
    const modal = document.createElement('div');
    modal.id = 'disclaimer-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    modal.innerHTML = `
        <div style="
            background: var(--bg-secondary);
            border: 2px solid #ffaa00;
            border-radius: 10px;
            padding: 30px;
            max-width: 500px;
            box-shadow: 0 10px 40px rgba(255, 170, 0, 0.3);
        ">
            <h2 style="color: #ffaa00; margin-bottom: 15px; font-size: 1.4em;">
                ⚠️ 重要提示
            </h2>
            <div style="color: var(--text-primary); line-height: 1.8; margin-bottom: 20px;">
                <p style="margin-bottom: 10px;"><strong>本软件为教学演示软件，具有以下限制：</strong></p>
                <ul style="margin-left: 20px; color: var(--text-secondary);">
                    <li>谱库数据为高斯峰模拟数据，非实测光谱</li>
                    <li>峰值检测算法为简化实现，可能存在误差</li>
                    <li>设备驱动为模拟驱动，不支持真实仪器</li>
                </ul>
                <p style="margin-top: 15px; color: #ff4444; font-weight: bold;">
                    ⚠️ 本软件仅用于教学演示和算法验证，不可用于实际物质分析或科研用途。
                </p>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button id="disclaimer-accept-btn" style="
                    padding: 10px 25px;
                    background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
                    color: #000;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 0.95em;
                ">我已知晓</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    
    document.getElementById('disclaimer-accept-btn').addEventListener('click', () => {
        closeDisclaimerModal();
    });
}

/**
 * 关闭免责声明弹窗
 */
export function closeDisclaimerModal() {
    const modal = document.getElementById('disclaimer-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * P11 新增：切换免责声明折叠状态
 */
export function toggleDisclaimer() {
    const disclaimer = document.getElementById('library-disclaimer');
    const content = document.getElementById('library-disclaimer-content');
    const toggleText = document.getElementById('disclaimer-toggle-text');
    
    if (!disclaimer || !content) return;
    
    const isExpanded = content.classList.contains('expanded');
    
    if (isExpanded) {
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        disclaimer.classList.remove('expanded');
        if (toggleText) {
            toggleText.textContent = '点击展开详情';
        }
    } else {
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        disclaimer.classList.add('expanded');
        if (toggleText) {
            toggleText.textContent = '点击收起详情';
        }
    }
}

// 导出到全局供 HTML 调用
if (typeof window !== 'undefined') {
    window.toggleDisclaimer = toggleDisclaimer;
}
