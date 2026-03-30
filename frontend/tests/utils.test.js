/**
 * 工具函数模块测试
 * @see utils.js
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { debounce, throttle, createEventCleanup, createTimerManager } from '../js/utils.js';

describe('utils.js', () => {
  describe('debounce（防抖函数）', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('应该在延迟后执行函数', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('应该重置计时器当多次调用时', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      vi.advanceTimersByTime(50);
      debouncedFn(); // 重置计时器
      vi.advanceTimersByTime(50);
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(100);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('应该保持 this 上下文', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);
      const context = { value: 42 };

      debouncedFn.call(context);
      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledWith();
      expect(fn).toHaveBeenLastCalledWith();
    });

    it('应该传递参数给函数', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn('arg1', 'arg2');
      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
    });
  });

  describe('throttle（节流函数）', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('应该在间隔内只执行一次', () => {
      const fn = vi.fn();
      const throttledFn = throttle(fn, 100);

      throttledFn();
      throttledFn();
      throttledFn();

      expect(fn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(100);
      throttledFn();
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('应该在间隔后允许再次执行', () => {
      const fn = vi.fn();
      const throttledFn = throttle(fn, 100);

      throttledFn();  // t=0, 立即执行 (1 次)
      expect(fn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(50);  // t=50
      throttledFn();  // t=50, 在间隔内，设置定时器
      expect(fn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(50);  // t=100, 定时器触发 (2 次)
      expect(fn).toHaveBeenCalledTimes(2);

      vi.advanceTimersByTime(100);  // t=200, 现在距离上次调用已过去 100ms
      throttledFn();  // t=200, 可以立即执行 (3 次)
      expect(fn).toHaveBeenCalledTimes(3);
    });
  });

  describe('createEventCleanup（事件监听器管理器）', () => {
    let cleanup;
    let target;
    let handler;

    beforeEach(() => {
      cleanup = createEventCleanup();
      target = document.createElement('div');
      document.body.appendChild(target);
      handler = vi.fn();
    });

    afterEach(() => {
      cleanup.removeAll();
      document.body.removeChild(target);
    });

    it('应该添加事件监听器', () => {
      cleanup.add(target, 'click', handler);
      target.click();
      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('应该移除所有事件监听器', () => {
      cleanup.add(target, 'click', handler);
      cleanup.removeAll();
      target.click();
      expect(handler).not.toHaveBeenCalled();
    });

    it('应该返回移除函数', () => {
      const remove = cleanup.add(target, 'click', handler);
      remove();
      target.click();
      expect(handler).not.toHaveBeenCalled();
    });

    it('应该跟踪监听器数量', () => {
      cleanup.add(target, 'click', handler);
      cleanup.add(target, 'mouseover', handler);
      expect(cleanup.getCount()).toBe(2);
    });
  });

  describe('createTimerManager（定时器管理器）', () => {
    let timerManager;

    beforeEach(() => {
      vi.useFakeTimers();
      timerManager = createTimerManager();
    });

    afterEach(() => {
      timerManager.clearAll();
      vi.useRealTimers();
    });

    it('应该管理 setTimeout', () => {
      const fn = vi.fn();
      timerManager.setTimeout(fn, 100);
      
      expect(fn).not.toHaveBeenCalled();
      vi.advanceTimersByTime(100);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('应该管理 setInterval', () => {
      const fn = vi.fn();
      timerManager.setInterval(fn, 100);

      vi.advanceTimersByTime(250);
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('应该清除所有定时器', () => {
      const fn1 = vi.fn();
      const fn2 = vi.fn();
      
      timerManager.setTimeout(fn1, 100);
      timerManager.setInterval(fn2, 100);
      
      timerManager.clearAll();
      
      vi.advanceTimersByTime(200);
      expect(fn1).not.toHaveBeenCalled();
      expect(fn2).not.toHaveBeenCalled();
    });

    it('应该跟踪定时器数量', () => {
      timerManager.setTimeout(() => {}, 100);
      timerManager.setInterval(() => {}, 100);
      
      const count = timerManager.getCount();
      expect(count.timeouts).toBe(1);
      expect(count.intervals).toBe(1);
    });
  });
});
