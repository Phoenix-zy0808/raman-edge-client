/**
 * 拉曼光谱边缘客户端 - 虚拟滚动模块
 * @module virtualScroll
 * 
 * P11 改进：实现虚拟滚动，优化长列表性能
 * 
 * 适用于：日志面板、数据列表等可能包含大量条目的场景
 * 
 * 使用示例:
 * // 初始化虚拟滚动日志面板
 * const virtualLog = createVirtualLog('#log-panel', {
 *     itemHeight: 24,
 *     maxItems: 1000
 * });
 * 
 * // 添加日志
 * virtualLog.addLog('系统初始化完成', 'info');
 * 
 * // 清理
 * virtualLog.destroy();
 */

import { addLog as originalAddLog, createTimerManager } from './utils.js';

/**
 * 虚拟滚动日志管理器
 */
export class VirtualLogManager {
    /**
     * @param {string} containerSelector - 容器选择器
     * @param {Object} options - 选项
     * @param {number} options.itemHeight - 每项高度（像素）
     * @param {number} options.maxItems - 最大保留条目数
     * @param {number} options.bufferSize - 缓冲区大小（渲染的额外条目数）
     */
    constructor(containerSelector, options = {}) {
        this.container = document.querySelector(containerSelector);
        if (!this.container) {
            throw new Error(`未找到容器：${containerSelector}`);
        }

        this.options = {
            itemHeight: 24,
            maxItems: 1000,
            bufferSize: 5,
            ...options
        };

        this.logs = [];
        this.visibleStart = 0;
        this.visibleEnd = 0;
        this.scrollTop = 0;

        // 定时器管理器
        this.timerManager = createTimerManager();

        // 创建虚拟滚动结构
        this._initVirtualScroll();

        // 绑定滚动事件（使用节流）
        this._bindScrollEvent();

        // 初始渲染
        this._render();
    }

    /**
     * 初始化虚拟滚动 DOM 结构
     */
    _initVirtualScroll() {
        // 保存原始内容（如果有）
        this.originalContent = this.container.innerHTML;

        // 创建虚拟滚动容器
        this.container.innerHTML = `
            <div class="virtual-log-container" style="position: relative; overflow-y: auto; height: 100%;">
                <div class="virtual-log-spacer" style="position: absolute; left: 0; right: 0;"></div>
                <div class="virtual-log-viewport" style="position: absolute; left: 0; right: 0;"></div>
            </div>
        `;

        this.scrollContainer = this.container.querySelector('.virtual-log-container');
        this.spacerElement = this.container.querySelector('.virtual-log-spacer');
        this.viewportElement = this.container.querySelector('.virtual-log-viewport');

        // 设置容器高度
        this.container.style.height = this.container.style.height || '150px';
        this.container.style.overflow = 'hidden';
    }

