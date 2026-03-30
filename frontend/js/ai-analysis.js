/**
 * AI 智能分析模块
 * @module ai-analysis
 *
 * 提供 AI 物质识别、不确定性量化、可解释性可视化功能
 */

import { bridge } from './bridge.js';
import { addLog } from './utils.js';

// AI 面板元素
let aiPanel = null;
let aiPredictionResult = null;
let aiUncertaintySection = null;
let aiExplainSection = null;
let aiHeatmapSection = null;

/**
 * 初始化 AI 分析模块
 */
export function initAIAnalysis() {
    // 获取 DOM 元素
    aiPanel = document.getElementById('ai-panel');
    aiPredictionResult = document.getElementById('ai-prediction-result');
    aiUncertaintySection = document.getElementById('ai-uncertainty-section');
    aiExplainSection = document.getElementById('ai-explain-section');
    aiHeatmapSection = document.getElementById('ai-heatmap-section');

    // 设置按钮事件
    setupAIButtons();

    // 设置面板关闭事件
    setupPanelCloseHandler();

    addLog('[AI] AI 分析模块已初始化');
}

/**
 * 设置 AI 分析按钮事件
 */
function setupAIButtons() {
    // AI 物质识别
    const btnPredict = document.getElementById('btn-ai-predict');
    if (btnPredict) {
        btnPredict.addEventListener('click', handleAIPredict);
    }

    // AI + 不确定性
    const btnUncertainty = document.getElementById('btn-ai-uncertainty');
    if (btnUncertainty) {
        btnUncertainty.addEventListener('click', handleAIUncertainty);
    }

    // AI 决策解释
    const btnExplain = document.getElementById('btn-ai-explain');
    if (btnExplain) {
        btnExplain.addEventListener('click', handleAIExplain);
    }

    // AI 完整分析
    const btnFull = document.getElementById('btn-ai-full');
    if (btnFull) {
        btnFull.addEventListener('click', handleAIFullAnalysis);
    }

    // AI 异常检测
    const btnOutlier = document.getElementById('btn-ai-outlier');
    if (btnOutlier) {
        btnOutlier.addEventListener('click', handleAIOutlier);
    }
}

/**
 * 设置面板关闭事件
 */
function setupPanelCloseHandler() {
    const btnClose = document.getElementById('btn-ai-close');
    if (btnClose) {
        btnClose.addEventListener('click', closeAIPanel);
    }

    // 点击面板外部关闭
    if (aiPanel) {
        aiPanel.addEventListener('click', (e) => {
            if (e.target === aiPanel) {
                closeAIPanel();
            }
        });
    }
}

/**
 * 关闭 AI 面板
 */
function closeAIPanel() {
    if (aiPanel) {
        aiPanel.style.display = 'none';
    }
}

/**
 * 显示 AI 面板
 */
function showAIPanel() {
    if (aiPanel) {
        aiPanel.style.display = 'block';
    }
}

/**
 * AI 物质识别（基础预测）
 */
async function handleAIPredict() {
    addLog('[AI] 执行 AI 物质识别...');

    try {
        const resultStr = await bridge.aiPredict();
        const result = JSON.parse(resultStr);

        if (result.success) {
            displayPredictionResult(result);
        } else {
            addLog(`[AI] 预测失败：${result.error}`, 'error');
            alert(`AI 预测失败：${result.error}`);
        }
    } catch (error) {
        addLog(`[AI] 预测异常：${error.message}`, 'error');
        alert(`AI 预测异常：${error.message}`);
    }
}

/**
 * AI 预测（带不确定性量化）
 */
async function handleAIUncertainty() {
    addLog('[AI] 执行 AI 预测（带不确定性）...');

    try {
        const resultStr = await bridge.aiPredictWithUncertainty();
        const result = JSON.parse(resultStr);

        if (result.success) {
            displayPredictionResult(result);
            displayUncertaintyResult(result);
        } else {
            addLog(`[AI] 预测失败：${result.error}`, 'error');
            alert(`AI 预测失败：${result.error}`);
        }
    } catch (error) {
        addLog(`[AI] 预测异常：${error.message}`, 'error');
        alert(`AI 预测异常：${error.message}`);
    }
}

/**
 * AI 可解释性分析
 */
