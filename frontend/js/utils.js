/**
 * 拉曼光谱边缘客户端 - 工具函数模块
 * @module utils
 * 
 * P11 改进：添加防抖、节流、内存泄漏防护工具
 */

// ==================== 防抖/节流 ====================

/**
 * 防抖函数（debounce）
 * 在 n 秒后执行函数，期间重新触发会重置计时器
 * 适用于：输入框、搜索框等频繁触发场景
 * 
 * @param {Function} fn - 要执行的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(fn, delay = 300) {
    let timer = null;
    return function(...args) {
        const context = this;
        clearTimeout(timer);
        timer = setTimeout(() => {
            fn.apply(context, args);
        }, delay);
    };
}

/**
 * 节流函数（throttle）
 * 在 n 秒内只执行一次函数
 * 适用于：滚动、窗口大小变化、鼠标移动等场景
 * 
 * P11 修复：修正第二次调用时机判断逻辑
 * 
 * @param {Function} fn - 要执行的函数
 * @param {number} interval - 间隔时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(fn, interval = 300) {
    let lastCall = 0;
    let timer = null;
    
    return function(...args) {
        const context = this;
        const now = Date.now();
        const timeSinceLastCall = now - lastCall;
        
        // 清除之前的定时器
        clearTimeout(timer);
        
        if (timeSinceLastCall >= interval) {
            // 距离上次调用已超过间隔，立即执行
            lastCall = now;
            fn.apply(context, args);
        } else {
            // 距离上次调用不足间隔，延迟执行
            timer = setTimeout(() => {
                lastCall = Date.now();
                fn.apply(context, args);
            }, interval - timeSinceLastCall);
        }
    };
}

// ==================== Toast 提示 ====================
/**
 * 显示 Toast 提示消息
 * @param {string} message - 提示消息
 * @param {'error'|'success'|'warning'|'info'} type - 提示类型
 * @param {number} duration - 显示时长 (毫秒)
 */
