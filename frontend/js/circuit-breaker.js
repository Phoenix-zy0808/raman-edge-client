/**
 * 电路断路器模块
 * @module circuit-breaker
 *
 * 防止连续失败导致系统雪崩，提供熔断保护
 *
 * 状态机:
 * CLOSED (闭合) → 正常状态，允许请求通过
 *    ↓ 失败次数达到阈值
 * OPEN (断开) → 熔断状态，拒绝所有请求
 *    ↓ 超时时间到达
 * HALF_OPEN (半开) → 测试状态，允许一个请求通过
 *    ↓ 成功 → CLOSED
 *    ↓ 失败 → OPEN
 *
 * @example
 * const breaker = new CircuitBreaker({
 *     threshold: 3,      // 失败 3 次后熔断
 *     timeout: 30000,    // 熔断 30 秒
 *     name: 'BackendAPI' // 断路器名称
 * });
 *
 * // 使用
 * const result = await breaker.execute(() => callBackendApi(...));
 *
 * // 监听状态变化
 * breaker.onStateChange((state) => {
 *     console.log('状态变化:', state);
 * });
 */

/**
 * 电路断路器状态枚举
 */
export const CircuitState = {
    CLOSED: 'CLOSED',       // 闭合 - 正常
    OPEN: 'OPEN',           // 断开 - 熔断
    HALF_OPEN: 'HALF_OPEN', // 半开 - 测试
};

/**
 * 电路断路器类
 */
export class CircuitBreaker {
    /**
     * 创建电路断路器
     * @param {Object} options - 配置选项
     * @param {number} [options.threshold=3] - 失败阈值（达到此次数后熔断）
     * @param {number} [options.timeout=30000] - 熔断超时（毫秒）
     * @param {number} [options.halfOpenMaxAttempts=1] - 半开状态最大尝试次数
     * @param {string} [options.name='CircuitBreaker'] - 断路器名称
     * @param {Function} [options.onStateChange] - 状态变化回调
     */
    constructor(options = {}) {
        this.threshold = options.threshold || 3;
        this.timeout = options.timeout || 30000;
        this.halfOpenMaxAttempts = options.halfOpenMaxAttempts || 1;
        this.name = options.name || 'CircuitBreaker';

        this._state = CircuitState.CLOSED;
        this._failureCount = 0;
        this._successCount = 0;
        this._lastFailureTime = null;
        this._nextAttemptTime = null;
        this._halfOpenAttempts = 0;
        this._stateChangeCallbacks = [];

        // 状态变化日志
        this._verbose = options.verbose || false;
    }

    /**
     * 获取当前状态
     * @returns {string} 状态
     */
    get state() {
        return this._state;
    }

    /**
     * 获取失败次数
     * @returns {number}
     */
    get failureCount() {
        return this._failureCount;
    }

    /**
     * 获取成功次数
     * @returns {number}
     */
    get successCount() {
        return this._successCount;
    }

    /**
     * 检查是否可用
     * @returns {boolean}
     */
    isAvailable() {
        return this._state === CircuitState.CLOSED || this._state === CircuitState.HALF_OPEN;
    }

    /**
     * 检查是否处于熔断状态
     * @returns {boolean}
     */
    isOpen() {
        return this._state === CircuitState.OPEN;
    }

    /**
     * 检查是否处于闭合状态
     * @returns {boolean}
     */
    isClosed() {
        return this._state === CircuitState.CLOSED;
    }

    /**
     * 获取统计信息
     * @returns {Object} 统计数据
     */
    getStats() {
        return {
            name: this.name,
            state: this._state,
            failureCount: this._failureCount,
            successCount: this._successCount,
            threshold: this.threshold,
            timeout: this.timeout,
            lastFailureTime: this._lastFailureTime,
            nextAttemptTime: this._nextAttemptTime,
        };
    }

    /**
     * 重置断路器
     */
    reset() {
        const oldState = this._state;
        this._state = CircuitState.CLOSED;
        this._failureCount = 0;
        this._successCount = 0;
        this._lastFailureTime = null;
        this._nextAttemptTime = null;
        this._halfOpenAttempts = 0;

        if (oldState !== CircuitState.CLOSED) {
            this._log(`断路器已重置为 ${CircuitState.CLOSED}`);
            this._notifyStateChange();
        }
    }

    /**
     * 强制打开断路器
     */
    open() {
        const oldState = this._state;
        this._state = CircuitState.OPEN;
        this._nextAttemptTime = Date.now() + this.timeout;

        this._log(`断路器被强制打开，将在 ${this.timeout}ms 后尝试恢复`);
        this._notifyStateChange();
    }

