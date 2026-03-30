/**
 * 峰值分析模块
 * @module peaks
 */

import { addLog, showToast } from './utils.js';
import {
    initBridge,
    getBackend,
    callBackend,
    findPeaks as apiFindPeaks,
    fitPeak as apiFitPeak
} from './bridge_helper.js';

let chart = null;
let pythonBackend = null;
let currentSpectrum = null;
let detectedPeaks = [];
let selectedPeakIndex = -1;
let wavelengthData = [];

// 光谱仪配置常量
const SPECTROMETER_CONFIG = {
    WAVELENGTH_MIN: 200,
    WAVELENGTH_MAX: 3200,
    DATA_POINTS: 1024
};

// 参数
let params = {
    sensitivity: 0.5,
    minSnr: 3.0,
    minDistance: 5
};

/**
 * 初始化峰值分析页面
 */
export async function initPeaksPage() {
    // 使用统一的桥接初始化
    const bridgeReady = await initBridge();
    if (!bridgeReady) {
        showToast('后端连接失败', 'error');
        return;
    }
    
    pythonBackend = getBackend();
    
    initChart();
    bindEvents();
    loadSpectrumFromMain();
    addLog('峰值分析页面初始化完成', 'info');
}

/**
 * 初始化图表
 */
function initChart() {
    if (!document.getElementById('peaks-chart')) {
        addLog('图表容器不存在', 'error');
        return;
    }

    chart = echarts.init(document.getElementById('peaks-chart'));

    // 生成波长数据
    wavelengthData = [];
    for (let i = 0; i < SPECTROMETER_CONFIG.DATA_POINTS; i++) {
        wavelengthData.push(
            SPECTROMETER_CONFIG.WAVELENGTH_MIN +
            (SPECTROMETER_CONFIG.WAVELENGTH_MAX - SPECTROMETER_CONFIG.WAVELENGTH_MIN) * i / (SPECTROMETER_CONFIG.DATA_POINTS - 1)
        );
    }

    const option = {
        title: { text: '峰值分析', textStyle: { color: '#00d9ff' } },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                let text = `拉曼位移：${params[0].value[0].toFixed(1)} cm⁻¹<br/>`;
                params.forEach(param => {
                    text += `<span style="color:${param.color}">${param.seriesName}: ${param.value[1].toFixed(4)}</span><br/>`;
                });
                return text;
            }
        },
        legend: {
            data: ['光谱', '检测到的峰'],
            textStyle: { color: '#aaa' },
            top: 30
        },
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
        series: [
            {
                name: '光谱',
                type: 'line',
                data: wavelengthData.map(w => [w, 0]),
                lineStyle: { color: '#00d9ff', width: 1.5 },
                symbol: 'none'
            },
            {
                name: '检测到的峰',
                type: 'scatter',
                symbol: 'circle',
                symbolSize: 8,
                data: [],
                itemStyle: { color: '#ff4444' }
            }
        ]
    };

    chart.setOption(option);
}

/**
 * 从主页面加载光谱数据
 */
function loadSpectrumFromMain() {
    // 尝试从 window.opener 或 localStorage 获取光谱数据
    try {
        if (window.opener && window.opener.RamanApp) {
            // 从 opener 获取（如果是从主页面打开的）
            addLog('尝试从主页面获取光谱数据...', 'info');
        }
        
        // 从 localStorage 获取（备用方案）
        const spectrumStr = localStorage.getItem('current_spectrum');
        if (spectrumStr) {
            currentSpectrum = JSON.parse(spectrumStr);
            updateChartSpectrum(currentSpectrum);
            addLog(`已加载光谱数据：${currentSpectrum.length} 点`, 'success');
        } else {
            showToast('未找到光谱数据，请从主页面发送光谱', 'warning');
        }
    } catch (error) {
        addLog(`加载光谱数据失败：${error.message}`, 'error');
    }
}

/**
 * 绑定事件
 */
function bindEvents() {
    document.getElementById('btn-auto-find').addEventListener('click', autoFindPeaks);
    document.getElementById('btn-clear-peaks').addEventListener('click', clearPeaks);
    document.getElementById('btn-export-peaks').addEventListener('click', exportPeaks);
    document.getElementById('btn-fit-peak').addEventListener('click', fitSelectedPeak);

    // 参数滑块
    document.getElementById('sensitivity-slider').addEventListener('input', (e) => {
        params.sensitivity = parseFloat(e.target.value);
        document.getElementById('sensitivity-value').textContent = params.sensitivity.toFixed(2);
    });

    document.getElementById('snr-slider').addEventListener('input', (e) => {
        params.minSnr = parseFloat(e.target.value);
        document.getElementById('snr-value').textContent = params.minSnr.toFixed(1);
    });

    document.getElementById('distance-slider').addEventListener('input', (e) => {
        params.minDistance = parseInt(e.target.value);
        document.getElementById('distance-value').textContent = params.minDistance;
    });

    // 窗口大小变化时调整图表
    window.addEventListener('resize', () => {
        if (chart) chart.resize();
    });
}

/**
 * 更新图表光谱
 */
function updateChartSpectrum(spectrum) {
    if (!chart || !spectrum) return;

    const chartData = spectrum.map((v, i) => [wavelengthData[i], v]);

    chart.setOption({
        series: [
            { data: chartData },
            { data: detectedPeaks.map(p => [p.position, p.intensity]) }
        ]
    });
}