    /**
     * 绑定滚动事件
     */
    _bindScrollEvent() {
        let ticking = false;

        this.scrollContainer.addEventListener('scroll', () => {
            if (!ticking) {
                this.timerManager.requestAnimationFrame(() => {
                    this.scrollTop = this.scrollContainer.scrollTop;
                    this._updateVisibleRange();
                    this._render();
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    /**
     * 更新可见范围
     */
    _updateVisibleRange() {
        const containerHeight = this.scrollContainer.clientHeight;
        const totalHeight = this.logs.length * this.options.itemHeight;

        // 计算可见区域
        const start = Math.floor(this.scrollTop / this.options.itemHeight);
        const visibleCount = Math.ceil(containerHeight / this.options.itemHeight);

        // 添加缓冲区
        const buffer = this.options.bufferSize;
        this.visibleStart = Math.max(0, start - buffer);
        this.visibleEnd = Math.min(this.logs.length, start + visibleCount + buffer);
    }

    /**
     * 渲染可见内容
     */
    _render() {
        const totalHeight = this.logs.length * this.options.itemHeight;
        this.spacerElement.style.height = `${totalHeight}px`;

        // 渲染可见条目
        const visibleLogs = this.logs.slice(this.visibleStart, this.visibleEnd);
        const offsetY = this.visibleStart * this.options.itemHeight;

        this.viewportElement.style.transform = `translateY(${offsetY}px)`;
        this.viewportElement.innerHTML = visibleLogs.map(log => `
            <div class="log-entry ${log.type}" style="height: ${this.options.itemHeight}px; line-height: ${this.options.itemHeight}px;">
                <span style="opacity: 0.7; margin-right: 8px;">[${log.time}]</span>
                ${log.message}
            </div>
        `).join('');
    }

    /**
     * 添加日志
     * @param {string} message - 日志消息
     * @param {'info'|'success'|'warning'|'error'} type - 日志类型
     */
    addLog(message, type = 'info') {
        const time = new Date().toLocaleTimeString();
        this.logs.push({ message, type, time });

        // 限制日志数量
        if (this.logs.length > this.options.maxItems) {
            this.logs = this.logs.slice(this.logs.length - this.options.maxItems);
            this.visibleStart = Math.max(0, this.visibleStart - (this.logs.length - this.options.maxItems));
            this.visibleEnd = this.logs.length;
        }

        // 自动滚动到底部（如果已经在底部附近）
        const containerHeight = this.scrollContainer.clientHeight;
        const scrollThreshold = containerHeight * 0.8;
        const isNearBottom = this.scrollTop + containerHeight >= this.scrollContainer.scrollHeight - scrollThreshold;

        if (isNearBottom || this.logs.length <= Math.ceil(containerHeight / this.options.itemHeight)) {
            this.timerManager.setTimeout(() => {
                this.scrollContainer.scrollTop = this.scrollContainer.scrollHeight;
            }, 50);
        }

        this._updateVisibleRange();
        this._render();
    }

    /**
     * 清除所有日志
     */
    clear() {
        this.logs = [];
        this.visibleStart = 0;
        this.visibleEnd = 0;
        this.scrollTop = 0;
        this.scrollContainer.scrollTop = 0;
        this._render();
    }

    /**
     * 获取日志数量
     * @returns {number}
     */
    getCount() {
        return this.logs.length;
    }

    /**
     * 导出日志
     * @returns {Array} 日志数组
     */
    exportLogs() {
        return [...this.logs];
    }

    /**
     * 导入日志
     * @param {Array} logs - 日志数组
     */
    importLogs(logs) {
        this.logs = logs.slice(-this.options.maxItems);
        this._updateVisibleRange();
        this._render();
    }

    /**
     * 销毁虚拟滚动
     */
    destroy() {
        this.timerManager.clearAll();
        this.container.innerHTML = this.originalContent || '';
    }
}

/**
 * 创建虚拟日志管理器
 * @param {string} containerSelector - 容器选择器
 * @param {Object} options - 选项
 * @returns {VirtualLogManager}
 */
export function createVirtualLog(containerSelector, options = {}) {
    return new VirtualLogManager(containerSelector, options);
}

/**
 * 通用虚拟列表管理器（可用于其他列表）
 */
export class VirtualListManager {
    /**
     * @param {string} containerSelector - 容器选择器
     * @param {Object} options - 选项
     * @param {number} options.itemHeight - 每项高度（像素）
     * @param {Function} options.renderItem - 渲染函数
     */
    constructor(containerSelector, options = {}) {
        this.container = document.querySelector(containerSelector);
        if (!this.container) {
            throw new Error(`未找到容器：${containerSelector}`);
        }

        this.options = {
            itemHeight: 40,
            renderItem: (item, index) => `<div>${JSON.stringify(item)}</div>`,
            ...options
        };

        this.items = [];
        this.visibleStart = 0;
        this.visibleEnd = 0;
        this.scrollTop = 0;

        this._initVirtualScroll();
        this._bindScrollEvent();
    }

    _initVirtualScroll() {
        this.container.innerHTML = `
            <div class="virtual-list-container" style="position: relative; overflow-y: auto; height: 100%;">
                <div class="virtual-list-spacer" style="position: absolute; left: 0; right: 0;"></div>
                <div class="virtual-list-viewport" style="position: absolute; left: 0; right: 0;"></div>
            </div>
        `;

        this.scrollContainer = this.container.querySelector('.virtual-list-container');
        this.spacerElement = this.container.querySelector('.virtual-list-spacer');
        this.viewportElement = this.container.querySelector('.virtual-list-viewport');

        this.container.style.overflow = 'hidden';
    }

    _bindScrollEvent() {
        let ticking = false;

        this.scrollContainer.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.scrollTop = this.scrollContainer.scrollTop;
                    this._updateVisibleRange();
                    this._render();
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    _updateVisibleRange() {
        const containerHeight = this.scrollContainer.clientHeight;
        const start = Math.floor(this.scrollTop / this.options.itemHeight);
        const visibleCount = Math.ceil(containerHeight / this.options.itemHeight);
        const buffer = 5;

        this.visibleStart = Math.max(0, start - buffer);
        this.visibleEnd = Math.min(this.items.length, start + visibleCount + buffer);
    }

    _render() {
        const totalHeight = this.items.length * this.options.itemHeight;
        this.spacerElement.style.height = `${totalHeight}px`;

        const visibleItems = this.items.slice(this.visibleStart, this.visibleEnd);
        const offsetY = this.visibleStart * this.options.itemHeight;

        this.viewportElement.style.transform = `translateY(${offsetY}px)`;
        this.viewportElement.innerHTML = visibleItems
            .map((item, index) => this.options.renderItem(item, this.visibleStart + index))
            .join('');
    }

    /**
     * 设置数据
     * @param {Array} items - 数据数组
     */
    setItems(items) {
        this.items = items;
        this._updateVisibleRange();
        this._render();
    }

    /**
     * 添加数据
     * @param {*} item - 数据项
     */
    addItem(item) {
        this.items.push(item);
        this._updateVisibleRange();
        this._render();
    }

    /**
     * 更新数据
     * @param {number} index - 索引
     * @param {*} item - 新数据
     */
    updateItem(index, item) {
        if (index >= 0 && index < this.items.length) {
            this.items[index] = item;
            if (index >= this.visibleStart && index < this.visibleEnd) {
                this._render();
            }
        }
    }

    /**
     * 删除数据
     * @param {number} index - 索引
     */
    removeItem(index) {
        if (index >= 0 && index < this.items.length) {
            this.items.splice(index, 1);
            this._updateVisibleRange();
            this._render();
        }
    }

    /**
     * 清除所有数据
     */
    clear() {
        this.items = [];
        this.scrollTop = 0;
        this.scrollContainer.scrollTop = 0;
        this._render();
    }

    /**
     * 销毁
     */
    destroy() {
        this.items = [];
    }
}

/**
 * 创建虚拟列表管理器
 * @param {string} containerSelector - 容器选择器
 * @param {Object} options - 选项
 * @returns {VirtualListManager}
 */
export function createVirtualList(containerSelector, options = {}) {
    return new VirtualListManager(containerSelector, options);
}
