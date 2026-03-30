/**
 * 拉曼光谱边缘客户端 - 骨架屏组件模块
 * @module skeleton
 * 
 * P11 改进：添加骨架屏加载组件，提升用户体验
 * 
 * 使用示例:
 * // 显示图表骨架屏
 * showChartSkeleton();
 * 
 * // 隐藏骨架屏
 * hideChartSkeleton();
 * 
 * // 或者使用包装器模式
 * const wrapper = createSkeletonWrapper('#spectrum-chart');
 * wrapper.show();
 * // ... 数据加载完成后
 * wrapper.hide();
 */

import { addLog } from './utils.js';

/**
 * 骨架屏配置
 */
const SKELETON_CONFIG = {
    chart: {
        containerId: 'spectrum-chart',
        parentClass: 'chart-container'
    },
    controlPanel: {
        containerId: 'control-panel',
        class: 'control-panel-skeleton'
    },
    statusBar: {
        containerId: 'status-bar',
        class: 'status-bar-skeleton'
    },
    logPanel: {
        containerId: 'log-panel',
        class: 'log-panel-skeleton'
    }
};

/**
 * 骨架屏实例缓存
 */
const skeletonInstances = new Map();

/**
 * 创建骨架屏包装器
 * @param {string} selector - 目标元素选择器
 * @param {string} type - 骨架屏类型 ('chart', 'control', 'status', 'log', 'custom')
 * @returns {{show: Function, hide: Function, destroy: Function}}
 */
