/**
 * 实时采集模块
 * @module live
 */

import { addLog, showToast } from './utils.js';
import { initBridge, isBridgeReady, getBackend, onLiveSpectrumUpdated } from './bridge_helper.js';

let chart = null;
let isLive = false;
let isPaused = false;
let frameCount = 0;
let startTime = null;
let timerInterval = null;
let wavelengthData = [];
let pythonBackend = null;

// 光谱仪配置常量
const SPECTROMETER_CONFIG = {
    WAVELENGTH_MIN: 200,
    WAVELENGTH_MAX: 3200,
    DATA_POINTS: 1024
};

/**
 * 初始化实时采集页面
 */
export async function initLivePage() {
    // 使用统一的桥接初始化
    const bridgeReady = await initBridge();
    if (!bridgeReady) {
        addLog('后端连接失败', 'error');
        showToast('后端连接失败，请刷新页面重试', 'error');
        return;
    }
    
    pythonBackend = getBackend();
    
    initChart();
    bindEvents();
    
    // 监听实时光谱更新
    onLiveSpectrumUpdated((spectrum, count) => {
        onSpectrumUpdate(spectrum, count);
    });
    
    addLog('实时采集页面初始化完成', 'info');
}

/**
 * 初始化图表
 */
function initChart() {
    if (!document.getElementById('live-chart')) {
        addLog('图表容器不存在', 'error');
        return;
    }

    chart = echarts.init(document.getElementById('live-chart'));

    // 生成波长数据
    wavelengthData = [];
    for (let i = 0; i < SPECTROMETER_CONFIG.DATA_POINTS; i++) {
        wavelengthData.push(
            SPECTROMETER_CONFIG.WAVELENGTH_MIN +
            (SPECTROMETER_CONFIG.WAVELENGTH_MAX - SPECTROMETER_CONFIG.WAVELENGTH_MIN) * i / (SPECTROMETER_CONFIG.DATA_POINTS - 1)
        );
    }

    const option = {
        title: { text: '实时光谱', textStyle: { color: '#00d9ff' } },
        tooltip: { trigger: 'axis' },
        xAxis: {
            name: '拉曼位移 (cm⁻¹)',
            nameTextStyle: { color: '#aaa' },
            axisLine: { lineStyle: { color: '#333' } },
            axisLabel: { color: '#aaa' }
        },
        yAxis: {
            name: '强度 (a.u.)',
            nameTextStyle: { color: '#aaa' },
            axisLine: { lineStyle: { color: '#333' } },
            axisLabel: { color: '#aaa' }
        },
        series: [{
            name: '光谱',
            type: 'line',
            data: wavelengthData.map(w => [w, 0]),
            lineStyle: { color: '#00d9ff', width: 1.5 },
            symbol: 'none'
        }]
    };

    chart.setOption(option);
}

/**
 * 绑定事件
 */
function bindEvents() {
    document.getElementById('btn-live-start').addEventListener('click', startLive);
    document.getElementById('btn-live-pause').addEventListener('click', togglePause);
    document.getElementById('btn-live-stop').addEventListener('click', stopLive);
    document.getElementById('btn-apply-rate').addEventListener('click', applyRefreshRate);

    // 窗口大小变化时调整图表
    window.addEventListener('resize', () => {
        if (chart) chart.resize();
    });
}

/**
 * 开始实时采集
 */
async function startLive() {
    if (!isBridgeReady()) {
        showToast('后端桥接未就绪', 'error');
        return;
    }

    const refreshRate = parseFloat(document.getElementById('refresh-rate-input').value);

    try {
        // 使用 bridge_helper 封装的方法
        const result = await window.bridge.startLiveMode(refreshRate);

        if (result.success) {
            isLive = true;
            isPaused = false;
            frameCount = 0;
            startTime = Date.now();

            // 更新 UI
            updateUIState();
            startTimer();

            addLog(`实时采集已启动，刷新率：${refreshRate}Hz`, 'success');
            showToast('实时采集已启动', 'success');
        } else {
            showToast(`启动失败：${result.error || result.message}`, 'error');
        }
    } catch (error) {
        addLog(`启动异常：${error.message}`, 'error');
        showToast('启动失败', 'error');
    }
}

/**
 * 暂停/继续
 */
async function togglePause() {
    if (!pythonBackend || !pythonBackend.pauseLiveMode) return;

    try {
        isPaused = !isPaused;
        const resultJson = await new Promise((resolve, reject) => {
            pythonBackend.pauseLiveMode(JSON.stringify(isPaused), resolve);
        });

        const result = JSON.parse(resultJson);

        if (result.success) {
            updateUIState();
            addLog(isPaused ? '实时采集已暂停' : '实时采集已继续', 'info');
        } else {
            showToast(`操作失败：${result.error}`, 'error');
        }
    } catch (error) {
        addLog(`操作异常：${error.message}`, 'error');
        showToast('操作失败', 'error');
    }
}

