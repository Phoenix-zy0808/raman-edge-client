/**
 * 特征可视化页面 - 前端逻辑
 * @module features
 */

let boxplotChart = null;
let correlationChart = null;
let importanceChart = null;
let pcaScatterChart = null;

/**
 * 初始化特征可视化页面
 */
export function initFeaturesPage() {
    console.log('[Features] 初始化特征可视化页面');

    // 初始化图表
    initCharts();

    // 设置事件监听
    setupEventListeners();

    // 加载默认数据
    loadFeatureData('all');
}

/**
 * 初始化所有图表
 */
function initCharts() {
    const boxplotEl = document.getElementById('feature-boxplot');
    const correlationEl = document.getElementById('correlation-heatmap');
    const importanceEl = document.getElementById('feature-importance-bar');
    const pcaEl = document.getElementById('pca-2d-scatter');

    if (boxplotEl && typeof echarts !== 'undefined') {
        boxplotChart = echarts.init(boxplotEl);
    }
    if (correlationEl && typeof echarts !== 'undefined') {
        correlationChart = echarts.init(correlationEl);
    }
    if (importanceEl && typeof echarts !== 'undefined') {
        importanceChart = echarts.init(importanceEl);
    }
    if (pcaEl && typeof echarts !== 'undefined') {
        pcaScatterChart = echarts.init(pcaEl);
    }

    // 响应式调整
    window.addEventListener('resize', () => {
        boxplotChart?.resize();
        correlationChart?.resize();
        importanceChart?.resize();
        pcaScatterChart?.resize();
    });
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    const btnUpdate = document.getElementById('btn-update-features');
    const featureTypeSelect = document.getElementById('feature-type');

    if (btnUpdate) {
        btnUpdate.addEventListener('click', () => {
            const type = featureTypeSelect?.value || 'all';
            loadFeatureData(type);
        });
    }

    if (featureTypeSelect) {
        featureTypeSelect.addEventListener('change', () => {
            const type = featureTypeSelect.value;
            loadFeatureData(type);
        });
    }
}

/**
 * 加载特征数据
 */
function loadFeatureData(type) {
    console.log('[Features] 加载特征数据:', type);

    // 根据类型加载不同数据
    switch (type) {
        case 'all':
            loadBoxplotData();
            loadCorrelationData();
            loadImportanceData();
            loadPCAScatterData();
            break;
        case 'selected':
            loadBoxplotData(true);
            loadCorrelationData(true);
            loadImportanceData();
            loadPCAScatterData(true);
            break;
        case 'peak_position':
            loadPeakPositionData();
            break;
        case 'peak_intensity':
            loadPeakIntensityData();
            break;
        case 'peak_width':
            loadPeakWidthData();
            break;
        case 'intensity_ratio':
            loadIntensityRatioData();
            break;
        case 'global':
            loadGlobalFeatureData();
            break;
    }
}

/**
 * 加载箱线图数据
 */
function loadBoxplotData(selected = false) {
    if (!boxplotChart) return;

    const categories = ['金刚石', '石英', '方解石', '刚玉', '长石', '橄榄石', '石墨', '硅'];
    const features = selected ?
        ['石英_464 强度', '石英_1082 强度', '金刚石_1332 强度', '方解石_1086 强度', '光谱重心'] :
        ['峰位置_1', '峰位置_2', '峰位置_3', '峰强度_1', '峰强度_2', '峰宽度_1', '强度比_1', '全局_1'];

    // 生成示例箱线图数据
    const data = features.map((feature, i) => {
        return categories.map((_, j) => {
            const min = Math.random() * 20;
            const q1 = min + Math.random() * 30;
            const median = q1 + Math.random() * 20;
            const q3 = median + Math.random() * 20;
            const max = q3 + Math.random() * 20;
            return [min, q1, median, q3, max];
        });
    });

    boxplotChart.setOption({
        title: {
            text: '特征分布箱线图',
            textStyle: { color: '#fff' }
        },
        tooltip: {
            trigger: 'item',
            axisPointer: { type: 'shadow' }
        },
        grid: { left: '10%', right: '10%', top: '15%', bottom: '15%' },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: { color: '#aaa', rotate: 45 }
        },
        yAxis: {
            type: 'value',
            name: '特征值',
            axisLabel: { color: '#aaa' }
        },
        series: [{
            name: '箱线图',
            type: 'boxplot',
            data: data,
            itemStyle: {
                color: '#00d9ff',
                borderColor: '#00ff88'
            }
        }]
    });
}

/**
 * 加载相关性矩阵数据
 */