async function handleAIExplain() {
    addLog('[AI] 执行 AI 可解释性分析...');

    try {
        const resultStr = await bridge.aiExplain('attention', 5);
        const result = JSON.parse(resultStr);

        if (result.success) {
            displayPredictionResult(result);
            displayExplainResult(result);
        } else {
            addLog(`[AI] 解释失败：${result.error}`, 'error');
            alert(`AI 解释失败：${result.error}`);
        }
    } catch (error) {
        addLog(`[AI] 解释异常：${error.message}`, 'error');
        alert(`AI 解释异常：${error.message}`);
    }
}

/**
 * AI 完整分析
 */
async function handleAIFullAnalysis() {
    addLog('[AI] 执行 AI 完整分析...');

    try {
        const resultStr = await bridge.aiFullAnalysis();
        const result = JSON.parse(resultStr);

        if (result.success) {
            displayPredictionResult(result);

            if (result.uncertainty) {
                displayUncertaintyResult({
                    ...result,
                    ...result.uncertainty
                });
            }

            if (result.explainability) {
                displayExplainResult({
                    ...result,
                    ...result.explainability
                });
            }
        } else {
            addLog(`[AI] 分析失败：${result.error}`, 'error');
            alert(`AI 分析失败：${result.error}`);
        }
    } catch (error) {
        addLog(`[AI] 分析异常：${error.message}`, 'error');
        alert(`AI 分析异常：${error.message}`);
    }
}

/**
 * AI 异常检测
 */
async function handleAIOutlier() {
    addLog('[AI] 执行 AI 异常检测...');

    try {
        const resultStr = await bridge.aiDetectOutlier('0.5');
        const result = JSON.parse(resultStr);

        if (result.success) {
            const message = result.is_outlier
                ? `⚠️ 检测到未知物质！\n异常分数：${result.outlier_score.toFixed(3)}`
                : `✅ 样本正常\n异常分数：${result.outlier_score.toFixed(3)}`;
            alert(message);
            addLog(`[AI] 异常检测：${result.message}`);
        } else {
            addLog(`[AI] 检测失败：${result.error}`, 'error');
            alert(`AI 异常检测失败：${result.error}`);
        }
    } catch (error) {
        addLog(`[AI] 检测异常：${error.message}`, 'error');
        alert(`AI 异常检测异常：${error.message}`);
    }
}

/**
 * 显示预测结果
 * @param {Object} result - 预测结果
 */
function displayPredictionResult(result) {
    if (!aiPredictionResult) return;

    const className = result.class_name_zh || result.class_name || '未知';
    const confidence = (result.confidence * 100).toFixed(1);

    aiPredictionResult.innerHTML = `
        <div class="prediction-class">${className}</div>
        <div class="prediction-confidence">置信度：${confidence}%</div>
        ${result.inference_time_ms ? `<div style="margin-top:10px;font-size:0.85em;color:#888;">推理时间：${result.inference_time_ms.toFixed(1)}ms</div>` : ''}
    `;

    showAIPanel();
}

/**
 * 显示不确定性结果
 * @param {Object} result - 不确定性结果
 */
function displayUncertaintyResult(result) {
    if (!aiUncertaintySection) return;

    // 显示不确定性区域
    aiUncertaintySection.style.display = 'block';

    // 更新置信度
    const confidence = result.confidence || 0;
    const uncertainty = result.uncertainty || 0;
    const confidenceInterval = result.confidence_interval_95 || [0, 0];
    const riskLevel = result.risk_level || 'unknown';
    const entropy = result.entropy || 0;

    document.getElementById('ai-confidence-bar').value = confidence;
    document.getElementById('ai-confidence-value').textContent = `${(confidence * 100).toFixed(1)}%`;
    document.getElementById('ai-uncertainty-value').textContent = `±${(uncertainty * 100).toFixed(1)}%`;
    document.getElementById('ai-confidence-interval').textContent = `[${(confidenceInterval[0] * 100).toFixed(1)}%, ${(confidenceInterval[1] * 100).toFixed(1)}%]`;

    const riskBadge = document.getElementById('ai-risk-level');
    riskBadge.textContent = getRiskLevelText(riskLevel);
    riskBadge.className = `risk-badge ${riskLevel}`;

    document.getElementById('ai-entropy').textContent = entropy.toFixed(3);
}

/**
 * 显示可解释性结果
 * @param {Object} result - 可解释性结果
 */
