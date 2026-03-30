/**
 * 焦点管理模块测试
 * @module test/focus-trap.test
 *
 * 测试范围:
 * - FocusTrap 基本功能
 * - 焦点陷阱激活/停用
 * - 可聚焦元素检测
 * - Tab 键导航
 * - 焦点陷阱管理器
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { FocusTrap, createFocusTrap, focusTrapManager, FocusTrapManager } from '@/focus-trap.js';

describe('FocusTrap', () => {
    let container;
    let trap;

    beforeEach(() => {
        // 创建测试容器
        container = document.createElement('div');
        container.innerHTML = `
            <button id="btn1">Button 1</button>
            <input id="input1" type="text" />
            <a id="link1" href="#">Link 1</a>
            <button id="btn2" disabled>Disabled Button</button>
            <button id="btn3">Button 3</button>
        `;
        document.body.appendChild(container);
    });

    afterEach(() => {
        if (trap && trap.isActive()) {
            trap.deactivate();
        }
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    });

    describe('基本功能', () => {
        it('应该能够创建实例', () => {
            trap = new FocusTrap(container);
            expect(trap).toBeInstanceOf(FocusTrap);
        });

        it('应该能够获取可聚焦元素', () => {
            trap = new FocusTrap(container);
            const elements = trap.getFocusableElements();
            // btn1, input1, link1, btn3 (btn2 被禁用)
            expect(elements.length).toBe(4);
        });

        it('应该能够获取第一个可聚焦元素', () => {
            trap = new FocusTrap(container);
            const first = trap.getFirstFocusableElement();
            expect(first.id).toBe('btn1');
        });

        it('应该能够获取最后一个可聚焦元素', () => {
            trap = new FocusTrap(container);
            const last = trap.getLastFocusableElement();
            expect(last.id).toBe('btn3');
        });
    });

    describe('激活/停用', () => {
        it('应该能够激活焦点陷阱', () => {
            trap = new FocusTrap(container);
            trap.activate();
            expect(trap.isActive()).toBe(true);
        });

        it('应该能够停用焦点陷阱', () => {
            trap = new FocusTrap(container);
            trap.activate();
            trap.deactivate();
            expect(trap.isActive()).toBe(false);
        });

        it('重复激活应该不报错', () => {
            trap = new FocusTrap(container);
            trap.activate();
            trap.activate();
            expect(trap.isActive()).toBe(true);
        });

        it('重复停用应该不报错', () => {
            trap = new FocusTrap(container);
            trap.activate();
            trap.deactivate();
            trap.deactivate();
            expect(trap.isActive()).toBe(false);
        });
    });

    describe('配置选项', () => {
        it('应该能够设置初始聚焦位置为 first', () => {
            const focusSpy = vi.spyOn(HTMLElement.prototype, 'focus');
            trap = new FocusTrap(container, { initialFocus: 'first' });
            trap.activate();
            expect(focusSpy).toHaveBeenCalled();
            focusSpy.mockRestore();
        });

        it('应该能够设置初始聚焦位置为 last', () => {
            const focusSpy = vi.spyOn(HTMLElement.prototype, 'focus');
            trap = new FocusTrap(container, { initialFocus: 'last' });
            trap.activate();
            expect(focusSpy).toHaveBeenCalled();
            focusSpy.mockRestore();
        });

        it('应该能够设置初始聚焦位置为 CSS 选择器', () => {
            const focusSpy = vi.spyOn(HTMLElement.prototype, 'focus');
            trap = new FocusTrap(container, { initialFocus: '#input1' });
            trap.activate();
            expect(focusSpy).toHaveBeenCalled();
            focusSpy.mockRestore();
        });

        it('应该能够禁用 ESC 键停用', () => {
            trap = new FocusTrap(container, { escapeDeactivates: false });
            trap.activate();
            expect(trap.isActive()).toBe(true);
            
            // 模拟 ESC 键按下
            const event = new KeyboardEvent('keydown', { key: 'Escape' });
            document.dispatchEvent(event);
            
            expect(trap.isActive()).toBe(true);
        });
    });

    describe('错误处理', () => {
        it('容器元素不存在应该抛出错误', () => {
            expect(() => new FocusTrap(null)).toThrow(TypeError);
        });

        it('容器为字符串选择器时应该正确处理', () => {
            expect(() => createFocusTrap('#nonexistent')).toThrow('容器元素不存在');
        });
    });
});

describe('createFocusTrap', () => {
    let container;

    beforeEach(() => {
        container = document.createElement('div');
        container.innerHTML = '<button>Button</button>';
        document.body.appendChild(container);
    });

    afterEach(() => {
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    });

    it('应该能够创建焦点陷阱', () => {
        const trap = createFocusTrap(container);
        expect(trap).toBeInstanceOf(FocusTrap);
    });

    it('应该能够接受字符串选择器', () => {
        container.id = 'test-container';
        const trap = createFocusTrap('#test-container');
        expect(trap).toBeInstanceOf(FocusTrap);
    });
});

describe('FocusTrapManager', () => {
    let manager;
    let container1;
    let container2;

    beforeEach(() => {
        manager = new FocusTrapManager();
        container1 = document.createElement('div');
        container1.id = 'container1';
        container1.innerHTML = '<button>Button 1</button>';
        container2 = document.createElement('div');
        container2.id = 'container2';
        container2.innerHTML = '<button>Button 2</button>';
        document.body.appendChild(container1);
        document.body.appendChild(container2);
    });

    afterEach(() => {
        manager.cleanup();
        if (container1 && container1.parentNode) {
            container1.parentNode.removeChild(container1);
        }
        if (container2 && container2.parentNode) {
            container2.parentNode.removeChild(container2);
        }
    });

    describe('基本功能', () => {
        it('应该能够注册焦点陷阱', () => {
            manager.register('trap1', container1);
            expect(manager._traps.has('trap1')).toBe(true);
        });

        it('应该能够激活焦点陷阱', () => {
            manager.register('trap1', container1);
            manager.activate('trap1');
            const trap = manager._traps.get('trap1');
            expect(trap.isActive()).toBe(true);
        });

        it('应该能够停用焦点陷阱', () => {
            manager.register('trap1', container1);
            manager.activate('trap1');
            manager.deactivate('trap1');
            const trap = manager._traps.get('trap1');
            expect(trap.isActive()).toBe(false);
        });

        it('应该能够移除焦点陷阱', () => {
            manager.register('trap1', container1);
            manager.remove('trap1');
            expect(manager._traps.has('trap1')).toBe(false);
        });

        it('应该能够清理所有焦点陷阱', () => {
            manager.register('trap1', container1);
            manager.register('trap2', container2);
            manager.cleanup();
            expect(manager._traps.size).toBe(0);
        });
    });

    describe('栈管理', () => {
        it('应该能够管理多个焦点陷阱的栈', () => {
            manager.register('trap1', container1);
            manager.register('trap2', container2);
            
            manager.activate('trap1');
            expect(manager._stack.length).toBe(1);
            
            manager.activate('trap2');
            expect(manager._stack.length).toBe(2);
            
            manager.deactivate('trap2');
            expect(manager._stack.length).toBe(1);
        });

        it('停用后应该恢复上一个陷阱', () => {
            manager.register('trap1', container1);
            manager.register('trap2', container2);
            
            manager.activate('trap1');
            manager.activate('trap2');
            
            const trap1 = manager._traps.get('trap1');
            const trap2 = manager._traps.get('trap2');
            
            expect(trap2.isActive()).toBe(true);
            expect(trap1.isActive()).toBe(false);
            
            manager.deactivate('trap2');
            
            expect(trap1.isActive()).toBe(true);
        });
    });

    describe('错误处理', () => {
        it('重复注册应该抛出错误', () => {
            manager.register('trap1', container1);
            expect(() => manager.register('trap1', container1)).toThrow('已存在');
        });

        it('激活不存在的陷阱应该抛出错误', () => {
            expect(() => manager.activate('nonexistent')).toThrow('不存在');
        });
    });
});

describe('focusTrapManager 单例', () => {
    it('应该导出 focusTrapManager 单例', () => {
        expect(focusTrapManager).toBeInstanceOf(FocusTrapManager);
    });
});
