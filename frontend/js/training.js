/**
 * 模型训练页面 - 前端逻辑
 * @module training
 */

import { bridge } from '../bridge.js';

// 全局变量
let trainingInProgress = false;
let trainingPaused = false;
let currentEpoch = 0;
let totalEpochs = 50;
let lossHistory = [];
let accuracyHistory = [];
let lossChart = null;
let accuracyChart = null;

/**
 * 初始化训练页面
 */
export function initTrainingPage() {
    console.log('[Training] 初始化训练页面');

    // 初始化图表
    initCharts();

    // 设置事件监听
    setupEventListeners();

    // 加载默认配置
    loadDefaultConfig();
}

/**
 * 初始化 ECharts 图表
 */
function initCharts() {
    const lossChartEl = document.getElementById('loss-chart');
    const accuracyChartEl = document.getElementById('accuracy-chart');

    if (lossChartEl && typeof echarts !== 'undefined') {
        lossChart = echarts.init(lossChartEl);
        lossChart.setOption({
            title: { text: 'Loss 曲线', textStyle: { color: '#aaa' } },
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'category',
                data: [],
                axisLabel: { color: '#aaa' }
            },
            yAxis: {
                type: 'value',
                axisLabel: { color: '#aaa' }
            },
            series: [{
                name: 'Train Loss',
                type: 'line',
                data: [],
                smooth: true,
                lineStyle: { color: '#ff4444' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(255, 68, 68, 0.3)' },
                        { offset: 1, color: 'rgba(255, 68, 68, 0.05)' }
                    ])
                }
            }]
        });
    }

    if (accuracyChartEl && typeof echarts !== 'undefined') {
        accuracyChart = echarts.init(accuracyChartEl);
        accuracyChart.setOption({
            title: { text: '准确率曲线', textStyle: { color: '#aaa' } },
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'category',
                data: [],
                axisLabel: { color: '#aaa' }
            },
            yAxis: {
                type: 'value',
                max: 100,
                axisLabel: { color: '#aaa', formatter: '{value}%' }
            },
            series: [{
                name: 'Val Accuracy',
                type: 'line',
                data: [],
                smooth: true,
                lineStyle: { color: '#00ff88' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(0, 255, 136, 0.3)' },
                        { offset: 1, color: 'rgba(0, 255, 136, 0.05)' }
                    ])
                }
            }]
        });
    }

    // 响应式调整
    window.addEventListener('resize', () => {
        lossChart && lossChart.resize();
        accuracyChart && accuracyChart.resize();
    });
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    // 开始训练按钮
    const btnStart = document.getElementById('btn-start-training');
    if (btnStart) {
        btnStart.addEventListener('click', startTraining);
    }

    // 暂停按钮
    const btnPause = document.getElementById('btn-pause-training');
    if (btnPause) {
        btnPause.addEventListener('click', pauseTraining);
    }

    // 停止按钮
    const btnStop = document.getElementById('btn-stop-training');
    if (btnStop) {
        btnStop.addEventListener('click', stopTraining);
    }

    // 更新特征按钮
    const btnUpdate = document.getElementById('btn-update-features');
    if (btnUpdate) {
        btnUpdate.addEventListener('click', () => {
            addLog('开始训练...', 'info');
        });
    }
}

/**
 * 加载默认配置
 */
function loadDefaultConfig() {
    // 设置默认值
    document.getElementById('epochs').value = '50';
    document.getElementById('batch-size').value = '32';
    document.getElementById('learning-rate').value = '0.001';
    document.getElementById('val-ratio').value = '20%';
}

/**
 * 开始训练
 */
async function startTraining() {
    if (trainingInProgress) {
        addLog('训练已在进行中', 'warning');
        return;
    }

    // 获取配置
    const dataset = document.querySelector('input[name="dataset"]:checked')?.value || 'demo';
    const model = document.querySelector('input[name="model"]:checked')?.value || 'random_forest';
    const epochs = parseInt(document.getElementById('epochs').value) || 50;
    const batchSize = parseInt(document.getElementById('batch-size').value) || 32;
    const learningRate = parseFloat(document.getElementById('learning-rate').value) || 0.001;

    totalEpochs = epochs;
    currentEpoch = 0;
    lossHistory = [];
    accuracyHistory = [];

    // 更新 UI 状态
    trainingInProgress = true;
    trainingPaused = false;
    updateButtonStates();

    addLog(`开始训练 - 模型：${model}, 数据集：${dataset}, Epochs: ${epochs}`, 'success');

    // 模拟训练过程（实际应该调用后端 API）
    await simulateTraining(model, epochs, batchSize, learningRate);
}

/**
 * 暂停训练
 */
