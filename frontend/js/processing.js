/**
 * 谱图预处理模块
 * @module processing
 */

import { addLog, showToast } from './utils.js';
import {
    initBridge,
    getBackend,
    preprocess as apiPreprocess
} from './bridge_helper.js';

let originalChart = null;
let processedChart = null;
let pythonBackend = null;
let originalSpectrum = null;
let processedSpectrum = null;
let wavelengthData = [];
let processingHistory = [];

// 当前选中的工具
let currentTool = 'smooth';

// 参数
let params = {
    smooth: { method: 'savitzky_golay', windowSize: 5, polyOrder: 2 },
    baseline: { method: 'iterative_poly', order: 5, iterations: 10 },
    normalize: { method: 'minmax' },
    derivative: { order: 1, windowSize: 5 },
    snv: {}
};

// 光谱仪配置常量
const SPECTROMETER_CONFIG = {
    WAVELENGTH_MIN: 200,
    WAVELENGTH_MAX: 3200,
    DATA_POINTS: 1024
};

/**
 * 初始化预处理页面
 */
export async function initProcessingPage() {
    // 使用统一的桥接初始化
    const bridgeReady = await initBridge();
    if (!bridgeReady) {
        showToast('后端连接失败', 'error');
        return;
    }
    
    pythonBackend = getBackend();
    
    initCharts();
    bindEvents();
    loadSpectrum();
    addLog('谱图预处理页面初始化完成', 'info');
}

/**
 * 初始化图表
 */
function initCharts() {
    // 生成波长数据
    wavelengthData = [];
    for (let i = 0; i < SPECTROMETER_CONFIG.DATA_POINTS; i++) {
        wavelengthData.push(
            SPECTROMETER_CONFIG.WAVELENGTH_MIN +
            (SPECTROMETER_CONFIG.WAVELENGTH_MAX - SPECTROMETER_CONFIG.WAVELENGTH_MIN) * i / (SPECTROMETER_CONFIG.DATA_POINTS - 1)
        );
    }

    // 原始光谱图表
    if (document.getElementById('original-chart')) {
        originalChart = echarts.init(document.getElementById('original-chart'));
        originalChart.setOption({
            title: { text: '', textStyle: { color: '#00d9ff' } },
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
        });
    }

    // 处理后光谱图表
    if (document.getElementById('processed-chart')) {
        processedChart = echarts.init(document.getElementById('processed-chart'));
        processedChart.setOption({
            title: { text: '', textStyle: { color: '#00ff88' } },
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
                name: '处理后',
                type: 'line',
                data: wavelengthData.map(w => [w, 0]),
                lineStyle: { color: '#00ff88', width: 1.5 },
                symbol: 'none'
            }]
        });
    }

    // 窗口大小变化时调整图表
    window.addEventListener('resize', () => {
        if (originalChart) originalChart.resize();
        if (processedChart) processedChart.resize();
    });
}

/**
 * 加载光谱数据
 */
function loadSpectrum() {
    try {
        const spectrumStr = localStorage.getItem('current_spectrum');
        if (spectrumStr) {
            originalSpectrum = JSON.parse(spectrumStr);
            updateOriginalChart(originalSpectrum);
            processedSpectrum = [...originalSpectrum];
            updateProcessedChart(processedSpectrum);
            addLog(`已加载光谱数据：${originalSpectrum.length} 点`, 'success');
        } else {
            showToast('未找到光谱数据', 'warning');
        }
    } catch (error) {
        addLog(`加载光谱数据失败：${error.message}`, 'error');
    }
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 工具切换
    document.querySelectorAll('.btn-tool[data-tool]').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.id === 'btn-reset' || btn.id === 'btn-apply' || btn.id === 'btn-export') return;
            
            document.querySelectorAll('.btn-tool[data-tool]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTool = btn.dataset.tool;
            showParamSection(currentTool);
        });
    });

    // 重置按钮
    document.getElementById('btn-reset').addEventListener('click', resetProcessing);

    // 应用按钮
    document.getElementById('btn-apply').addEventListener('click', applyProcessing);

    // 导出按钮
    document.getElementById('btn-export').addEventListener('click', exportSpectrum);

    // 平滑参数
    document.getElementById('window-slider').addEventListener('input', (e) => {
        params.smooth.windowSize = parseInt(e.target.value);
        document.getElementById('window-value').textContent = params.smooth.windowSize;
    });

    document.getElementById('poly-slider').addEventListener('input', (e) => {
        params.smooth.polyOrder = parseInt(e.target.value);
        document.getElementById('poly-value').textContent = params.smooth.polyOrder;
    });

    document.getElementById('smooth-method').addEventListener('change', (e) => {
        params.smooth.method = e.target.value;
        document.getElementById('poly-order-group').style.display = 
            params.smooth.method === 'savitzky_golay' ? 'block' : 'none';
    });

    // 基线参数
    document.getElementById('baseline-order-slider').addEventListener('input', (e) => {
        params.baseline.order = parseInt(e.target.value);
        document.getElementById('baseline-order-value').textContent = params.baseline.order;
    });

    document.getElementById('iter-slider').addEventListener('input', (e) => {
        params.baseline.iterations = parseInt(e.target.value);
        document.getElementById('iter-value').textContent = params.baseline.iterations;
    });

    document.getElementById('baseline-method').addEventListener('change', (e) => {
        params.baseline.method = e.target.value;
    });

    // 归一化方法
    document.getElementById('normalize-method').addEventListener('change', (e) => {
        params.normalize.method = e.target.value;
    });

    // 求导参数
    document.getElementById('derivative-order').addEventListener('change', (e) => {
        params.derivative.order = parseInt(e.target.value);
    });

    document.getElementById('deriv-window-slider').addEventListener('input', (e) => {
        params.derivative.windowSize = parseInt(e.target.value);
        document.getElementById('deriv-window-value').textContent = params.derivative.windowSize;
    });
}