/**
 * 停止实时采集
 */
async function stopLive() {
    if (!pythonBackend || !pythonBackend.stopLiveMode) return;

    try {
        const resultJson = await new Promise((resolve, reject) => {
            pythonBackend.stopLiveMode(resolve);
        });

        const result = JSON.parse(resultJson);

        if (result.success) {
            isLive = false;
            isPaused = false;
            stopTimer();
            updateUIState();
            addLog('实时采集已停止', 'info');
            showToast('实时采集已停止', 'info');
        } else {
            showToast(`停止失败：${result.error}`, 'error');
        }
    } catch (error) {
        addLog(`停止异常：${error.message}`, 'error');
        showToast('停止失败', 'error');
    }
}

/**
 * 应用刷新率
 */
async function applyRefreshRate() {
    if (!pythonBackend || !pythonBackend.setLiveRefreshRate) {
        showToast('功能不可用', 'error');
        return;
    }

    const refreshRate = parseFloat(document.getElementById('refresh-rate-input').value);

    try {
        const resultJson = await new Promise((resolve, reject) => {
            pythonBackend.setLiveRefreshRate(JSON.stringify(refreshRate), resolve);
        });

        const result = JSON.parse(resultJson);

        if (result.success) {
            addLog(`刷新率已更新：${refreshRate}Hz`, 'success');
            showToast(`刷新率已更新：${refreshRate}Hz`, 'success');
        } else {
            showToast(`更新失败：${result.error}`, 'error');
        }
    } catch (error) {
        showToast('更新失败', 'error');
    }
}

/**
 * 更新 UI 状态
 */
function updateUIState() {
    const btnStart = document.getElementById('btn-live-start');
    const btnPause = document.getElementById('btn-live-pause');
    const btnStop = document.getElementById('btn-live-stop');
    const indicator = document.getElementById('live-indicator');
    const statusText = document.getElementById('live-status-text');
    const rateInput = document.getElementById('refresh-rate-input');
    const btnApply = document.getElementById('btn-apply-rate');

    btnStart.disabled = isLive;
    btnPause.disabled = !isLive;
    btnStop.disabled = !isLive;
    rateInput.disabled = isLive;
    btnApply.disabled = isLive;

    if (isLive) {
        if (isPaused) {
            indicator.className = 'live-indicator paused';
            statusText.textContent = '暂停中';
            btnPause.textContent = '▶️ 继续';
        } else {
            indicator.className = 'live-indicator active';
            statusText.textContent = '采集中';
            btnPause.textContent = '⏸️ 暂停';
        }
    } else {
        indicator.className = 'live-indicator';
        statusText.textContent = '待机';
        btnPause.textContent = '⏸️ 暂停';
    }
}

/**
 * 启动计时器
 */
function startTimer() {
    stopTimer();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const hours = Math.floor(elapsed / 3600).toString().padStart(2, '0');
        const minutes = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        document.getElementById('live-timer').textContent = `${hours}:${minutes}:${seconds}`;
    }, 1000);
}

/**
 * 停止计时器
 */
function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    document.getElementById('live-timer').textContent = '00:00:00';
}

/**
 * 更新帧计数
 */
function updateFrameCount(count) {
    frameCount = count;
    document.getElementById('frame-counter').textContent = `Frame: ${frameCount}`;
}

/**
 * 更新光谱显示
 */
function updateSpectrum(spectrumData) {
    if (!chart || !spectrumData) return;

    const chartData = spectrumData.map((v, i) => [wavelengthData[i], v]);

    chart.setOption({
        series: [{ data: chartData }]
    }, true);
}

// ==================== 信号回调 ====================

/**
 * 实时光谱更新回调
 */
function onLiveSpectrumUpdated(data) {
    try {
        const parsed = JSON.parse(data);
        if (parsed.spectrum) {
            updateSpectrum(parsed.spectrum);
        }
        if (parsed.frame_count !== undefined) {
            updateFrameCount(parsed.frame_count);
        }
    } catch (error) {
        addLog(`解析光谱数据失败：${error.message}`, 'error');
    }
}

/**
 * 实时采集启动回调
 */
function onLiveModeStarted(sessionId) {
    addLog(`实时采集已启动：session_id=${sessionId}`, 'success');
}

/**
 * 实时采集停止回调
 */
function onLiveModeStopped() {
    isLive = false;
    isPaused = false;
    stopTimer();
    updateUIState();
    addLog('实时采集已停止', 'info');
}

/**
 * 实时采集暂停/继续回调
 */
function onLiveModePaused(paused) {
    isPaused = paused;
    updateUIState();
    addLog(paused ? '实时采集已暂停' : '实时采集已继续', 'info');
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLivePage);
} else {
    initLivePage();
}
