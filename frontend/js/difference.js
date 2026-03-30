/**
 * 差谱运算 JS 模块
 *
 * 功能:
 * - 加载两个光谱数据
 * - 设置减数系数
 * - 调用后端 API 进行差谱运算
 * - 显示差谱结果和统计信息
 */

// ========== 状态管理 ==========
import {
    initBridge,
    getBackend,
    subtractSpectra as apiSubtractSpectra
} from './bridge_helper.js';

let pythonBackend = null;
let bridgeReady = false;

let spectrum1 = null;  // 参考光谱 (被减数)
let spectrum2 = null;  // 待减光谱 (减数)
let differenceResult = null;  // 差谱结果

let wavelengthData = null;  // 波长数据 (拉曼位移)

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', async () => {
    // 使用统一的桥接初始化
    const ready = await initBridge();
    if (ready) {
        pythonBackend = getBackend();
        bridgeReady = true;
        updateBridgeStatus('ready', '已连接');
    } else {
        updateBridgeStatus('error', '连接失败');
    }
    
    initCharts();
    setupEventListeners();
});

/**
 * 更新桥接状态显示
 */
function updateBridgeStatus(status, text) {
    const statusEl = document.getElementById('bridgeStatus');
    statusEl.className = `status-indicator status-${status}`;
    statusEl.innerHTML = `<span class="dot"></span><span>${text}</span>`;
}

/**
 * 初始化图表
 */
function initCharts() {
    const chartConfig = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    };

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 20, r: 20, b: 40, l: 40 },
        xaxis: {
            title: '拉曼位移 (cm⁻¹)',
            showgrid: true,
            gridcolor: 'rgba(128,128,128,0.2)',
        },
        yaxis: {
            title: '强度 (a.u.)',
            showgrid: true,
            gridcolor: 'rgba(128,128,128,0.2)',
        },
        showlegend: true,
        legend: {
            x: 0,
            y: 1,
            bgcolor: 'rgba(0,0,0,0.5)',
        },
    };

    // 光谱 1 图表
    Plotly.newPlot('spectrum1Chart', [], {
        ...layout,
        title: { text: '参考光谱', font: { size: 14 } },
    }, chartConfig);

    // 光谱 2 图表
    Plotly.newPlot('spectrum2Chart', [], {
        ...layout,
        title: { text: '待减光谱', font: { size: 14 } },
    }, chartConfig);

    // 结果图表
    Plotly.newPlot('resultChart', [], {
        ...layout,
        title: { text: '差谱结果', font: { size: 14 } },
        yaxis: {
            ...layout.yaxis,
            title: '强度差值 (a.u.)',
        },
    }, chartConfig);
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    // 监听后端信号
    if (window.qt && qt.webChannelTransport) {
        // 差谱计算完成信号
        if (pythonBackend && pythonBackend.differenceCalculated) {
            pythonBackend.differenceCalculated.connect((resultJson) => {
                onDifferenceCalculated(JSON.parse(resultJson));
            });
        }
    }
}

// ========== 光谱加载功能 ==========

/**
 * 从文件加载光谱 1
 */
async function loadSpectrum1() {
    try {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv,.txt,.json';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                const data = await parseSpectrumFile(file);
                spectrum1 = data.intensity;
                if (!wavelengthData) {
                    wavelengthData = data.wavelength;
                }
                updateSpectrumInfo('spectrum1Info', file.name, spectrum1.length);
                updateChart('spectrum1Chart', [createTrace(spectrum1, '参考光谱', '#2196F3')]);
            }
        };

        input.click();
    } catch (error) {
        console.error('加载光谱 1 失败:', error);
        alert(`加载失败：${error.message}`);
    }
}

/**
 * 从文件加载光谱 2
 */
async function loadSpectrum2() {
    try {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv,.txt,.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                const data = await parseSpectrumFile(file);
                spectrum2 = data.intensity;
                if (!wavelengthData) {
                    wavelengthData = data.wavelength;
                }
                updateSpectrumInfo('spectrum2Info', file.name, spectrum2.length);
                updateChart('spectrum2Chart', [createTrace(spectrum2, '待减光谱', '#FF5722')]);
            }
        };
        
        input.click();
    } catch (error) {
        console.error('加载光谱 2 失败:', error);
        alert(`加载失败：${error.message}`);
    }
}

/**
 * 从当前数据加载光谱 1
 */
