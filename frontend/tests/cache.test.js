/**
 * 缓存模块测试（SWR 模式）
 * @see cache.js
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  swr,
  getCache,
  setCache,
  deleteCache,
  clearCache,
  generateCacheKey,
  cleanupExpiredCache,
  getCacheStats,
  prefetch,
  SWRConfig
} from '../js/cache.js';

describe('cache.js (SWR)', () => {
  beforeEach(() => {
    clearCache();
    vi.useFakeTimers();
  });

  afterEach(() => {
    clearCache();
    vi.useRealTimers();
  });

  describe('generateCacheKey', () => {
    it('应该生成简单键', () => {
      const key = generateCacheKey('test');
      expect(key).toBe('test');
    });

    it('应该生成带参数的键', () => {
      const key = generateCacheKey('test', { a: 1, b: 2 });
      expect(key).toBe('test:a=1&b=2');
    });

    it('应该对参数排序以保证一致性', () => {
      const key1 = generateCacheKey('test', { b: 2, a: 1 });
      const key2 = generateCacheKey('test', { a: 1, b: 2 });
      expect(key1).toBe(key2);
    });
  });

  describe('setCache / getCache', () => {
    it('应该设置和获取缓存', () => {
      setCache('test', { data: 'value' });
      const result = getCache('test');
      expect(result).toEqual({ data: 'value' });
    });

    it('应该返回过期缓存 null', () => {
      setCache('test', { data: 'value' }, 100);
      vi.advanceTimersByTime(150);
      const result = getCache('test', 100);
      expect(result).toBeNull();
    });

    it('应该删除缓存', () => {
      setCache('test', { data: 'value' });
      deleteCache('test');
      const result = getCache('test');
      expect(result).toBeNull();
    });

    it('应该清空所有缓存', () => {
      setCache('test1', 'value1');
      setCache('test2', 'value2');
      clearCache();
      expect(getCache('test1')).toBeNull();
      expect(getCache('test2')).toBeNull();
    });
  });

  describe('swr (Stale-While-Revalidate)', () => {
    it('应该返回新鲜缓存数据', async () => {
      const fetcher = vi.fn().mockResolvedValue({ data: 'fresh' });
      
      // 第一次调用，获取数据
      const result1 = await swr('test', fetcher, { ttl: 1000 });
      expect(result1.data).toEqual({ data: 'fresh' });
      expect(result1.stale).toBe(false);
      expect(fetcher).toHaveBeenCalledTimes(1);

      // 第二次调用，返回缓存
      const result2 = await swr('test', fetcher, { ttl: 1000 });
      expect(result2.data).toEqual({ data: 'fresh' });
      expect(result2.stale).toBe(false);
      expect(fetcher).toHaveBeenCalledTimes(1); // 没有再次调用
    });

    it('应该返回过期但在宽限期内的缓存并后台刷新', async () => {
      const fetcher = vi.fn()
        .mockResolvedValueOnce({ data: 'stale' })
        .mockResolvedValueOnce({ data: 'fresh' });

      // 第一次调用
      await swr('test', fetcher, { ttl: 100, gracePeriod: 50 });

      // 时间过去，缓存过期但在宽限期内
      vi.advanceTimersByTime(120);

      const result = await swr('test', fetcher, { ttl: 100, gracePeriod: 50 });
      expect(result.stale).toBe(true);
      expect(result.data).toEqual({ data: 'stale' });

      // 等待后台刷新完成
      await vi.advanceTimersByTimeAsync(100);
      expect(fetcher).toHaveBeenCalledTimes(2);
    });

    it('应该在缓存完全过期时等待刷新', async () => {
      const fetcher = vi.fn()
        .mockResolvedValueOnce({ data: 'old' })
        .mockResolvedValueOnce({ data: 'new' });

      await swr('test', fetcher, { ttl: 100, gracePeriod: 5000 });

      // 推进时间到 ttl + gracePeriod 之后（完全过期）
      // ttl=100ms, gracePeriod=5000ms, 所以需要推进 5101ms
      vi.setSystemTime(Date.now() + 100 + 5000 + 1);

      const result = await swr('test', fetcher, { ttl: 100, gracePeriod: 5000 });
      expect(result.stale).toBe(false);
      expect(result.data).toEqual({ data: 'new' });
    });

    it('应该在刷新失败时返回旧数据', async () => {
      const fetcher = vi.fn()
        .mockResolvedValueOnce({ data: 'old' })
        .mockRejectedValueOnce(new Error('Network error'));

      await swr('test', fetcher, { ttl: 100, gracePeriod: 5000 });

      // 推进时间到完全过期
      vi.setSystemTime(Date.now() + 100 + 5000 + 1);

      const result = await swr('test', fetcher, { ttl: 100, gracePeriod: 5000 });
      // 刷新失败后降级返回旧数据，stale=true
      expect(result.stale).toBe(true);
      expect(result.data).toEqual({ data: 'old' });
    });

    it('应该强制刷新', async () => {
      const fetcher = vi.fn().mockResolvedValue({ data: 'updated' });

      // 第一次调用，应该调用 fetcher
      await swr('test', fetcher, { ttl: 1000 });
      expect(fetcher).toHaveBeenCalledTimes(1);

      // 第二次调用，不使用 forceRefresh，应该使用缓存（不调用 fetcher）
      await swr('test', fetcher, { ttl: 1000 });
      expect(fetcher).toHaveBeenCalledTimes(1);

      // 第三次调用，使用 forceRefresh，应该再次调用 fetcher
      // 注意：forceRefresh 是 options 的一部分，不是单独的参数
      await swr('test', fetcher, { ttl: 1000, forceRefresh: true });
      expect(fetcher).toHaveBeenCalledTimes(2);
    });
  });

  describe('cleanupExpiredCache', () => {
    it('应该清理过期缓存', () => {
      setCache('fresh', 'value1', 1000);
      setCache('expired', 'value2', 100);

      vi.advanceTimersByTime(200);

      const count = cleanupExpiredCache();
      expect(count).toBe(1);
      expect(getCache('fresh')).toBe('value1');
      expect(getCache('expired')).toBeNull();
    });
  });

  describe('getCacheStats', () => {
    it('应该返回缓存统计', () => {
      setCache('fresh', 'value1', 1000);
      setCache('expired', 'value2', 100);

      vi.advanceTimersByTime(200);

      const stats = getCacheStats();
      expect(stats.total).toBe(2);
      expect(stats.fresh).toBe(1);
      expect(stats.expired).toBe(1);
    });
  });

  describe('prefetch', () => {
    it('应该预取数据到缓存', async () => {
      const fetcher = vi.fn().mockResolvedValue({ data: 'prefetched' });

      await prefetch('test', fetcher, 1000);

      const cached = getCache('test');
      expect(cached).toEqual({ data: 'prefetched' });
      expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('不应该重复预取已有有效缓存的数据', async () => {
      const fetcher = vi.fn().mockResolvedValue({ data: 'cached' });
      
      setCache('test', { data: 'existing' }, 1000);
      await prefetch('test', fetcher, 1000);

      expect(fetcher).not.toHaveBeenCalled();
    });
  });

  describe('SWRConfig', () => {
    it('应该包含预定义配置', () => {
      expect(SWRConfig.calibrationStatus).toBeDefined();
      expect(SWRConfig.calibrationStatus.ttl).toBe(300000); // 5 分钟
      expect(SWRConfig.deviceParams).toBeDefined();
      expect(SWRConfig.deviceParams.ttl).toBe(5000); // 5 秒
      expect(SWRConfig.wavelengths).toBeDefined();
      expect(SWRConfig.wavelengths.ttl).toBe(300000); // 5 分钟
    });
  });
});