    /**
     * 执行函数，带熔断保护
     * @template T
     * @param {Function} fn - 要执行的异步函数
     * @param {Object} [options] - 执行选项
     * @param {boolean} [options.recordStats=true] - 是否记录统计
     * @returns {Promise<T>} 执行结果
     */
    async execute(fn, options = {}) {
        const recordStats = options.recordStats !== false;

        // 检查状态
        if (this._state === CircuitState.OPEN) {
            // 检查是否可以进入半开状态
            if (this._nextAttemptTime && Date.now() >= this._nextAttemptTime) {
                this._transitionToHalfOpen();
            } else {
                const error = new Error(`电路熔断中，拒绝执行 [${this.name}]`);
                error.code = 'CIRCUIT_OPEN';
                error.stats = this.getStats();
                throw error;
            }
        }

        // 半开状态下限制尝试次数
        if (this._state === CircuitState.HALF_OPEN) {
            if (this._halfOpenAttempts >= this.halfOpenMaxAttempts) {
                const error = new Error(`电路半开状态已达最大尝试次数 [${this.name}]`);
                error.code = 'CIRCUIT_HALF_OPEN_MAX_ATTEMPTS';
                error.stats = this.getStats();
                throw error;
            }
            this._halfOpenAttempts++;
        }

        try {
            // 执行函数
            const result = await fn();

            // 成功
            if (recordStats) {
                this._onSuccess();
            }

            return result;
        } catch (error) {
            // 失败
            if (recordStats) {
                this._onFailure();
            }

            // 包装错误，添加断路器信息
            error.circuitBreaker = this.getStats();
            throw error;
        }
    }

    /**
     * 包装 Promise，带熔断保护
     * @template T
     * @param {Promise<T>} promise - 要执行的 Promise
     * @returns {Promise<T>}
     */
    async wrap(promise) {
        return this.execute(() => promise);
    }

    /**
     * 注册状态变化回调
     * @param {Function} callback - 回调函数，接收新状态和旧状态
     */
    onStateChange(callback) {
        this._stateChangeCallbacks.push(callback);
    }

    /**
     * 移除状态变化回调
     * @param {Function} callback - 要移除的回调
     */
    offStateChange(callback) {
        const index = this._stateChangeCallbacks.indexOf(callback);
        if (index !== -1) {
            this._stateChangeCallbacks.splice(index, 1);
        }
    }

    /**
     * 成功处理
     * @private
     */
    _onSuccess() {
        this._successCount++;
        this._failureCount = 0;

        if (this._state === CircuitState.HALF_OPEN) {
            // 半开状态下成功，恢复到闭合状态
            this._transitionToClosed();
        } else if (this._failureCount >= this.threshold) {
            // 如果之前已达到阈值，现在恢复了
            this._log('连续成功，断路器恢复正常');
        }
    }

    /**
     * 失败处理
     * @private
     */
    _onFailure() {
        this._failureCount++;
        this._lastFailureTime = Date.now();

        if (this._state === CircuitState.HALF_OPEN) {
            // 半开状态下失败，重新打开
            this._transitionToOpen();
        } else if (this._failureCount >= this.threshold) {
            // 达到阈值，打开断路器
            this._transitionToOpen();
        } else {
            this._log(`失败次数：${this._failureCount}/${this.threshold}`);
        }
    }

    /**
     * 转换到闭合状态
     * @private
     */
    _transitionToClosed() {
        const oldState = this._state;
        this._state = CircuitState.CLOSED;
        this._halfOpenAttempts = 0;
        this._nextAttemptTime = null;

        this._log(`断路器已恢复为 ${CircuitState.CLOSED} 状态`);
        this._notifyStateChange(oldState);
    }

    /**
     * 转换到断开状态
     * @private
     */
    _transitionToOpen() {
        const oldState = this._state;
        this._state = CircuitState.OPEN;
        this._nextAttemptTime = Date.now() + this.timeout;
        this._halfOpenAttempts = 0;

        this._log(`断路器已打开，将在 ${this.timeout}ms 后尝试恢复`);
        this._notifyStateChange(oldState);
    }

    /**
     * 转换到半开状态
     * @private
     */
    _transitionToHalfOpen() {
        const oldState = this._state;
        this._state = CircuitState.HALF_OPEN;
        this._halfOpenAttempts = 0;

        this._log(`断路器进入 ${CircuitState.HALF_OPEN} 状态`);
        this._notifyStateChange(oldState);
    }

    /**
     * 通知状态变化
     * @private
     */
    _notifyStateChange(oldState) {
        const newState = this._state;
        this._stateChangeCallbacks.forEach(callback => {
            try {
                callback(newState, oldState, this.getStats());
            } catch (error) {
                console.error(`[CircuitBreaker] 状态变化回调出错:`, error);
            }
        });
    }

    /**
     * 日志记录
     * @private
     */
    _log(message) {
        if (this._verbose) {
            console.log(`[CircuitBreaker:${this.name}] ${message}`);
        }
    }
}

/**
 * 创建默认的后端 API 断路器
 */
export const backendBreaker = new CircuitBreaker({
    threshold: 3,
    timeout: 30000,
    name: 'BackendAPI',
    verbose: true,
});

/**
 * 创建 QWebChannel 通信断路器
 */
export const channelBreaker = new CircuitBreaker({
    threshold: 5,
    timeout: 10000,
    name: 'QWebChannel',
    verbose: true,
});

export default CircuitBreaker;
