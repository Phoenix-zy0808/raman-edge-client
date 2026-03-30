/**
 * 事件总线模块
 * @module event-bus
 *
 * 提供轻量级事件总线，替代全局回调，实现模块间解耦
 *
 * @example
 * // 订阅事件
 * events.on('device:connected', (data) => {
 *     console.log('设备已连接', data);
 * });
 *
 * // 发布事件
 * events.emit('device:connected', { deviceId: 'abc123' });
 *
 * // 取消订阅
 * events.off('device:connected', callback);
 *
 * // 一次性订阅
 * events.once('device:connected', (data) => {
 *     console.log('只接收一次');
 * });
 */

/**
 * 事件总线类
 */
export class EventEmitter {
    constructor() {
        this._events = new Map();
        this._maxListeners = 10; // 默认最大监听器数量
    }

    /**
     * 设置最大监听器数量
     * @param {number} n - 最大数量
     */
    setMaxListeners(n) {
        this._maxListeners = n;
        return this;
    }

    /**
     * 获取最大监听器数量
     * @returns {number}
     */
    getMaxListeners() {
        return this._maxListeners;
    }

    /**
     * 订阅事件
     * @param {string} event - 事件名称
     * @param {Function} listener - 回调函数
     * @returns {EventEmitter} this
     */
    on(event, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function');
        }

        const listeners = this._events.get(event) || [];

        // 检查是否超过最大监听器数量
        if (listeners.length >= this._maxListeners) {
            console.warn(`[EventBus] 警告：事件 "${event}" 的监听器数量超过最大限制 (${this._maxListeners})`);
        }

        listeners.push(listener);
        this._events.set(event, listeners);

        return this;
    }

    /**
     * 一次性订阅事件（触发后自动取消）
     * @param {string} event - 事件名称
     * @param {Function} listener - 回调函数
     * @returns {EventEmitter} this
     */
    once(event, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function');
        }

        const onceWrapper = (...args) => {
            this.off(event, onceWrapper);
            listener.apply(this, args);
        };

        // 保存原始 listener 引用，方便后续移除
        onceWrapper._listener = listener;

        return this.on(event, onceWrapper);
    }

    /**
     * 取消订阅事件
     * @param {string} event - 事件名称
     * @param {Function} listener - 回调函数
     * @returns {EventEmitter} this
     */
    off(event, listener) {
        const listeners = this._events.get(event);
        if (!listeners) {
            return this;
        }

        if (!listener) {
            // 移除该事件的所有监听器
            this._events.delete(event);
            return this;
        }

        const index = listeners.findIndex(l => l === listener || l._listener === listener);
        if (index !== -1) {
            listeners.splice(index, 1);
            if (listeners.length === 0) {
                this._events.delete(event);
            }
        }

        return this;
    }

    /**
     * 发布事件
     * @param {string} event - 事件名称
     * @param {...any} args - 传递给回调的参数
     * @returns {boolean} 是否有监听器
     */
    emit(event, ...args) {
        const listeners = this._events.get(event);
        if (!listeners || listeners.length === 0) {
            return false;
        }

        // 复制监听器列表，避免在触发过程中被修改
        const listenersCopy = listeners.slice();

        for (const listener of listenersCopy) {
            try {
                listener.apply(this, args);
            } catch (error) {
                console.error(`[EventBus] 事件 "${event}" 的监听器抛出错误:`, error);
            }
        }

        return true;
    }

    /**
     * 获取事件的监听器数量
     * @param {string} event - 事件名称
     * @returns {number}
     */
    listenerCount(event) {
        const listeners = this._events.get(event);
        return listeners ? listeners.length : 0;
    }

    /**
     * 获取所有事件名称
     * @returns {string[]}
     */
    eventNames() {
        return Array.from(this._events.keys());
    }

    /**
     * 移除所有监听器
     * @param {string} [event] - 可选，指定事件名称；不传则移除所有
     * @returns {EventEmitter} this
     */
    removeAllListeners(event) {
        if (event) {
            this._events.delete(event);
        } else {
            this._events.clear();
        }
        return this;
    }

    /**
     * 获取监听器列表
     * @param {string} event - 事件名称
     * @returns {Function[]}
     */
    listeners(event) {
        const listeners = this._events.get(event);
        return listeners ? listeners.slice() : [];
    }
}

/**
 * 创建全局事件总线实例
 */
export const events = new EventEmitter();

/**
 * 预定义事件常量
 */
export const EventTypes = {
    // 设备连接相关
    DEVICE_CONNECTED: 'device:connected',
    DEVICE_CONNECT_FAILED: 'device:connect-failed',
    DEVICE_DISCONNECTED: 'device:disconnected',

    // 数据采集相关
    ACQUISITION_STARTED: 'acquisition:started',
    ACQUISITION_STOPPED: 'acquisition:stopped',
    ACQUISITION_ERROR: 'acquisition:error',
    SPECTRUM_READY: 'spectrum:ready',

    // 校准相关
    CALIBRATION_WAVELENGTH_SUCCESS: 'calibration:wavelength-success',
    CALIBRATION_WAVELENGTH_FAILED: 'calibration:wavelength-failed',
    CALIBRATION_INTENSITY_SUCCESS: 'calibration:intensity-success',
    CALIBRATION_INTENSITY_FAILED: 'calibration:intensity-failed',

    // UI 相关
    THEME_CHANGED: 'ui:theme-changed',
    PANEL_OPENED: 'ui:panel-opened',
    PANEL_CLOSED: 'ui:panel-closed',

    // 日志相关
    LOG_ADDED: 'log:added',
    LOG_CLEARED: 'log:cleared',

    // 错误相关
    ERROR_OCCURRED: 'error:occurred',
    WARNING_OCCURRED: 'warning:occurred',
};

/**
 * 创建事件总线管理器（带自动清理）
 * @returns {Object} 事件管理器
 */
export function createEventManager() {
    const subscriptions = new Map();

    /**
     * 订阅事件（自动跟踪）
     */
    function subscribe(event, listener) {
        if (!subscriptions.has(event)) {
            subscriptions.set(event, new Set());
        }
        subscriptions.get(event).add(listener);
        return events.on(event, listener);
    }

    /**
     * 取消订阅事件（自动清理）
     */
    function unsubscribe(event, listener) {
        if (listener) {
            const eventSubs = subscriptions.get(event);
            if (eventSubs) {
                eventSubs.delete(listener);
                if (eventSubs.size === 0) {
                    subscriptions.delete(event);
                }
            }
            return events.off(event, listener);
        } else {
            // 取消该事件的所有订阅
            const eventSubs = subscriptions.get(event);
            if (eventSubs) {
                eventSubs.forEach(listener => events.off(event, listener));
                subscriptions.delete(event);
            }
            return events.removeAllListeners(event);
        }
    }

    /**
     * 清理所有订阅
     */
    function cleanup() {
        subscriptions.forEach((listeners, event) => {
            listeners.forEach(listener => events.off(event, listener));
        });
        subscriptions.clear();
    }

    return {
        subscribe,
        unsubscribe,
        cleanup,
        emit: events.emit.bind(events),
        on: events.on.bind(events),
        once: events.once.bind(events),
        off: events.off.bind(events),
    };
}

export default events;
