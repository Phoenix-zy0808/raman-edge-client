/**
 * 模型对比页面 - 前端逻辑
 * @module comparison
 */

import { bridge } from '../bridge.js';

let accuracyBarChart = null;
let inferenceTimeChart = null;
let rfConfusionChart = null;
let tfConfusionChart = null;
let featureImportanceChart = null;
let attentionHeatmapChart = null;

/**
 * 初始化对比页面
 */
export function initComparisonPage() {
    console.log('[Comparison] 初始化对比页面');

    // 初始化所有图表
    initCharts();

    // 填充示例数据（实际应该从后端 API 获取）
    loadComparisonData();

    // 窗口大小调整
    window.addEventListener('resize', () => {
        accuracyBarChart?.resize();
        inferenceTimeChart?.resize();
        rfConfusionChart?.resize();
        tfConfusionChart?.resize();
        featureImportanceChart?.resize();
        attentionHeatmapChart?.resize();
    });
}

/**
 * 初始化所有图表
 */
function initCharts() {
    initAccuracyBarChart();
    initInferenceTimeChart();
    initConfusionMatrices();
    initFeatureImportanceChart();
    initAttentionHeatmap();
}

/**
 * 初始化准确率柱状图
 */
function initAccuracyBarChart() {
    const el = document.getElementById('accuracy-bar-chart');
    if (!el || typeof echarts === 'undefined') return;

    accuracyBarChart = echarts.init(el);
    accuracyBarChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: ['训练集', '验证集', '测试集'], textStyle: { color: '#aaa' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'value',
            max: 100,
            axisLabel: { color: '#aaa', formatter: '{value}%' }
        },
        yAxis: {
            type: 'category',
            data: ['随机森林', 'Transformer'],
            axisLabel: { color: '#fff' }
        },
        series: [
            {
                name: '训练集',
                type: 'bar',
                data: [100, 98],
                itemStyle: { color: '#00d9ff' }
            },
            {
                name: '验证集',
                type: 'bar',
                data: [85, 92],
                itemStyle: { color: '#00ff88' }
            },
            {
                name: '测试集',
                type: 'bar',
                data: [83, 90],
                itemStyle: { color: '#ffaa00' }
            }
        ]
    });
}

/**
 * 初始化推理时间图表
 */
function initInferenceTimeChart() {
    const el = document.getElementById('inference-time-chart');
    if (!el || typeof echarts === 'undefined') return;

    inferenceTimeChart = echarts.init(el);
    inferenceTimeChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: ['随机森林', 'Transformer'],
            axisLabel: { color: '#fff' }
        },
        yAxis: {
            type: 'value',
            name: '时间 (ms)',
            axisLabel: { color: '#aaa' }
        },
        series: [{
            type: 'bar',
            data: [35, 85],
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#00d9ff' },
                    { offset: 1, color: '#0066ff' }
                ])
            },
            label: {
                show: true,
                position: 'top',
                color: '#fff',
                formatter: '{c}ms'
            }
        }]
    });
}

/**
 * 初始化混淆矩阵
 */
function initConfusionMatrices() {
    // 随机森林混淆矩阵
    const rfEl = document.getElementById('rf-confusion-matrix');
    if (rfEl && typeof echarts !== 'undefined') {
        rfConfusionChart = echarts.init(rfEl);
        rfConfusionChart.setOption({
            tooltip: { position: 'top' },
            grid: { left: '10%', right: '10%', top: '10%', bottom: '20%' },
            xAxis: {
                type: 'category',
                data: ['金刚石', '石英', '方解石', '刚玉', '长石'],
                axisLabel: { color: '#aaa', rotate: 45 }
            },
            yAxis: {
                type: 'category',
                data: ['金刚石', '石英', '方解石', '刚玉', '长石'],
                axisLabel: { color: '#aaa' }
            },
            visualMap: {
                min: 0,
                max: 100,
                calculable: false,
                orient: 'horizontal',
                right: '10%',
                top: '5%',
                inRange: { color: ['#1a1a2e', '#00d9ff', '#00ff88'] },
                textStyle: { color: '#aaa' }
            },
            series: [{
                type: 'heatmap',
                data: [
                    [0, 0, 95], [1, 0, 3], [2, 0, 1], [3, 0, 1], [4, 0, 0],
                    [0, 1, 2], [1, 1, 93], [2, 1, 3], [3, 1, 1], [4, 1, 1],
                    [0, 2, 1], [1, 2, 4], [2, 2, 92], [3, 2, 2], [4, 2, 1],
                    [0, 3, 2], [1, 3, 2], [2, 3, 3], [3, 3, 90], [4, 3, 3],
                    [0, 4, 1], [1, 4, 3], [2, 4, 2], [3, 4, 4], [4, 4, 90]
                ].map(item => [item[1], item[0], item[2] || '-']),
                label: { show: true, color: '#fff' }
            }]
        });
    }

    // Transformer 混淆矩阵
    const tfEl = document.getElementById('tf-confusion-matrix');
    if (tfEl && typeof echarts !== 'undefined') {
        tfConfusionChart = echarts.init(tfEl);
        tfConfusionChart.setOption({
            tooltip: { position: 'top' },
            grid: { left: '10%', right: '10%', top: '10%', bottom: '20%' },
            xAxis: {
                type: 'category',
                data: ['金刚石', '石英', '方解石', '刚玉', '长石'],
                axisLabel: { color: '#aaa', rotate: 45 }
            },
            yAxis: {
                type: 'category',
                data: ['金刚石', '石英', '方解石', '刚玉', '长石'],
                axisLabel: { color: '#aaa' }
            },
            visualMap: {
                min: 0,
                max: 100,
                calculable: false,
                orient: 'horizontal',
                right: '10%',
                top: '5%',
                inRange: { color: ['#1a1a2e', '#00d9ff', '#00ff88'] },
                textStyle: { color: '#aaa' }
            },
            series: [{
                type: 'heatmap',
                data: [
                    [0, 0, 98], [1, 0, 1], [2, 0, 0], [3, 0, 1], [4, 0, 0],
                    [0, 1, 1], [1, 1, 97], [2, 1, 1], [3, 1, 0], [4, 1, 1],
                    [0, 2, 0], [1, 2, 2], [2, 2, 96], [3, 2, 1], [4, 2, 1],
                    [0, 3, 1], [1, 3, 1], [2, 3, 1], [3, 3, 95], [4, 3, 2],
                    [0, 4, 0], [1, 4, 2], [2, 4, 1], [3, 4, 2], [4, 4, 95]
                ].map(item => [item[1], item[0], item[2] || '-']),
                label: { show: true, color: '#fff' }
            }]
        });
    }
}

