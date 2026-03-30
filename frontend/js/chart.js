/**
 * 拉曼光谱边缘客户端 - ECharts 图表渲染模块
 * @module chart
 */

import { addLog } from './utils.js';

/** @type {any} ECharts 图表实例 */
let chart = null;

/** @type {number[]} 波长数据数组 (cm^-1) */
let wavelengthData = [];

/** @type {boolean} 是否显示峰值标注 */
let showPeakLabels = true;

/** @type {Array<{name: string, data: number[], color: string}>} 历史光谱数据 */
let historySpectra = [];

/** @type {boolean} 是否显示多光谱对比 */
let showMultiSpectrum = false;

/** @type {string[]} 光谱颜色列表 */
const SPECTRUM_COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#00BCD4'];

/**
 * 光谱仪配置常量
 * @constant
 */
const SPECTROMETER_CONFIG = {
    WAVELENGTH_MIN: 200,      // cm⁻¹ 最小波长
    WAVELENGTH_MAX: 3200,     // cm⁻¹ 最大波长
    DATA_POINTS: 1024         // 数据点数
};

// 特征峰位置（与后端谱库 backend/library/*.json 保持一致）
// 数据来源：后端谱库标准物质特征峰
const PEAK_POSITIONS = [
    // 硅 (silicon.json)
    { position: 520, label: 'Si', intensity: 1.0, source: 'silicon' },
    { position: 302, label: 'Si (2TA)', intensity: 0.15, source: 'silicon' },
    { position: 435, label: 'Si (TO+LA)', intensity: 0.08, source: 'silicon' },
    { position: 620, label: 'Si (2TO)', intensity: 0.05, source: 'silicon' },
    // 金刚石 (diamond.json)
    { position: 1332, label: 'Diamond', intensity: 1.0, source: 'diamond' },
    // 石墨/石墨烯 (graphite.json, graphene.json)
    { position: 1580, label: 'G 峰', intensity: 0.8, source: 'graphite' },
    { position: 2700, label: '2D 峰', intensity: 0.6, source: 'graphite' },
    // 二氧化钛 (tio2.json)
    { position: 144, label: 'TiO₂', intensity: 0.7, source: 'tio2' },
    { position: 399, label: 'TiO₂', intensity: 0.5, source: 'tio2' },
    { position: 516, label: 'TiO₂', intensity: 0.4, source: 'tio2' },
    // 氧化锌 (zno.json)
    { position: 437, label: 'ZnO', intensity: 0.8, source: 'zno' },
    // 碳酸钙 (caco3.json)
    { position: 1086, label: 'CaCO₃', intensity: 0.9, source: 'caco3' },
    // 苯 (benzene.json)
    { position: 992, label: 'C₆H₆', intensity: 0.7, source: 'benzene' },
    // 氧化铝 (al2o3.json)
    { position: 418, label: 'Al₂O₃', intensity: 0.6, source: 'al2o3' },
    // 碳纳米管 (carbon_nanotube.json)
    { position: 1590, label: 'CNT G', intensity: 0.8, source: 'cnt' },
    { position: 1350, label: 'CNT D', intensity: 0.5, source: 'cnt' }
];

/**
 * 获取峰值数据（供外部模块使用）
 * @returns {Array} 峰值位置数组
 */
export function getPeakPositions() {
    return [...PEAK_POSITIONS];
}

/**
 * 初始化 ECharts 图表
 * @returns {any} ECharts 实例
 */
