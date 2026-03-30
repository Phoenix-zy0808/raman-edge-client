/**
 * 电路断路器模块测试
 * @module test/circuit-breaker.test
 *
 * 测试范围:
 * - CircuitBreaker 基本功能
 * - 状态转换
 * - 熔断保护
 * - 自动恢复
 * - 统计信息
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CircuitBreaker, CircuitState, backendBreaker, channelBreaker } from '@/circuit-breaker.js';

describe('CircuitBreaker', () => {
    let breaker;

    beforeEach(() => {
        breaker = new CircuitBreaker({
            threshold: 3,
            timeout: 1000,
            name: 'TestBreaker',
        });
    });

    describe('基本功能', () => {
        it('应该能够创建实例', () => {
            expect(breaker).toBeInstanceOf(CircuitBreaker);
        });

        it('初始状态应该是 CLOSED', () => {
            expect(breaker.state).toBe(CircuitState.CLOSED);
        });

        it('应该能够获取统计信息', () => {
            const stats = breaker.getStats();
            expect(stats.name).toBe('TestBreaker');
            expect(stats.state).toBe('CLOSED');
            expect(stats.threshold).toBe(3);
            expect(stats.timeout).toBe(1000);
        });
    });

    describe('状态检查', () => {
        it('应该能够检查是否可用', () => {
            expect(breaker.isAvailable()).toBe(true);
            expect(breaker.isClosed()).toBe(true);
            expect(breaker.isOpen()).toBe(false);
        });

        it('打开后应该不可用', () => {
            breaker.open();
            expect(breaker.isAvailable()).toBe(false);
            expect(breaker.isClosed()).toBe(false);
            expect(breaker.isOpen()).toBe(true);
        });
    });

    describe('执行函数', () => {
        it('应该能够执行成功的函数', async () => {
            const fn = vi.fn().mockResolvedValue('success');
            const result = await breaker.execute(fn);
            expect(result).toBe('success');
            expect(fn).toHaveBeenCalledTimes(1);
        });

        it('应该能够处理失败的函数', async () => {
            const fn = vi.fn().mockRejectedValue(new Error('Test error'));
            await expect(breaker.execute(fn)).rejects.toThrow('Test error');
        });

        it('成功后应该重置失败计数', async () => {
            const fn = vi.fn().mockResolvedValue('success');
            await breaker.execute(fn);
            await breaker.execute(fn);
            expect(breaker.failureCount).toBe(0);
        });
    });

    describe('熔断保护', () => {
        it('达到阈值后应该熔断', async () => {
            const fn = vi.fn().mockRejectedValue(new Error('Error'));
            
            // 连续失败 3 次
            for (let i = 0; i < 3; i++) {
                try {
                    await breaker.execute(fn);
                } catch (e) {
                    // 忽略错误
                }
            }
            
            expect(breaker.state).toBe(CircuitState.OPEN);
        });

        it('熔断后应该拒绝执行', async () => {
            const fn = vi.fn().mockRejectedValue(new Error('Error'));
            
            // 触发熔断
            for (let i = 0; i < 3; i++) {
                try {
                    await breaker.execute(fn);
                } catch (e) {}
            }
            
            // 熔断后执行应该立即失败
            await expect(breaker.execute(fn)).rejects.toThrow('电路熔断中');
            expect(fn).toHaveBeenCalledTimes(3);
        });

        it('超时后应该进入半开状态', async () => {
            const fn = vi.fn().mockRejectedValue(new Error('Error'));
            
            // 触发熔断
            for (let i = 0; i < 3; i++) {
                try {
                    await breaker.execute(fn);
                } catch (e) {}
            }
            
            // 等待超时
            await new Promise(resolve => setTimeout(resolve, 1100));
            
            // 半开状态
            expect(breaker.state).toBe(CircuitState.HALF_OPEN);
        });

        it('半开状态成功应该恢复', async () => {
            const fn = vi.fn()
                .mockRejectedValueOnce(new Error('Error'))
                .mockRejectedValueOnce(new Error('Error'))
                .mockRejectedValueOnce(new Error('Error'))
                .mockResolvedValueOnce('success');
            
            // 触发熔断
            for (let i = 0; i < 3; i++) {
                try {
                    await breaker.execute(fn);
                } catch (e) {}
            }
            
            // 等待超时
            await new Promise(resolve => setTimeout(resolve, 1100));
            
            // 成功执行
            const result = await breaker.execute(fn);
            expect(result).toBe('success');
            expect(breaker.state).toBe(CircuitState.CLOSED);
        });

        it('半开状态失败应该重新熔断', async () => {
            const fn = vi.fn()
                .mockRejectedValueOnce(new Error('Error'))
                .mockRejectedValueOnce(new Error('Error'))
                .mockRejectedValueOnce(new Error('Error'))
                .mockRejectedValueOnce(new Error('Error'));
            
            // 触发熔断
            for (let i = 0; i < 3; i++) {
                try {
                    await breaker.execute(fn);
                } catch (e) {}
            }
            
            // 等待超时
            await new Promise(resolve => setTimeout(resolve, 1100));
            
            // 失败执行
            await expect(breaker.execute(fn)).rejects.toThrow();
            expect(breaker.state).toBe(CircuitState.OPEN);
        });
    });

    describe('重置功能', () => {
        it('应该能够重置断路器', async () => {
            const fn = vi.fn().mockRejectedValue(new Error('Error'));
            
            // 触发熔断
            for (let i = 0; i < 3; i++) {
                try {
                    await breaker.execute(fn);
                } catch (e) {}
            }
            
            expect(breaker.state).toBe(CircuitState.OPEN);
            
            // 重置
            breaker.reset();
            expect(breaker.state).toBe(CircuitState.CLOSED);
            expect(breaker.failureCount).toBe(0);
        });
    });

    describe('状态变化回调', () => {
        it('应该能够注册状态变化回调', () => {
            const callback = vi.fn();
            breaker.onStateChange(callback);
            breaker.open();
            expect(callback).toHaveBeenCalledWith(
                CircuitState.OPEN,
                CircuitState.CLOSED,
                expect.any(Object)
            );
        });

        it('应该能够移除状态变化回调', () => {
            const callback = vi.fn();
            breaker.onStateChange(callback);
            breaker.offStateChange(callback);
            breaker.open();
            expect(callback).not.toHaveBeenCalled();
        });

        it('应该能够处理多个回调', () => {
            const callback1 = vi.fn();
            const callback2 = vi.fn();
            breaker.onStateChange(callback1);
            breaker.onStateChange(callback2);
            breaker.open();
            expect(callback1).toHaveBeenCalled();
            expect(callback2).toHaveBeenCalled();
        });
    });

    describe('包装 Promise', () => {
        it('应该能够包装 Promise', async () => {
            const promise = Promise.resolve('success');
            const result = await breaker.wrap(promise);
            expect(result).toBe('success');
        });

        it('应该能够处理失败的 Promise', async () => {
            const promise = Promise.reject(new Error('Error'));
            await expect(breaker.wrap(promise)).rejects.toThrow('Error');
        });
    });
});

describe('CircuitState', () => {
    it('应该包含所有状态常量', () => {
        expect(CircuitState.CLOSED).toBe('CLOSED');
        expect(CircuitState.OPEN).toBe('OPEN');
        expect(CircuitState.HALF_OPEN).toBe('HALF_OPEN');
    });
});

describe('预定义断路器', () => {
    it('应该导出 backendBreaker', () => {
        expect(backendBreaker).toBeInstanceOf(CircuitBreaker);
    });

    it('应该导出 channelBreaker', () => {
        expect(channelBreaker).toBeInstanceOf(CircuitBreaker);
    });
});