export function createSkeletonWrapper(selector, type = 'custom') {
    const target = document.querySelector(selector);
    if (!target) {
        addLog(`[Skeleton] 未找到目标元素：${selector}`, 'warning');
        return {
            show: () => {},
            hide: () => {},
            destroy: () => {}
        };
    }

    const skeletonId = `skeleton-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // 保存原始内容
    const originalContent = target.innerHTML;
    const originalStyle = target.style.cssText;

    /**
     * 显示骨架屏
     */
    function show() {
        const skeletonHTML = getSkeletonHTML(type);
        target.innerHTML = skeletonHTML;
        target.classList.add('skeleton-wrapper');
        target.classList.add('loading');
        skeletonInstances.set(skeletonId, { target, originalContent, originalStyle });
        addLog(`[Skeleton] 显示骨架屏：${selector}`, 'info');
    }

    /**
     * 隐藏骨架屏
     */
    function hide() {
        target.innerHTML = originalContent;
        target.style.cssText = originalStyle;
        target.classList.remove('skeleton-wrapper', 'loading');
        skeletonInstances.delete(skeletonId);
        addLog(`[Skeleton] 隐藏骨架屏：${selector}`, 'info');
    }

    /**
     * 销毁骨架屏
     */
    function destroy() {
        hide();
    }

    return { show, hide, destroy };
}

/**
 * 获取骨架屏 HTML
 * @param {string} type - 骨架屏类型
 * @returns {string} HTML 字符串
 */
function getSkeletonHTML(type) {
    switch (type) {
        case 'chart':
            return `
                <div class="chart-skeleton">
                    <div class="skeleton-item skeleton-chart-title"></div>
                    <div class="skeleton-item skeleton-chart-area"></div>
                    <div class="skeleton-item skeleton-chart-x-axis"></div>
                </div>
            `;
        
        case 'control':
            return `
                <div class="control-panel-skeleton">
                    <div class="skeleton-item skeleton-title"></div>
                    <div class="skeleton-item skeleton-button"></div>
                    <div class="skeleton-item skeleton-button"></div>
                    <div class="skeleton-item skeleton-button"></div>
                    <div class="skeleton-item skeleton-input"></div>
                    <div class="skeleton-item skeleton-input"></div>
                </div>
            `;
        
        case 'status':
            return `
                <div class="status-bar-skeleton">
                    <div class="skeleton-status">
                        <div class="skeleton-item skeleton-status-indicator"></div>
                        <div class="skeleton-item skeleton-status-text"></div>
                    </div>
                    <div class="skeleton-status">
                        <div class="skeleton-item skeleton-status-indicator"></div>
                        <div class="skeleton-item skeleton-status-text"></div>
                    </div>
                    <div class="skeleton-status">
                        <div class="skeleton-item skeleton-status-indicator"></div>
                        <div class="skeleton-item skeleton-status-text"></div>
                    </div>
                </div>
            `;
        
        case 'log':
            return `
                <div class="log-panel-skeleton">
                    <div class="skeleton-item skeleton-log-line"></div>
                    <div class="skeleton-item skeleton-log-line"></div>
                    <div class="skeleton-item skeleton-log-line"></div>
                    <div class="skeleton-item skeleton-log-line"></div>
                    <div class="skeleton-item skeleton-log-line"></div>
                </div>
            `;
        
        case 'custom':
        default:
            return `
                <div class="skeleton-container">
                    <div class="skeleton-item text-long"></div>
                    <div class="skeleton-item text-long"></div>
                    <div class="skeleton-item text-medium"></div>
                    <div class="skeleton-item text-short"></div>
                </div>
            `;
    }
}

/**
 * 显示图表骨架屏
 */
export function showChartSkeleton() {
    const container = document.getElementById(SKELETON_CONFIG.chart.containerId);
    if (container) {
        container.innerHTML = getSkeletonHTML('chart');
        container.classList.add('skeleton-active');
        addLog('[Skeleton] 显示图表骨架屏', 'info');
    }
}

/**
 * 隐藏图表骨架屏
 * @param {string} contentHTML - 可选的内容 HTML，不提供则保持骨架屏
 */
export function hideChartSkeleton(contentHTML = '') {
    const container = document.getElementById(SKELETON_CONFIG.chart.containerId);
    if (container) {
        if (contentHTML) {
            container.innerHTML = contentHTML;
        }
        container.classList.remove('skeleton-active');
        addLog('[Skeleton] 隐藏图表骨架屏', 'info');
    }
}

/**
 * 显示控制面板骨架屏
 */
export function showControlPanelSkeleton() {
    const container = document.querySelector(`.${SKELETON_CONFIG.controlPanel.class}`);
    if (container) {
        const originalContent = container.innerHTML;
        container.setAttribute('data-original-content', originalContent);
        container.innerHTML = getSkeletonHTML('control');
        addLog('[Skeleton] 显示控制面板骨架屏', 'info');
    }
}

/**
 * 隐藏控制面板骨架屏
 */
export function hideControlPanelSkeleton() {
    const container = document.querySelector(`.${SKELETON_CONFIG.controlPanel.class}`);
    if (container) {
        const originalContent = container.getAttribute('data-original-content');
        if (originalContent) {
            container.innerHTML = originalContent;
            container.removeAttribute('data-original-content');
        }
        addLog('[Skeleton] 隐藏控制面板骨架屏', 'info');
    }
}

/**
 * 显示状态栏骨架屏
 */
export function showStatusBarSkeleton() {
    const container = document.getElementById('status-bar');
    if (container) {
        const originalContent = container.innerHTML;
        container.setAttribute('data-original-content', originalContent);
        container.innerHTML = getSkeletonHTML('status');
        addLog('[Skeleton] 显示状态栏骨架屏', 'info');
    }
}

/**
 * 隐藏状态栏骨架屏
 */
export function hideStatusBarSkeleton() {
    const container = document.getElementById('status-bar');
    if (container) {
        const originalContent = container.getAttribute('data-original-content');
        if (originalContent) {
            container.innerHTML = originalContent;
            container.removeAttribute('data-original-content');
        }
        addLog('[Skeleton] 隐藏状态栏骨架屏', 'info');
    }
}

/**
 * 显示日志面板骨架屏
 */
export function showLogPanelSkeleton() {
    const container = document.getElementById('log-panel');
    if (container) {
        const originalContent = container.innerHTML;
        container.setAttribute('data-original-content', originalContent);
        container.innerHTML = getSkeletonHTML('log');
        addLog('[Skeleton] 显示日志面板骨架屏', 'info');
    }
}

/**
 * 隐藏日志面板骨架屏
 */
export function hideLogPanelSkeleton() {
    const container = document.getElementById('log-panel');
    if (container) {
        const originalContent = container.getAttribute('data-original-content');
        if (originalContent) {
            container.innerHTML = originalContent;
            container.removeAttribute('data-original-content');
        }
        addLog('[Skeleton] 隐藏日志面板骨架屏', 'info');
    }
}

/**
 * 显示通用骨架屏
 * @param {string} containerId - 容器 ID
 * @param {string} type - 骨架屏类型
 */
export function showGenericSkeleton(containerId, type = 'custom') {
    const container = document.getElementById(containerId);
    if (container) {
        const originalContent = container.innerHTML;
        container.setAttribute('data-original-content', originalContent);
        container.innerHTML = getSkeletonHTML(type);
        addLog(`[Skeleton] 显示通用骨架屏：${containerId}`, 'info');
    }
}

/**
 * 隐藏通用骨架屏
 * @param {string} containerId - 容器 ID
 */
export function hideGenericSkeleton(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const originalContent = container.getAttribute('data-original-content');
        if (originalContent) {
            container.innerHTML = originalContent;
            container.removeAttribute('data-original-content');
        }
        addLog(`[Skeleton] 隐藏通用骨架屏：${containerId}`, 'info');
    }
}

/**
 * 全局显示所有骨架屏（用于首次加载）
 */
export function showAllSkeletons() {
    showChartSkeleton();
    showControlPanelSkeleton();
    showStatusBarSkeleton();
    showLogPanelSkeleton();
    addLog('[Skeleton] 显示所有骨架屏', 'info');
}

/**
 * 全局隐藏所有骨架屏
 */
export function hideAllSkeletons() {
    hideChartSkeleton();
    hideControlPanelSkeleton();
    hideStatusBarSkeleton();
    hideLogPanelSkeleton();
    addLog('[Skeleton] 隐藏所有骨架屏', 'info');
}
