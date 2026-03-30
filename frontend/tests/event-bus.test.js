/**
 * 事件总线模块测试
 * @module test/event-bus.test
 *
 * 测试范围:
 * - EventEmitter 基本功能
 * - 事件订阅/取消订阅
 * - 事件发布
 * - 一次性订阅
 * - 事件管理器
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { EventEmitter, events, EventTypes, createEventManager } from '@/event-bus.js';

describe('EventEmitter', () => {
    let emitter;

    beforeEach(() => {
        emitter = new EventEmitter();
    });

    describe('基本功能', () => {
        it('应该能够创建实例', () => {
            expect(emitter).toBeInstanceOf(EventEmitter);
        });

        it('应该能够设置最大监听器数量', () => {
            emitter.setMaxListeners(20);
            expect(emitter.getMaxListeners()).toBe(20);
        });

        it('默认最大监听器数量应为 10', () => {
            expect(emitter.getMaxListeners()).toBe(10);
        });
    });

    describe('事件订阅', () => {
        it('应该能够订阅事件', () => {
            const callback = vi.fn();
            emitter.on('test', callback);
            expect(emitter.listenerCount('test')).toBe(1);
        });

        it('应该能够取消订阅事件', () => {
            const callback = vi.fn();
            emitter.on('test', callback);
            emitter.off('test', callback);
            expect(emitter.listenerCount('test')).toBe(0);
        });

        it('应该能够取消所有订阅', () => {
            const callback1 = vi.fn();
            const callback2 = vi.fn();
            emitter.on('test', callback1);
            emitter.on('test', callback2);
            emitter.off('test');
            expect(emitter.listenerCount('test')).toBe(0);
        });

        it('应该能够获取所有事件名称', () => {
            emitter.on('event1', vi.fn());
            emitter.on('event2', vi.fn());
            const eventNames = emitter.eventNames();
            expect(eventNames).toEqual(['event1', 'event2']);
        });
    });

    describe('事件发布', () => {
        it('应该能够发布事件', () => {
            const callback = vi.fn();
            emitter.on('test', callback);
            emitter.emit('test', 'data');
            expect(callback).toHaveBeenCalledWith('data');
        });

        it('应该能够发布多个参数', () => {
            const callback = vi.fn();
            emitter.on('test', callback);
            emitter.emit('test', 'arg1', 'arg2', 'arg3');
            expect(callback).toHaveBeenCalledWith('arg1', 'arg2', 'arg3');
        });

        it('应该返回是否有监听器', () => {
            emitter.on('test', vi.fn());
            expect(emitter.emit('test')).toBe(true);
            expect(emitter.emit('nonexistent')).toBe(false);
        });

        it('应该能够处理多个监听器', () => {
            const callback1 = vi.fn();
            const callback2 = vi.fn();
            emitter.on('test', callback1);
            emitter.on('test', callback2);
            emitter.emit('test');
            expect(callback1).toHaveBeenCalled();
            expect(callback2).toHaveBeenCalled();
        });
    });

    describe('一次性订阅', () => {
        it('应该能够一次性订阅事件', () => {
            const callback = vi.fn();
            emitter.once('test', callback);
            emitter.emit('test');
            emitter.emit('test');
            expect(callback).toHaveBeenCalledTimes(1);
        });

        it('应该能够取消一次性订阅', () => {
            const callback = vi.fn();
            emitter.once('test', callback);
            emitter.off('test', callback);
            emitter.emit('test');
            expect(callback).not.toHaveBeenCalled();
        });
    });

    describe('错误处理', () => {
        it('应该能够处理监听器抛出的错误', () => {
            const errorCallback = vi.fn(() => { throw new Error('Test error'); });
            const normalCallback = vi.fn();
            emitter.on('test', errorCallback);
            emitter.on('test', normalCallback);
            
            expect(() => emitter.emit('test')).not.toThrow();
            expect(normalCallback).toHaveBeenCalled();
        });

        it('订阅非函数应该抛出错误', () => {
            expect(() => emitter.on('test', 'not a function')).toThrow(TypeError);
        });
    });

    describe('监听器管理', () => {
        it('应该能够获取监听器列表', () => {
            const callback = vi.fn();
            emitter.on('test', callback);
            const listeners = emitter.listeners('test');
            expect(listeners).toHaveLength(1);
            expect(listeners[0]).toBe(callback);
        });

        it('获取的监听器列表应该是副本', () => {
            const callback = vi.fn();
            emitter.on('test', callback);
            const listeners = emitter.listeners('test');
            emitter.off('test', callback);
            expect(listeners).toHaveLength(1);
        });

        it('应该能够移除所有监听器', () => {
            emitter.on('test1', vi.fn());
            emitter.on('test2', vi.fn());
            emitter.removeAllListeners();
            expect(emitter.eventNames()).toHaveLength(0);
        });

        it('应该能够移除指定事件的所有监听器', () => {
            emitter.on('test1', vi.fn());
            emitter.on('test2', vi.fn());
            emitter.removeAllListeners('test1');
            expect(emitter.listenerCount('test1')).toBe(0);
            expect(emitter.listenerCount('test2')).toBe(1);
        });
    });
});

describe('EventTypes', () => {
    it('应该包含预定义的事件类型', () => {
        expect(EventTypes.DEVICE_CONNECTED).toBe('device:connected');
        expect(EventTypes.DEVICE_CONNECT_FAILED).toBe('device:connect-failed');
        expect(EventTypes.ACQUISITION_STARTED).toBe('acquisition:started');
        expect(EventTypes.SPECTRUM_READY).toBe('spectrum:ready');
    });
});

describe('createEventManager', () => {
    let manager;

    beforeEach(() => {
        manager = createEventManager();
    });

    it('应该能够创建事件管理器', () => {
        expect(manager).toHaveProperty('subscribe');
        expect(manager).toHaveProperty('unsubscribe');
        expect(manager).toHaveProperty('cleanup');
        expect(manager).toHaveProperty('emit');
    });

    it('应该能够订阅和取消订阅事件', () => {
        const callback = vi.fn();
        manager.subscribe('test', callback);
        manager.emit('test', 'data');
        expect(callback).toHaveBeenCalledWith('data');

        manager.unsubscribe('test', callback);
        manager.emit('test');
        expect(callback).toHaveBeenCalledTimes(1);
    });

    it('应该能够清理所有订阅', () => {
        const callback = vi.fn();
        manager.subscribe('test', callback);
        manager.cleanup();
        manager.emit('test');
        expect(callback).not.toHaveBeenCalled();
    });
});

describe('全局 events 实例', () => {
    it('应该导出全局 events 实例', () => {
        expect(events).toBeInstanceOf(EventEmitter);
    });
});