function pauseTraining() {
    if (!trainingInProgress) return;

    trainingPaused = !trainingPaused;
    updateButtonStates();
    addLog(trainingPaused ? '训练已暂停' : '训练已恢复', 'warning');
}

/**
 * 停止训练
 */
function stopTraining() {
    if (!trainingInProgress) return;

    trainingInProgress = false;
    trainingPaused = false;
    updateButtonStates();
    addLog('训练已停止', 'error');
}

/**
 * 更新按钮状态
 */
function updateButtonStates() {
    const btnStart = document.getElementById('btn-start-training');
    const btnPause = document.getElementById('btn-pause-training');
    const btnStop = document.getElementById('btn-stop-training');

    if (btnStart) btnStart.disabled = trainingInProgress && !trainingPaused;
    if (btnPause) {
        btnPause.disabled = !trainingInProgress;
        btnPause.textContent = trainingPaused ? '▶️ 恢复' : '⏸️ 暂停';
    }
    if (btnStop) btnStop.disabled = !trainingInProgress;
}

/**
 * 模拟训练过程（演示用）
 * 实际应该调用后端 API 进行真实训练
 */
async function simulateTraining(model, epochs, batchSize, learningRate) {
    const bestAccuracy = model === 'transformer' ? 92.5 : 85.2;
    const bestEpoch = Math.floor(epochs * 0.7);

    for (let epoch = 1; epoch <= epochs; epoch++) {
        if (!trainingInProgress) break;
        if (trainingPaused) {
            await sleep(1000);
            epoch--; // 不增加 epoch
            continue;
        }

        currentEpoch = epoch;

        // 模拟 Loss 和准确率
        const progress = epoch / epochs;
        const trainLoss = 2.5 * Math.exp(-3 * progress) + 0.1 * Math.random();
        const valAccuracy = bestAccuracy * (1 - Math.exp(-5 * progress)) + (Math.random() - 0.5) * 2;

        // 更新历史数据
        lossHistory.push(trainLoss);
        accuracyHistory.push(valAccuracy);

        // 更新图表
        updateCharts(epoch, trainLoss, valAccuracy);

        // 更新进度条
        updateProgress(epoch, epochs, valAccuracy);

        // 添加日志
        const logMsg = `Epoch ${epoch}/${epochs} - Loss: ${trainLoss.toFixed(4)}, Val Acc: ${valAccuracy.toFixed(2)}%`;
        if (valAccuracy > bestAccuracy * 0.95) {
            addLog(logMsg + ' ⭐', 'success');
        } else {
            addLog(logMsg, 'info');
        }

        // 模拟训练延迟
        await sleep(200); // 200ms 每 epoch（演示用）
    }

    // 训练完成
    if (trainingInProgress) {
        trainingInProgress = false;
        updateButtonStates();
        addLog(`训练完成！最佳准确率：${bestAccuracy.toFixed(2)}%`, 'success');

        // 保存模型
        addLog('正在保存模型...', 'info');
        await sleep(500);
        addLog('模型已保存到 models/random_forest_minerals.pkl', 'success');
    }
}

/**
 * 更新图表
 */
function updateCharts(epoch, loss, accuracy) {
    if (lossChart) {
        lossChart.setOption({
            xAxis: { data: lossHistory.map((_, i) => i + 1) },
            series: [{ data: lossHistory }]
        });
    }

    if (accuracyChart) {
        accuracyChart.setOption({
            xAxis: { data: accuracyHistory.map((_, i) => i + 1) },
            series: [{ data: accuracyHistory }]
        });
    }
}

/**
 * 更新进度条
 */
function updateProgress(current, total, accuracy) {
    const progress = (current / total) * 100;
    const progressFill = document.getElementById('training-progress');
    const epochInfo = document.getElementById('epoch-info');
    const accuracyInfo = document.getElementById('accuracy-info');
    const timeInfo = document.getElementById('time-info');

    if (progressFill) {
        progressFill.style.width = `${progress}%`;
        progressFill.textContent = `${progress.toFixed(0)}%`;
    }

    if (epochInfo) {
        epochInfo.textContent = `Epoch: ${current}/${total}`;
    }

    if (accuracyInfo) {
        accuracyInfo.textContent = `准确率：${accuracy.toFixed(1)}%`;
    }

    if (timeInfo) {
        const remaining = Math.floor((total - current) * 0.2); // 估算剩余秒数
        timeInfo.textContent = `剩余时间：~${remaining}s`;
    }
}

/**
 * 添加训练日志
 */
function addLog(message, type = 'info') {
    const logContainer = document.getElementById('training-log');
    if (!logContainer) return;

    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(logEntry);

    // 滚动到底部
    logContainer.scrollTop = logContainer.scrollHeight;
}

/**
 * 延时函数
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTrainingPage);
} else {
    initTrainingPage();
}

export default { initTrainingPage, addLog };