/**
 * 初始化特征重要性图表
 */
function initFeatureImportanceChart() {
    const el = document.getElementById('feature-importance-chart');
    if (!el || typeof echarts === 'undefined') return;

    featureImportanceChart = echarts.init(el);
    featureImportanceChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '10%', top: '3%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'value',
            axisLabel: { color: '#aaa', formatter: '{value}' }
        },
        yAxis: {
            type: 'category',
            data: [
                '光谱峰度', '光谱偏度', '光谱重心', '曲线下面积', '光谱斜率',
                'I_1082/I_464', '石英_1082 宽度', '石英_464 宽度',
                '石英_1082 强度', '石英_464 强度'
            ].reverse(),
            axisLabel: { color: '#fff', fontSize: 11 }
        },
        series: [{
            type: 'bar',
            data: [0.02, 0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.25, 0.35],
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
 * 初始化注意力权重热力图
 */
function initAttentionHeatmap() {
    const el = document.getElementById('attention-heatmap');
    if (!el || typeof echarts === 'undefined') return;

    attentionHeatmapChart = echarts.init(el);

    // 生成示例注意力权重数据
    const wavenumbers = Array.from({ length: 64 }, (_, i) => 200 + i * 46.875);
    const attentionData = [];

    for (let i = 0; i < 64; i++) {
        for (let j = 0; j < 64; j++) {
            // 模拟注意力权重（对角线 + 特征峰位置高权重）
            let value = Math.exp(-Math.abs(i - j) / 10) * 0.5;
            if (i >= 5 && i <= 10 && j >= 5 && j <= 10) value += 0.3; // 模拟 464 cm⁻¹
            if (i >= 20 && i <= 25 && j >= 20 && j <= 25) value += 0.4; // 模拟 1082 cm⁻¹
            if (i >= 30 && i <= 35 && j >= 30 && j <= 35) value += 0.5; // 模拟 1332 cm⁻¹
            attentionData.push([i, j, Math.min(value, 1)]);
        }
    }

    attentionHeatmapChart.setOption({
        tooltip: {
            position: 'top',
            formatter: (params) => {
                const wn1 = wavenumbers[params.data[0]]?.toFixed(0) || 0;
                const wn2 = wavenumbers[params.data[1]]?.toFixed(0) || 0;
                return `${wn1} cm⁻¹ ↔ ${wn2} cm⁻¹<br/>注意力：${params.data[2].toFixed(3)}`;
            }
        },
        grid: { left: '10%', right: '10%', top: '10%', bottom: '15%' },
        xAxis: {
            type: 'category',
            data: wavenumbers.map((wn, i) => i % 8 === 0 ? wn.toFixed(0) : ''),
            axisLabel: { color: '#aaa', rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'category',
            data: wavenumbers.map((wn, i) => i % 8 === 0 ? wn.toFixed(0) : ''),
            axisLabel: { color: '#aaa', fontSize: 10 }
        },
        visualMap: {
            min: 0,
            max: 1,
            calculable: false,
            orient: 'horizontal',
            right: '10%',
            top: '5%',
            inRange: { color: ['#1a1a2e', '#0066ff', '#00d9ff', '#00ff88'] },
            textStyle: { color: '#aaa' }
        },
        series: [{
            type: 'heatmap',
            data: attentionData,
            label: { show: false }
        }]
    });
}

/**
 * 加载对比数据（示例数据）
 */
function loadComparisonData() {
    // 更新指标卡片
    document.getElementById('rf-accuracy')?.textContent = '85%';
    document.getElementById('tf-accuracy')?.textContent = '92%';
    document.getElementById('rf-inference')?.textContent = '35ms';
    document.getElementById('tf-inference')?.textContent = '85ms';

    // 更新表格数据
    document.getElementById('rf-acc-table')?.textContent = '85%';
    document.getElementById('tf-acc-table')?.textContent = '92%';
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initComparisonPage);
} else {
    initComparisonPage();
}

export default { initComparisonPage };