export function showToast(message, type = 'info', duration = 3000) {
    // 成功提示使用日志代替
    if (type === 'success') {
        addLog(message, 'success');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // 样式
    const bgColors = {
        'error': '#ff4444',
        'warning': '#ffaa00',
        'info': '#00d9ff'
    };
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 6px;
        color: #fff;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        background: ${bgColors[type] || bgColors['info']};
    `;

    document.body.appendChild(toast);

    // 自动消失
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==================== 日志系统 ====================

/**
 * 全局虚拟日志管理器（如果启用虚拟滚动）
 * @type {VirtualLogManager|null}
 */
let virtualLogInstance = null;

/**
 * 是否启用虚拟滚动
 * @type {boolean}
 */
let virtualScrollEnabled = false;

/**
 * 启用虚拟滚动日志
 * @param {string} containerSelector - 容器选择器
 * @param {Object} options - 选项
 * @returns {VirtualLogManager}
 */
export function enableVirtualLog(containerSelector = '#log-panel', options = {}) {
    if (virtualLogInstance) {
        virtualLogInstance.destroy();
    }
    
    const { createVirtualLog } = import('./virtual-scroll.js');
    // 注意：由于是动态导入，需要在 main.js 中初始化
    virtualScrollEnabled = true;
    
    return virtualLogInstance;
}

/**
 * 设置虚拟日志实例
 * @param {VirtualLogManager} instance - 虚拟日志实例
 */
export function setVirtualLogInstance(instance) {
    virtualLogInstance = instance;
    virtualScrollEnabled = true;
}

/**
 * 获取虚拟日志实例
 * @returns {VirtualLogManager|null}
 */
export function getVirtualLogInstance() {
    return virtualLogInstance;
}

/**
 * 添加日志到日志面板（支持虚拟滚动）
 * @param {string} message - 日志消息
 * @param {'info'|'success'|'warning'|'error'} type - 日志类型
 */
export function addLog(message, type = 'info') {
    if (virtualScrollEnabled && virtualLogInstance) {
        // 使用虚拟滚动
        virtualLogInstance.addLog(message, type);
    } else {
        // 使用传统方式
        const logPanel = document.getElementById('log-panel');
        if (!logPanel) return;

        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        const time = new Date().toLocaleTimeString();
        entry.textContent = `[${time}] ${message}`;
        logPanel.appendChild(entry);
        logPanel.scrollTop = logPanel.scrollHeight;
        
        // P11 改进：限制日志数量，防止内存泄漏
        const maxLogs = 500;
        while (logPanel.children.length > maxLogs) {
            logPanel.removeChild(logPanel.firstChild);
        }
    }
}

// ==================== 数据验证 ====================
/**
 * 验证积分时间参数
 * @param {number} timeMs - 积分时间 (ms)
 * @returns {{valid: boolean, value: number, message?: string}}
 */
export function validateIntegrationTime(timeMs) {
    const value = parseInt(timeMs);
    if (isNaN(value) || value < 10 || value > 10000) {
        return {
            valid: false,
            value: 100,
            message: '积分时间必须在 10-10000ms 之间'
        };
    }
    return { valid: true, value };
}

/**
 * 验证噪声水平参数
 * @param {number} noiseLevel - 噪声水平
 * @returns {{valid: boolean, value: number, message?: string}}
 */
export function validateNoiseLevel(noiseLevel) {
    const value = parseFloat(noiseLevel);
    if (isNaN(value) || value < 0 || value > 0.5) {
        return {
            valid: false,
            value: 0.02,
            message: '噪声水平必须在 0-0.5 之间'
        };
    }
    return { valid: true, value };
}

/**
 * 验证累加平均次数参数
 * @param {number} count - 累加次数
 * @returns {{valid: boolean, value: number, message?: string}}
 */
export function validateAccumulationCount(count) {
    const value = parseInt(count);
    if (isNaN(value) || value < 1 || value > 100) {
        return {
            valid: false,
            value: 1,
            message: '累加平均次数必须在 1-100 之间'
        };
    }
    return { valid: true, value };
}

/**
 * 验证平滑窗口参数
 * @param {number} window - 窗口大小
 * @returns {{valid: boolean, value: number, message?: string}}
 */
export function validateSmoothingWindow(window) {
    const value = parseInt(window);
    if (isNaN(value) || value < 0 || value > 51) {
        return {
            valid: false,
            value: 0,
            message: '平滑窗口必须在 0-51 之间'
        };
    }
    // 确保为奇数
    if (value > 1 && value % 2 === 0) {
        return {
            valid: true,
            value: value + 1,
            message: `平滑窗口调整为奇数：${value + 1}`
        };
    }
    return { valid: true, value };
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string}
 */
export function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/**
 * 格式化时间戳
 * @param {number} timestamp - 时间戳
 * @returns {string}
 */
export function formatTimestamp(timestamp) {
    return new Date(timestamp * 1000).toLocaleString();
}

// ==================== 内存泄漏防护 ====================

/**
 * 事件监听器管理器
 * 用于统一管理和清理事件监听器，防止内存泄漏
 * 
 * @example
 * const cleanup = createEventCleanup();
 * cleanup.add(window, 'resize', handleResize);
 * cleanup.add(document, 'click', handleClick);
 * // 组件卸载时调用
 * cleanup.removeAll();
 */
export function createEventCleanup() {
    const listeners = [];
    
    return {
        /**
         * 添加事件监听器
         * @param {EventTarget} target - 事件目标
         * @param {string} event - 事件名
         * @param {Function} handler - 处理函数
         * @param {Object} options - 事件选项
         */
        add(target, event, handler, options = {}) {
            target.addEventListener(event, handler, options);
            listeners.push({ target, event, handler, options });
            return () => this.remove(target, event, handler, options);
        },
        
        /**
         * 移除单个事件监听器
         * @param {EventTarget} target - 事件目标
         * @param {string} event - 事件名
         * @param {Function} handler - 处理函数
         * @param {Object} options - 事件选项
         */
        remove(target, event, handler, options = {}) {
            target.removeEventListener(event, handler, options);
            const index = listeners.findIndex(
                l => l.target === target && l.event === event && l.handler === handler
            );
            if (index > -1) {
                listeners.splice(index, 1);
            }
        },
        
        /**
         * 移除所有事件监听器
         */
        removeAll() {
            listeners.forEach(({ target, event, handler, options }) => {
                target.removeEventListener(event, handler, options);
            });
            listeners.length = 0;
        },
        
        /**
         * 获取监听器数量
         * @returns {number}
         */
        getCount() {
            return listeners.length;
        }
    };
}

/**
 * 定时器管理器
 * 用于统一管理和清理定时器，防止内存泄漏
 * 
 * @example
 * const timerManager = createTimerManager();
 * const timeoutId = timerManager.setTimeout(() => {}, 1000);
 * const intervalId = timerManager.setInterval(() => {}, 1000);
 * // 组件卸载时调用
 * timerManager.clearAll();
 */
export function createTimerManager() {
    const timeouts = [];
    const intervals = [];
    const animationFrames = [];
    
    return {
        /**
         * 设置超时定时器
         * @param {Function} fn - 回调函数
         * @param {number} delay - 延迟时间
         * @returns {number} 定时器 ID
         */
        setTimeout(fn, delay) {
            const id = setTimeout(() => {
                fn();
                const index = timeouts.indexOf(id);
                if (index > -1) timeouts.splice(index, 1);
            }, delay);
            timeouts.push(id);
            return id;
        },
        
        /**
         * 设置间隔定时器
         * @param {Function} fn - 回调函数
         * @param {number} interval - 间隔时间
         * @returns {number} 定时器 ID
         */
        setInterval(fn, interval) {
            const id = setInterval(fn, interval);
            intervals.push(id);
            return id;
        },
        
        /**
         * 请求动画帧
         * @param {Function} fn - 回调函数
         * @returns {number} 帧 ID
         */
        requestAnimationFrame(fn) {
            const id = requestAnimationFrame(() => {
                fn();
                const index = animationFrames.indexOf(id);
                if (index > -1) animationFrames.splice(index, 1);
            });
            animationFrames.push(id);
            return id;
        },
        
        /**
         * 清除超时定时器
         * @param {number} id - 定时器 ID
         */
        clearTimeout(id) {
            clearTimeout(id);
            const index = timeouts.indexOf(id);
            if (index > -1) timeouts.splice(index, 1);
        },
        
        /**
         * 清除间隔定时器
         * @param {number} id - 定时器 ID
         */
        clearInterval(id) {
            clearInterval(id);
            const index = intervals.indexOf(id);
            if (index > -1) intervals.splice(index, 1);
        },
        
        /**
         * 取消动画帧
         * @param {number} id - 帧 ID
         */
        cancelAnimationFrame(id) {
            cancelAnimationFrame(id);
            const index = animationFrames.indexOf(id);
            if (index > -1) animationFrames.splice(index, 1);
        },
        
        /**
         * 清除所有定时器
         */
        clearAll() {
            timeouts.forEach(id => clearTimeout(id));
            intervals.forEach(id => clearInterval(id));
            animationFrames.forEach(id => cancelAnimationFrame(id));
            timeouts.length = 0;
            intervals.length = 0;
            animationFrames.length = 0;
        },
        
        /**
         * 获取定时器数量
         * @returns {{timeouts: number, intervals: number, animationFrames: number}}
         */
        getCount() {
            return {
                timeouts: timeouts.length,
                intervals: intervals.length,
                animationFrames: animationFrames.length
            };
        }
    };
}