/**
 * 自动寻峰
 */
async function autoFindPeaks() {
    if (!currentSpectrum || currentSpectrum.length === 0) {
        showToast('没有光谱数据', 'error');
        return;
    }

    try {
        // 使用 bridge_helper 封装的方法
        const result = await apiFindPeaks(currentSpectrum, {
            sensitivity: params.sensitivity,
            minSnr: params.minSnr,
            minDistance: params.minDistance
        });

        if (result.success) {
            detectedPeaks = result.data.peaks || [];
            updatePeakList();
            updateChartPeaks();

            addLog(`检测到 ${detectedPeaks.length} 个峰值`, 'success');
            showToast(`检测到 ${detectedPeaks.length} 个峰值`, 'success');
        } else {
            showToast(`寻峰失败：${result.error}`, 'error');
        }
    } catch (error) {
        addLog(`寻峰异常：${error.message}`, 'error');
        showToast('寻峰失败', 'error');
    }
}

/**
 * 清除所有峰
 */
function clearPeaks() {
    detectedPeaks = [];
    selectedPeakIndex = -1;
    updatePeakList();
    updateChartPeaks();
    document.getElementById('fit-result').style.display = 'none';
    document.getElementById('btn-fit-peak').disabled = true;
    addLog('已清除所有峰值', 'info');
}

/**
 * 导出峰值列表
 */
function exportPeaks() {
    if (detectedPeaks.length === 0) {
        showToast('没有可导出的峰值', 'warning');
        return;
    }

    // 生成 CSV 内容
    let csv = 'Position (cm⁻¹),Intensity,SNR,Index\n';
    detectedPeaks.forEach(peak => {
        csv += `${peak.position.toFixed(4)},${peak.intensity.toFixed(6)},${peak.snr.toFixed(2)},${peak.index}\n`;
    });

    // 创建下载
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `peaks_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    addLog(`已导出 ${detectedPeaks.length} 个峰值`, 'success');
    showToast('峰值列表已导出', 'success');
}

/**
 * 更新峰值列表显示
 */
function updatePeakList() {
    const list = document.getElementById('peak-list');
    const countSpan = document.getElementById('peak-count');

    countSpan.textContent = detectedPeaks.length;

    if (detectedPeaks.length === 0) {
        list.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">未检测到峰值</div>';
        return;
    }

    list.innerHTML = detectedPeaks.map((peak, index) => `
        <div class="peak-item ${index === selectedPeakIndex ? 'selected' : ''}"
             data-index="${index}">
            <div>
                <div class="peak-position">${peak.position.toFixed(2)} cm⁻¹</div>
                <div class="peak-intensity">强度：${peak.intensity.toFixed(4)}</div>
                <div class="peak-snr">SNR: ${peak.snr.toFixed(2)}</div>
            </div>
            <div style="color: #00d9ff;">➜</div>
        </div>
    `).join('');

    // 绑定点击事件
    list.querySelectorAll('.peak-item').forEach((item) => {
        const index = parseInt(item.getAttribute('data-index'), 10);
        item.addEventListener('click', () => selectPeak(index));
    });
}

/**
 * 更新图表峰值标记
 */
function updateChartPeaks() {
    if (!chart) return;

    chart.setOption({
        series: [
            {},  // 保持光谱数据不变
            {
                data: detectedPeaks.map(p => [p.position, p.intensity])
            }
        ]
    });
}

/**
 * 选择峰值
 */
function selectPeak(index) {
    if (index < 0 || index >= detectedPeaks.length) return;
    
    selectedPeakIndex = index;
    updatePeakList();
    document.getElementById('btn-fit-peak').disabled = false;
    
    addLog(`选中峰值：${detectedPeaks[index].position.toFixed(2)} cm⁻¹`, 'info');
}

/**
 * 拟合选中峰
 */
async function fitSelectedPeak() {
    if (selectedPeakIndex < 0 || selectedPeakIndex >= detectedPeaks.length) {
        showToast('请先选择一个峰值', 'warning');
        return;
    }

    const peak = detectedPeaks[selectedPeakIndex];

    try {
        // 使用 bridge_helper 封装的方法
        const result = await apiFitPeak(currentSpectrum, { index: peak.position }, 'gaussian');

        if (result.success) {
            showFitResult(result.data);
            addLog(`峰值拟合成功：R²=${result.data.r_squared.toFixed(4)}`, 'success');
        } else {
            showToast(`拟合失败：${result.error}`, 'error');
        }
    } catch (error) {
        addLog(`拟合异常：${error.message}`, 'error');
        showToast('拟合失败', 'error');
    }
}

/**
 * 显示拟合结果
 */
function showFitResult(data) {
    const resultDiv = document.getElementById('fit-result');
    resultDiv.style.display = 'block';

    document.getElementById('fit-position').textContent = data.position.toFixed(2);
    document.getElementById('fit-intensity').textContent = data.intensity.toFixed(6);
    document.getElementById('fit-fwhm').textContent = data.fwhm.toFixed(2);
    document.getElementById('fit-area').textContent = data.area.toFixed(2);
    document.getElementById('fit-r2').textContent = data.r_squared.toFixed(4);
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPeaksPage);
} else {
    initPeaksPage();
}