export function initChart() {
    if (!document.getElementById('spectrum-chart')) {
        addLog('图表容器不存在', 'error');
        return null;
    }

    chart = echarts.init(document.getElementById('spectrum-chart'));

    // 生成波长数据 (200-3200 cm⁻¹)
    wavelengthData = [];
    for (let i = 0; i < SPECTROMETER_CONFIG.DATA_POINTS; i++) {
        wavelengthData.push(
            SPECTROMETER_CONFIG.WAVELENGTH_MIN + 
            (SPECTROMETER_CONFIG.WAVELENGTH_MAX - SPECTROMETER_CONFIG.WAVELENGTH_MIN) * i / (SPECTROMETER_CONFIG.DATA_POINTS - 1)
        );
    }

    const option = {
        backgroundColor: '#1E1E1E',
        grid: {
            left: '50px',
            right: '20px',
            bottom: '40px',
            top: '20px'
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                let text = `拉曼位移：${params[0].value[0].toFixed(1)} cm⁻¹<br/>`;
                params.forEach(param => {
                    if (param.seriesName !== '特征峰') {
                        text += `<span style="color:${param.color}">${param.seriesName}: ${param.value[1].toFixed(4)}</span><br/>`;
                    }
                });
                if (params.find(p => p.seriesName === '特征峰')) {
                    const peakParam = params.find(p => p.seriesName === '特征峰');
                    if (peakParam && peakParam.name) {
                        text += `<br/><span style="color:#FF9800">${peakParam.name}</span>`;
                    }
                }
                return text;
            }
        },
        xAxis: {
            type: 'value',
            name: '拉曼位移 (cm⁻¹)',
            nameTextStyle: { color: '#999' },
            axisLine: { lineStyle: { color: '#666' } },
            axisLabel: { color: '#999' },
            splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
        },
        yAxis: {
            type: 'value',
            name: '强度 (a.u.)',
            nameTextStyle: { color: '#999' },
            axisLine: { lineStyle: { color: '#666' } },
            axisLabel: { color: '#999' },
            splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
        },
        series: [
            {
                name: '光谱',
                type: 'line',
                data: new Array(1024).fill(0).map((v, i) => [wavelengthData[i], v]),
                lineStyle: { color: '#2196F3', width: 1.5 },
                symbol: 'none',
                areaStyle: {
                    color: 'rgba(33, 150, 243, 0.1)'
                }
            },
            {
                name: '特征峰',
                type: 'scatter',
                symbol: 'pin',
                symbolSize: 10,
                data: showPeakLabels ? PEAK_POSITIONS.map(peak => ({
                    value: [peak.position, 0.1 + peak.intensity * 0.3],
                    name: peak.label
                })) : [],
                label: {
                    show: true,
                    position: 'top',
                    color: '#FF9800',
                    fontSize: 10,
                    formatter: '{b}'
                },
                itemStyle: { color: '#FF9800' },
                tooltip: { show: false }
            }
        ]
    };

    chart.setOption(option);
    addLog('图表初始化完成', 'info');
    return chart;
}

/**
 * 获取图表实例
 * @returns {any}
 */
export function getChart() {
    return chart;
}

/**
 * 获取波长数据
 * @returns {number[]}
 */
export function getWavelengthData() {
    return wavelengthData;
}

/**
 * 更新光谱数据
 * @param {number[]} spectrumData - 光谱强度数据
 * @param {number[]} [wavenumbers] - 可选的波数数据
 */
export function updateSpectrum(spectrumData, wavenumbers) {
    if (!chart) {
        console.error('[Chart] 图表未初始化');
        return;
    }

    if (!spectrumData || spectrumData.length === 0) {
        console.error('[Chart] 光谱数据为空');
        return;
    }

    // 如果提供了 wavenumbers，更新 wavelengthData
    if (wavenumbers && wavenumbers.length > 0) {
        wavelengthData = wavenumbers;
    }

    // 如果 wavelengthData 仍然为空，生成默认值
    if (!wavelengthData || wavelengthData.length === 0) {
        wavelengthData = Array.from({ length: spectrumData.length }, (_, i) => 200 + i * 2.93);
        console.warn('[Chart] 使用默认波长数据');
    }

    // 构建多光谱系列
    const series = [];

    // 添加当前光谱
    const chartData = spectrumData.map((v, i) => [wavelengthData[i], v]);
    series.push({
        name: '当前光谱',
        type: 'line',
        data: chartData,
        lineStyle: { color: '#00d9ff', width: 1.5 },
        symbol: 'none',
        areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                offset: 0, color: 'rgba(0, 217, 255, 0.3)'
            }, { offset: 1, color: 'rgba(0, 217, 255, 0)' }])
        }
    });

    // 添加历史光谱对比
    if (showMultiSpectrum && historySpectra.length > 0) {
        historySpectra.forEach((hist) => {
            const histData = hist.data.map((v, i) => [wavelengthData[i], v]);
            series.push({
                name: hist.name,
                type: 'line',
                data: histData,
                lineStyle: { color: hist.color, width: 1.5, type: 'dashed' },
                symbol: 'none'
            });
        });
    }

    // 添加峰值标注
    series.push({
        name: '特征峰',
        type: 'scatter',
        symbol: 'pin',
        symbolSize: 10,
        data: showPeakLabels ? PEAK_POSITIONS.map(peak => ({
            value: [peak.position, 0.1 + peak.intensity * 0.3],
            name: peak.label
        })) : [],
        label: {
            show: true,
            position: 'top',
            color: '#ffaa00',
            fontSize: 10,
            formatter: '{b}'
        },
        itemStyle: { color: '#ffaa00' },
        tooltip: { show: false }
    });

    chart.setOption({ series }, true);
}

