/**
 * 焦点管理模块
 * @module focus-trap
 *
 * 提供焦点陷阱功能，确保键盘用户在对话框等模态组件中操作时，
 * 焦点不会跑到组件外部，符合无障碍访问（A11y）标准
 *
 * @example
 * // 在对话框中使用
 * const dialog = document.getElementById('my-dialog');
 * const focusTrap = createFocusTrap(dialog);
 *
 * // 激活焦点陷阱
 * focusTrap.activate();
 *
 * // 停用焦点陷阱
 * focusTrap.deactivate();
 */

/**
 * 可聚焦元素选择器
 */
const FOCUSABLE_SELECTORS = [
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'a[href]',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable]',
].join(', ');

/**
 * 焦点陷阱类
 */
export class FocusTrap {
    /**
     * 创建焦点陷阱
     * @param {HTMLElement} container - 容器元素
     * @param {Object} options - 配置选项
     * @param {string} [options.initialFocus='first'] - 初始聚焦位置 ('first' | 'last' | CSS 选择器)
     * @param {boolean} [options.escapeDeactivates=true] - ESC 键是否停用
     * @param {Function} [options.onActivate] - 激活回调
     * @param {Function} [options.onDeactivate] - 停用回调
     */
    constructor(container, options = {}) {
        if (!(container instanceof HTMLElement)) {
            throw new TypeError('container 必须是 HTMLElement');
        }

        this.container = container;
        this.options = {
            initialFocus: options.initialFocus || 'first',
            escapeDeactivates: options.escapeDeactivates !== false,
            onActivate: options.onActivate || (() => {}),
            onDeactivate: options.onDeactivate || (() => {}),
        };

        this._active = false;
        this._previousActiveElement = null;
        this._handleTabKey = this._handleTabKey.bind(this);
        this._handleKeyDown = this._handleKeyDown.bind(this);
    }

    /**
     * 获取所有可聚焦元素
     * @returns {HTMLElement[]}
     */
    getFocusableElements() {
        const elements = this.container.querySelectorAll(FOCUSABLE_SELECTORS);
        return Array.from(elements).filter(el => {
            // 过滤掉不可见的元素
            return el.offsetParent !== null &&
                   getComputedStyle(el).visibility !== 'hidden' &&
                   !el.hasAttribute('inert');
        });
    }

    /**
     * 获取第一个可聚焦元素
     * @returns {HTMLElement|null}
     */
    getFirstFocusableElement() {
        const elements = this.getFocusableElements();
        return elements.length > 0 ? elements[0] : null;
    }

    /**
     * 获取最后一个可聚焦元素
     * @returns {HTMLElement|null}
     */
    getLastFocusableElement() {
        const elements = this.getFocusableElements();
        return elements.length > 0 ? elements[elements.length - 1] : null;
    }

    /**
     * 激活焦点陷阱
     * @returns {FocusTrap} this
     */
    activate() {
        if (this._active) {
            return this;
        }

        // 保存当前聚焦元素
        this._previousActiveElement = document.activeElement;

        // 添加事件监听
        document.addEventListener('keydown', this._handleKeyDown);
        this.container.addEventListener('keydown', this._handleTabKey);

        // 聚焦到初始位置
        this._setInitialFocus();

        this._active = true;
        this.options.onActivate(this);

        return this;
    }

    /**
     * 停用焦点陷阱
     * @returns {FocusTrap} this
     */
    deactivate() {
        if (!this._active) {
            return this;
        }

        // 移除事件监听
        document.removeEventListener('keydown', this._handleKeyDown);
        this.container.removeEventListener('keydown', this._handleTabKey);

        // 恢复之前的聚焦元素
        if (this._previousActiveElement && typeof this._previousActiveElement.focus === 'function') {
            this._previousActiveElement.focus();
        }

        this._active = false;
        this.options.onDeactivate(this);

        return this;
    }

    /**
     * 检查是否激活
     * @returns {boolean}
     */
    isActive() {
        return this._active;
    }