function loadFromCurrent1() {
    // 从 localStorage 或其他地方获取当前数据
    try {
        const currentData = localStorage.getItem('currentSpectrum');
        if (currentData) {
            const data = JSON.parse(currentData);
            spectrum1 = data.intensity || data;
            wavelengthData = data.wavelength || null;
            updateSpectrumInfo('spectrum1Info', '当前数据', spectrum1.length);
            updateChart('spectrum1Chart', [createTrace(spectrum1, '参考光谱', '#2196F3')]);
        } else {
            alert('当前没有可用数据');
        }
    } catch (error) {
        console.error('从当前数据加载失败:', error);
        alert('加载失败：' + error.message);
    }
}

/**
 * 从当前数据加载光谱 2
 */
function loadFromCurrent2() {
    try {
        const currentData = localStorage.getItem('currentSpectrum');
        if (currentData) {
            const data = JSON.parse(currentData);
            spectrum2 = data.intensity || data;
            wavelengthData = data.wavelength || null;
            updateSpectrumInfo('spectrum2Info', '当前数据', spectrum2.length);
            updateChart('spectrum2Chart', [createTrace(spectrum2, '待减光谱', '#FF5722')]);
        } else {
            alert('当前没有可用数据');
        }
    } catch (error) {
        console.error('从当前数据加载失败:', error);
        alert('加载失败：' + error.message);
    }
}

/**
 * 加载演示光谱 1
 */
function loadDemoSpectrum1() {
    const demoData = generateDemoSpectrum(1024, 5, 2.0);
    spectrum1 = demoData.intensity;
    wavelengthData = demoData.wavelength;
    updateSpectrumInfo('spectrum1Info', '演示数据', spectrum1.length);
    updateChart('spectrum1Chart', [createTrace(spectrum1, '参考光谱 (演示)', '#2196F3')]);
}

/**
 * 加载演示光谱 2
 */
function loadDemoSpectrum2() {
    const demoData = generateDemoSpectrum(1024, 3, 1.5);
    spectrum2 = demoData.intensity;
    if (!wavelengthData) {
        wavelengthData = demoData.wavelength;
    }
    updateSpectrumInfo('spectrum2Info', '演示数据', spectrum2.length);
    updateChart('spectrum2Chart', [createTrace(spectrum2, '待减光谱 (演示)', '#FF5722')]);
}

/**
 * 生成演示光谱数据
 */
function generateDemoSpectrum(points, peakCount, noiseLevel) {
    const wavelength = Array.from({ length: points }, (_, i) => 200 + (i / points) * 3000);
    const intensity = new Array(points).fill(0);
    
    // 添加基线
    for (let i = 0; i < points; i++) {
        intensity[i] += 100 + 50 * Math.sin(i / points * Math.PI);
    }
    
    // 添加随机峰
    for (let p = 0; p < peakCount; p++) {
        const center = Math.floor(Math.random() * points);
        const height = 200 + Math.random() * 300;
        const width = 20 + Math.random() * 30;
        
        for (let i = 0; i < points; i++) {
            const dist = (i - center) ** 2;
            intensity[i] += height * Math.exp(-dist / (2 * width ** 2));
        }
    }
    
    // 添加噪声
    for (let i = 0; i < points; i++) {
        intensity[i] += (Math.random() - 0.5) * noiseLevel * 20;
    }
    
    return { wavelength, intensity };
}

/**
 * 解析光谱文件
 */
async function parseSpectrumFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            try {
                const content = e.target.result;
                const lines = content.trim().split('\n');
                
                const wavelength = [];
                const intensity = [];
                
                for (const line of lines) {
                    if (line.trim().startsWith('#') || line.trim() === '') continue;
                    
                    const parts = line.split(/[,\t\s]+/);
                    if (parts.length >= 2) {
                        wavelength.push(parseFloat(parts[0]));
                        intensity.push(parseFloat(parts[1]));
                    }
                }
                
                resolve({ wavelength, intensity });
            } catch (error) {
                reject(error);
            }
        };
        
        reader.onerror = () => reject(new Error('文件读取失败'));
        reader.readAsText(file);
    });
}

/**
 * 更新光谱信息
 */
function updateSpectrumInfo(elementId, filename, points) {
    const el = document.getElementById(elementId);
    el.innerHTML = `
        <span class="status-ready">
            <span class="dot"></span>
            ${filename} (${points} 点)
        </span>
    `;
}

/**
 * 更新图表
 */
function updateChart(chartId, traces) {
    if (wavelengthData) {
        traces.forEach(trace => {
            trace.x = wavelengthData.slice(0, trace.y.length);
        });
    }
    Plotly.react(chartId, traces);
}

/**
 * 创建图表轨迹
 */
function createTrace(data, name, color) {
    return {
        y: data,
        name: name,
        type: 'scatter',
        mode: 'lines',
        line: { color: color, width: 1.5 },
    };
}