/**
 * 添加光谱到历史对比
 * @param {number[]} spectrumData - 光谱数据
 * @param {string} name - 光谱名称
 * @returns {boolean} 是否添加成功
 */
export function addToHistory(spectrumData, name = null) {
    if (!spectrumData || spectrumData.length === 0) {
        return false;
    }

    if (historySpectra.length >= 5) {
        return false;
    }

    const timestamp = new Date().toLocaleTimeString();
    const spectrumName = name || `历史光谱 ${historySpectra.length + 1} (${timestamp})`;
    const color = SPECTRUM_COLORS[historySpectra.length % SPECTRUM_COLORS.length];

    historySpectra.push({
        name: spectrumName,
        data: [...spectrumData],
        color: color
    });

    updateSpectrum(spectrumData);
    return true;
}

/**
 * 清除历史光谱
 */
export function clearHistory() {
    historySpectra = [];
    if (chart) {
        updateSpectrum(new Array(SPECTROMETER_CONFIG.DATA_POINTS).fill(0));
    }
}

/**
 * 获取历史光谱数量
 * @returns {number}
 */
export function getHistoryCount() {
    return historySpectra.length;
}

/**
 * 切换多光谱对比模式
 * @returns {boolean} 新的状态
 */
export function toggleMultiSpectrum() {
    showMultiSpectrum = !showMultiSpectrum;
    return showMultiSpectrum;
}

/**
 * 获取多光谱对比状态
 * @returns {boolean}
 */
export function isMultiSpectrumEnabled() {
    return showMultiSpectrum;
}

/**
 * 切换峰值标注
 * @returns {boolean} 新的状态
 */
export function togglePeakLabels() {
    showPeakLabels = !showPeakLabels;
    
    if (chart) {
        chart.setOption({
            series: [{
                name: '特征峰',
                data: showPeakLabels ? PEAK_POSITIONS.map(peak => ({
                    value: [peak.position, 0.1 + peak.intensity * 0.3],
                    name: peak.label
                })) : []
            }]
        }, true);
    }
    
    return showPeakLabels;
}

/**
 * 获取峰值标注状态
 * @returns {boolean}
 */
export function isPeakLabelsEnabled() {
    return showPeakLabels;
}

/**
 * 更新图表主题
 * @param {'dark'|'light'} theme - 主题
 */
export function updateChartTheme(theme) {
    if (!chart) return;

    const textColor = theme === 'dark' ? '#aaa' : '#666';
    const lineColor = theme === 'dark' ? '#00d9ff' : '#0099cc';
    const gridColor = theme === 'dark' ? '#222' : '#e0e0e0';

    chart.setOption({
        title: { textStyle: { color: theme === 'dark' ? '#00d9ff' : '#0099cc' } },
        xAxis: {
            nameTextStyle: { color: textColor },
            axisLine: { lineStyle: { color: theme === 'dark' ? '#333' : '#ccc' } },
            axisLabel: { color: textColor },
            splitLine: { lineStyle: { color: gridColor } }
        },
        yAxis: {
            nameTextStyle: { color: textColor },
            axisLine: { lineStyle: { color: theme === 'dark' ? '#333' : '#ccc' } },
            axisLabel: { color: textColor },
            splitLine: { lineStyle: { color: gridColor } }
        },
        series: [{
            lineStyle: { color: lineColor },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0, color: theme === 'dark' ? 'rgba(0, 217, 255, 0.3)' : 'rgba(0, 153, 204, 0.3)'
                }, { offset: 1, color: 'rgba(0, 0, 0, 0)' }])
            }
        }]
    });
}

/**
 * 调整图表大小
 */
export function resizeChart() {
    if (chart) {
        chart.resize();
    }
}