/**
 * 显示参数区域
 */
function showParamSection(tool) {
    document.querySelectorAll('.param-section').forEach(el => el.style.display = 'none');
    
    const section = document.getElementById(`${tool}-params`);
    if (section) section.style.display = 'block';
}

/**
 * 更新原始光谱图表
 */
function updateOriginalChart(spectrum) {
    if (!originalChart || !spectrum) return;
    const chartData = spectrum.map((v, i) => [wavelengthData[i], v]);
    originalChart.setOption({ series: [{ data: chartData }] });
}

/**
 * 更新处理后光谱图表
 */
function updateProcessedChart(spectrum) {
    if (!processedChart || !spectrum) return;
    const chartData = spectrum.map((v, i) => [wavelengthData[i], v]);
    processedChart.setOption({ series: [{ data: chartData }] });
}

/**
 * 重置处理
 */
function resetProcessing() {
    if (!originalSpectrum) {
        showToast('没有光谱数据', 'error');
        return;
    }
    processedSpectrum = [...originalSpectrum];
    processingHistory = [];
    updateProcessedChart(processedSpectrum);
    updateHistory();
    addLog('已重置到原始光谱', 'info');
}

/**
 * 应用处理
 */
async function applyProcessing() {
    if (!processedSpectrum) {
        showToast('没有光谱数据', 'error');
        return;
    }

    try {
        // 构建预处理工具列表
        const tools = [];
        
        if (currentTool === 'smooth') {
            tools.push(['smooth', {
                method: params.smooth.method,
                window_size: params.smooth.windowSize,
                poly_order: params.smooth.polyOrder
            }]);
        } else if (currentTool === 'baseline') {
            tools.push(['baseline', {
                order: params.baseline.order,
                iterations: params.baseline.iterations
            }]);
        } else if (currentTool === 'normalize') {
            tools.push(['normalize', {
                method: params.normalize.method
            }]);
        } else if (currentTool === 'derivative') {
            tools.push(['derivative', {
                order: params.derivative.order,
                smooth_window: params.derivative.windowSize
            }]);
        } else if (currentTool === 'snv') {
            tools.push(['snv', {}]);
        }

        // 使用 bridge_helper 封装的方法
        const result = await apiPreprocess(processedSpectrum, { tools });

        if (result.success) {
            const oldSpectrum = [...processedSpectrum];
            processedSpectrum = result.data.spectrum;

            // 添加到历史
            processingHistory.push({
                tool: currentTool,
                params: { ...params[currentTool] },
                timestamp: new Date().toLocaleTimeString()
            });

            updateProcessedChart(processedSpectrum);
            updateHistory();
            addLog(`${getToolName(currentTool)} 处理完成`, 'success');
            showToast(`${getToolName(currentTool)} 处理完成`, 'success');
        } else {
            showToast(`处理失败：${result.error}`, 'error');
        }
    } catch (error) {
        addLog(`处理异常：${error.message}`, 'error');
        showToast('处理失败', 'error');
    }
}

/**
 * 获取工具名称
 */
function getToolName(tool) {
    const names = {
        smooth: '平滑',
        baseline: '基线校正',
        normalize: '归一化',
        derivative: '求导',
        snv: 'SNV 变换'
    };
    return names[tool] || tool;
}

/**
 * 更新历史显示
 */
function updateHistory() {
    const list = document.getElementById('history-list');
    if (processingHistory.length === 0) {
        list.innerHTML = '<div class="history-item">暂无处理记录</div>';
        return;
    }

    list.innerHTML = processingHistory.map((item, i) => 
        `<div class="history-item">${i + 1}. [${item.timestamp}] ${getToolName(item.tool)}</div>`
    ).join('');
}

/**
 * 导出光谱
 */
function exportSpectrum() {
    if (!processedSpectrum) {
        showToast('没有可导出的光谱', 'error');
        return;
    }

    // 生成 CSV
    let csv = 'Wavelength (cm⁻¹),Intensity\n';
    processedSpectrum.forEach((v, i) => {
        csv += `${wavelengthData[i].toFixed(4)},${v.toFixed(8)}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `processed_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    addLog('光谱已导出', 'success');
    showToast('光谱已导出', 'success');
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProcessingPage);
} else {
    initProcessingPage();
}