    /**
     * 设置初始聚焦
     * @private
     */
    _setInitialFocus() {
        const { initialFocus } = this.options;

        if (initialFocus === 'first') {
            const first = this.getFirstFocusableElement();
            if (first) {
                setTimeout(() => first.focus(), 0);
            }
        } else if (initialFocus === 'last') {
            const last = this.getLastFocusableElement();
            if (last) {
                setTimeout(() => last.focus(), 0);
            }
        } else if (typeof initialFocus === 'string') {
            const element = this.container.querySelector(initialFocus);
            if (element && typeof element.focus === 'function') {
                setTimeout(() => element.focus(), 0);
            }
        }
    }

    /**
     * 处理 Tab 键
     * @private
     */
    _handleTabKey(event) {
        if (event.key !== 'Tab') {
            return;
        }

        const focusableElements = this.getFocusableElements();
        if (focusableElements.length === 0) {
            return;
        }

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const activeElement = document.activeElement;

        if (event.shiftKey) {
            // Shift + Tab：反向导航
            if (activeElement === firstElement || !this.container.contains(activeElement)) {
                event.preventDefault();
                lastElement.focus();
            }
        } else {
            // Tab：正向导航
            if (activeElement === lastElement || !this.container.contains(activeElement)) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    }

    /**
     * 处理其他按键
     * @private
     */
    _handleKeyDown(event) {
        // ESC 键处理
        if (this.options.escapeDeactivates && event.key === 'Escape') {
            this.deactivate();
        }
    }
}

/**
 * 创建焦点陷阱
 * @param {HTMLElement|string} container - 容器元素或选择器
 * @param {Object} [options] - 配置选项
 * @returns {FocusTrap}
 */
export function createFocusTrap(container, options = {}) {
    const element = typeof container === 'string'
        ? document.querySelector(container)
        : container;

    if (!element) {
        throw new Error('容器元素不存在');
    }

    return new FocusTrap(element, options);
}

/**
 * 焦点陷阱管理器（管理多个焦点陷阱）
 */
export class FocusTrapManager {
    constructor() {
        this._traps = new Map();
        this._stack = [];
    }

    /**
     * 注册焦点陷阱
     * @param {string} id - 陷阱 ID
     * @param {HTMLElement} container - 容器元素
     * @param {Object} [options] - 配置选项
     */
    register(id, container, options = {}) {
        if (this._traps.has(id)) {
            throw new Error(`焦点陷阱 "${id}" 已存在`);
        }

        const trap = createFocusTrap(container, options);
        this._traps.set(id, trap);
    }

    /**
     * 激活焦点陷阱
     * @param {string} id - 陷阱 ID
     */
    activate(id) {
        const trap = this._traps.get(id);
        if (!trap) {
            throw new Error(`焦点陷阱 "${id}" 不存在`);
        }

        // 停用当前激活的陷阱
        if (this._stack.length > 0) {
            const currentTop = this._stack[this._stack.length - 1];
            if (currentTop && currentTop.isActive()) {
                currentTop.deactivate();
            }
        }

        trap.activate();
        this._stack.push(trap);
    }

    /**
     * 停用焦点陷阱
     * @param {string} id - 陷阱 ID
     */
    deactivate(id) {
        const trap = this._traps.get(id);
        if (!trap) {
            return;
        }

        trap.deactivate();

        // 从栈中移除
        const index = this._stack.indexOf(trap);
        if (index !== -1) {
            this._stack.splice(index, 1);
        }

        // 恢复上一个陷阱
        if (this._stack.length > 0) {
            const previousTop = this._stack[this._stack.length - 1];
            if (previousTop) {
                previousTop.activate();
            }
        }
    }

    /**
     * 移除焦点陷阱
     * @param {string} id - 陷阱 ID
     */
    remove(id) {
        const trap = this._traps.get(id);
        if (trap) {
            trap.deactivate();
            this._traps.delete(id);
        }
    }

    /**
     * 清理所有焦点陷阱
     */
    cleanup() {
        this._traps.forEach(trap => trap.deactivate());
        this._traps.clear();
        this._stack = [];
    }
}

/**
 * 创建焦点陷阱管理器实例
 */
export const focusTrapManager = new FocusTrapManager();

export default createFocusTrap;