// ========== 差谱计算功能 ==========

/**
 * 计算差谱
 */
async function calculateDifference() {
    if (!spectrum1 || !spectrum2) {
        alert('请先加载两个光谱数据');
        return;
    }
    
    if (spectrum1.length !== spectrum2.length) {
        alert(`光谱维度不匹配：${spectrum1.length} vs ${spectrum2.length}`);
        return;
    }
    
    const coefficient = parseFloat(document.getElementById('coefficientValue').value);

    const calculateBtn = document.getElementById('calculateBtn');
    calculateBtn.disabled = true;
    calculateBtn.innerHTML = '⏳ 计算中...';

    try {
        // 使用 bridge_helper 封装的方法
        const result = await apiSubtractSpectra(spectrum1, spectrum2, coefficient);

        if (result.success) {
            differenceResult = result.data.difference;
            displayDifferenceResult(result.data);
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('差谱计算失败:', error);
        alert(`计算失败：${error.message}`);
    } finally {
        calculateBtn.disabled = false;
        calculateBtn.innerHTML = '🚀 开始计算';
    }
}

/**
 * 显示差谱结果
 */
function displayDifferenceResult(data) {
    const { difference, coefficient } = data;
    
    // 更新图表
    const resultTrace = createTrace(difference, `差谱 (k=${coefficient})`, '#4CAF50');
    updateChart('resultChart', [resultTrace]);
    
    // 计算统计信息
    const stats = calculateStatistics(difference);
    
    // 显示统计面板
    document.getElementById('resultStats').style.display = 'grid';
    document.getElementById('statMax').textContent = stats.max.toFixed(4);
    document.getElementById('statMin').textContent = stats.min.toFixed(4);
    document.getElementById('statMean').textContent = stats.mean.toFixed(4);
    document.getElementById('statStd').textContent = stats.std.toFixed(4);
    document.getElementById('statPoints').textContent = stats.points;
    
    // 启用导出按钮
    document.getElementById('exportBtn').disabled = false;
}

/**
 * 计算统计信息
 */
function calculateStatistics(data) {
    const n = data.length;
    const sum = data.reduce((a, b) => a + b, 0);
    const mean = sum / n;
    const variance = data.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
    
    return {
        max: Math.max(...data),
        min: Math.min(...data),
        mean: mean,
        std: Math.sqrt(variance),
        points: n,
    };
}

/**
 * 导出差谱结果
 */
function exportDifference() {
    if (!differenceResult) {
        alert('没有可导出的结果');
        return;
    }
    
    const coefficient = document.getElementById('coefficientValue').value;
    
    // 生成 CSV 内容
    let csv = 'Wavelength,Spectrum1,Spectrum2,Difference\n';
    for (let i = 0; i < differenceResult.length; i++) {
        const wl = wavelengthData ? wavelengthData[i] : i;
        csv += `${wl},${spectrum1[i]},${spectrum2[i]},${differenceResult[i]}\n`;
    }
    
    // 创建下载链接
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `difference_k${coefficient}_${new Date().getTime()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * 清空全部
 */
function clearAll() {
    spectrum1 = null;
    spectrum2 = null;
    differenceResult = null;
    
    document.getElementById('spectrum1Info').innerHTML = `
        <span class="status-empty">
            <span class="dot"></span>
            未加载光谱
        </span>
    `;
    document.getElementById('spectrum2Info').innerHTML = `
        <span class="status-empty">
            <span class="dot"></span>
            未加载光谱
        </span>
    `;
    
    Plotly.react('spectrum1Chart', []);
    Plotly.react('spectrum2Chart', []);
    Plotly.react('resultChart', []);
    
    document.getElementById('resultStats').style.display = 'none';
    document.getElementById('exportBtn').disabled = true;
}

// ========== 全局导出（供 HTML onclick 调用） ==========
// 确保在 DOM 加载完成后暴露到 window
function mountToWindow() {
    window.loadSpectrum1 = loadSpectrum1;
    window.loadSpectrum2 = loadSpectrum2;
    window.loadFromCurrent1 = loadFromCurrent1;
    window.loadFromCurrent2 = loadFromCurrent2;
    window.loadDemoSpectrum1 = loadDemoSpectrum1;
    window.loadDemoSpectrum2 = loadDemoSpectrum2;
    window.calculateDifference = calculateDifference;
    window.exportDifference = exportDifference;
    window.clearAll = clearAll;
    console.log('[Difference] 函数已挂载到 window');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountToWindow);
} else {
    mountToWindow();
}