function loadCorrelationData(selected = false) {
    if (!correlationChart) return;

    const features = selected ?
        ['石英_464 强度', '石英_1082 强度', '金刚石_1332', '方解石_1086', '光谱重心', '曲线下面积', 'I_1082/I_464'] :
        ['峰位置_1', '峰位置_2', '峰位置_3', '峰强度_1', '峰强度_2', '峰宽度_1', '峰宽度_2', '强度比_1', '强度比_2', '全局_1'];

    // 生成示例相关性矩阵
    const n = features.length;
    const data = [];
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            let correlation;
            if (i === j) {
                correlation = 1;
            } else if (Math.abs(i - j) === 1 && i % 2 === 0) {
                correlation = 0.7 + Math.random() * 0.25; // 相邻特征可能高度相关
            } else {
                correlation = (Math.random() - 0.5) * 0.6; // 其他随机相关
            }
            data.push([j, i, correlation.toFixed(2)]);
        }
    }

    correlationChart.setOption({
        title: {
            text: '特征相关性热力图',
            textStyle: { color: '#fff' }
        },
        tooltip: {
            position: 'top',
            formatter: (params) => {
                return `${features[params.data[1]]} ↔ ${features[params.data[0]]}<br/>相关系数：${params.data[2]}`;
            }
        },
        grid: { left: '15%', right: '15%', top: '10%', bottom: '15%' },
        xAxis: {
            type: 'category',
            data: features.map(f => f.length > 6 ? f.substring(0, 6) + '...' : f),
            axisLabel: { color: '#aaa', rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'category',
            data: features.map(f => f.length > 6 ? f.substring(0, 6) + '...' : f),
            axisLabel: { color: '#aaa', fontSize: 10 }
        },
        visualMap: {
            min: -1,
            max: 1,
            calculable: false,
            orient: 'horizontal',
            right: '10%',
            top: '5%',
            inRange: {
                color: ['#0066ff', '#1a1a2e', '#ff6600']
            },
            textStyle: { color: '#aaa' }
        },
        series: [{
            type: 'heatmap',
            data: data,
            label: {
                show: true,
                color: '#fff',
                fontSize: 9
            }
        }]
    });
}

/**
 * 加载特征重要性数据
 */
function loadImportanceData() {
    if (!importanceChart) return;

    const features = [
        '光谱峰度', '光谱偏度', '光谱重心', '曲线下面积', '光谱斜率',
        'I_1082/I_464', '石英_1082 宽度', '石英_464 宽度',
        '石英_1082 强度', '石英_464 强度'
    ].reverse();

    const importances = [0.02, 0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.25, 0.35];

    importanceChart.setOption({
        title: {
            text: '随机森林特征重要性',
            textStyle: { color: '#fff' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        grid: { left: '3%', right: '10%', top: '15%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'value',
            name: '重要性',
            axisLabel: { color: '#aaa' }
        },
        yAxis: {
            type: 'category',
            data: features,
            axisLabel: { color: '#fff', fontSize: 11 }
        },
        series: [{
            type: 'bar',
            data: importances,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#1a1a2e' },
                    { offset: 1, color: '#00d9ff' }
                ])
            },
            label: {
                show: true,
                position: 'right',
                color: '#fff',
                formatter: '{c}'
            }
        }]
    });
}

/**
 * 加载 PCA 散点图数据
 */
function loadPCAScatterData(selected = false) {
    if (!pcaScatterChart) return;

    const categories = ['金刚石', '石英', '方解石', '刚玉', '长石', '橄榄石', '石墨', '硅'];
    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ff8800', '#8800ff'];

    // 生成示例 PCA 散点数据
    const data = categories.map((cat, catIdx) => {
        const centerX = (catIdx % 4) * 2 - 3;
        const centerY = Math.floor(catIdx / 4) * 2 - 1;
        return Array.from({ length: 20 }, () => [
            centerX + (Math.random() - 0.5) * 1.5,
            centerY + (Math.random() - 0.5) * 1.5
        ]);
    });

    const series = categories.map((cat, idx) => ({
        name: cat,
        type: 'scatter',
        data: data[idx],
        itemStyle: { color: colors[idx] }
    }));

    pcaScatterChart.setOption({
        title: {
            text: 'PCA 降维可视化（2D）',
            textStyle: { color: '#fff' }
        },
        tooltip: {
            trigger: 'item',
            formatter: (params) => {
                return `${params.seriesName}<br/>PC1: ${params.data[0].toFixed(2)}<br/>PC2: ${params.data[1].toFixed(2)}`;
            }
        },
        legend: {
            data: categories,
            textStyle: { color: '#aaa' },
            bottom: '5%'
        },
        grid: { left: '10%', right: '10%', top: '15%', bottom: '20%' },
        xAxis: {
            name: 'PC1',
            type: 'value',
            axisLabel: { color: '#aaa' }
        },
        yAxis: {
            name: 'PC2',
            type: 'value',
            axisLabel: { color: '#aaa' }
        },
        series: series
    });
}

// 占位函数（特定特征类型）
function loadPeakPositionData() { loadBoxplotData(); }
function loadPeakIntensityData() { loadBoxplotData(); }
function loadPeakWidthData() { loadBoxplotData(); }
function loadIntensityRatioData() { loadBoxplotData(); }
function loadGlobalFeatureData() { loadBoxplotData(); }

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFeaturesPage);
} else {
    initFeaturesPage();
}

export default { initFeaturesPage };