function displayExplainResult(result) {
    if (!aiExplainSection) return;

    // 显示可解释性区域
    aiExplainSection.style.display = 'block';

    // 更新决策依据
    const decisionBasis = document.getElementById('ai-decision-basis');
    if (result.decision_basis) {
        decisionBasis.textContent = result.decision_basis;
    }

    // 更新特征贡献度
    const featureContributions = document.getElementById('ai-feature-contributions');
    if (result.top_contributions && result.top_contributions.length > 0) {
        const maxContribution = Math.max(...result.top_contributions.map(c => c.contribution));

        featureContributions.innerHTML = `
            <div style="margin-bottom:10px;font-weight:bold;">关键特征峰贡献度：</div>
            ${result.top_contributions.map(contrib => {
                const barWidth = (contrib.contribution / maxContribution * 100).toFixed(0);
                const assignment = contrib.assignment || '未知振动模式';
                return `
                    <div class="contribution-item">
                        <div class="contribution-position">${contrib.position.toFixed(0)} cm⁻¹</div>
                        <div class="contribution-bar">
                            <div class="contribution-fill" style="width: ${barWidth}%"></div>
                        </div>
                        <div class="contribution-value">${(contrib.contribution * 100).toFixed(1)}%</div>
                        <div class="contribution-assignment" title="${assignment}">${assignment}</div>
                    </div>
                `;
            }).join('')}
        `;
    }

    // 显示热力图（如果有）
    if (result.feature_importance) {
        displayHeatmap(result.feature_importance);
    }
}

/**
 * 显示热力图
 * @param {Object} heatmapData - 热力图数据
 */
function displayHeatmap(heatmapData) {
    if (!aiHeatmapSection || !aiHeatmapSection) return;

    aiHeatmapSection.style.display = 'block';

    const container = document.getElementById('ai-heatmap-container');
    if (!container) return;

    // 使用 ECharts 绘制热力图
    if (typeof echarts !== 'undefined') {
        const chart = echarts.init(container);

        const wavenumbers = heatmapData.wavenumbers || [];
        const importance = heatmapData.importance || [];

        // 准备数据
        const data = wavenumbers.map((wn, i) => [wn, 0, importance[i] || 0]);

        const option = {
            tooltip: {
                formatter: (params) => {
                    return `${params.data[0].toFixed(0)} cm⁻¹<br/>重要性：${(params.data[2] * 100).toFixed(1)}%`;
                }
            },
            grid: {
                top: '10%',
                bottom: '20%',
                left: '10%',
                right: '5%'
            },
            xAxis: {
                type: 'value',
                name: '拉曼位移 (cm⁻¹)',
                nameTextStyle: {
                    color: '#aaa'
                },
                axisLabel: {
                    color: '#aaa'
                }
            },
            yAxis: {
                type: 'category',
                show: false
            },
            visualMap: {
                min: 0,
                max: 1,
                calculable: false,
                orient: 'horizontal',
                right: '10%',
                top: '5%',
                itemWidth: 10,
                itemHeight: 20,
                inRange: {
                    color: ['#1a1a2e', '#00d9ff', '#00ff88']
                },
                textStyle: {
                    color: '#aaa'
                }
            },
            series: [{
                type: 'heatmap',
                data: data,
                pointSize: 4,
                symbolSize: function (val) {
                    return val[2] * 20;
                }
            }]
        };

        chart.setOption(option);

        // 响应式调整
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }
}

/**
 * 获取风险等级文本
 * @param {string} riskLevel - 风险等级
 * @returns {string} 风险等级文本
 */
function getRiskLevelText(riskLevel) {
    const riskLevelMap = {
        'low': '低风险',
        'medium': '中风险',
        'high': '高风险',
        'unknown': '未知'
    };
    return riskLevelMap[riskLevel] || riskLevel;
}

/**
 * 重置 AI 面板
 */
export function resetAIPanel() {
    if (aiUncertaintySection) {
        aiUncertaintySection.style.display = 'none';
    }
    if (aiExplainSection) {
        aiExplainSection.style.display = 'none';
    }
    if (aiHeatmapSection) {
        aiHeatmapSection.style.display = 'none';
    }
    if (aiPredictionResult) {
        aiPredictionResult.innerHTML = '';
    }
}
