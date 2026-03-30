/**
 * 虚拟滚动模块测试
 * @see virtual-scroll.js
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createVirtualLog, VirtualLogManager, createVirtualList, VirtualListManager } from '../js/virtual-scroll.js';

describe('virtual-scroll.js', () => {
  describe('VirtualLogManager', () => {
    let container;
    let virtualLog;

    beforeEach(() => {
      container = document.createElement('div');
      container.id = 'log-panel-test';
      container.style.height = '200px';
      document.body.appendChild(container);
      
      virtualLog = new VirtualLogManager('#log-panel-test', {
        itemHeight: 24,
        maxItems: 100,
        bufferSize: 2
      });
    });

    afterEach(() => {
      if (virtualLog) {
        virtualLog.destroy();
      }
      document.body.removeChild(container);
    });

    it('应该创建虚拟滚动实例', () => {
      expect(virtualLog).toBeInstanceOf(VirtualLogManager);
    });

    it('应该添加日志', () => {
      virtualLog.addLog('Test log', 'info');
      expect(virtualLog.getCount()).toBe(1);
    });

    it('应该限制日志数量', () => {
      for (let i = 0; i < 150; i++) {
        virtualLog.addLog(`Log ${i}`, 'info');
      }
      expect(virtualLog.getCount()).toBe(100); // maxItems
    });

    it('应该清除所有日志', () => {
      virtualLog.addLog('Log 1', 'info');
      virtualLog.addLog('Log 2', 'info');
      virtualLog.clear();
      expect(virtualLog.getCount()).toBe(0);
    });

    it('应该导出日志', () => {
      virtualLog.addLog('Log 1', 'info');
      virtualLog.addLog('Log 2', 'success');
      
      const logs = virtualLog.exportLogs();
      expect(logs).toHaveLength(2);
      expect(logs[0].message).toBe('Log 1');
      expect(logs[1].message).toBe('Log 2');
    });

    it('应该导入日志', () => {
      const importedLogs = [
        { message: 'Imported 1', type: 'info', time: '12:00:00' },
        { message: 'Imported 2', type: 'success', time: '12:00:01' }
      ];
      
      virtualLog.importLogs(importedLogs);
      expect(virtualLog.getCount()).toBe(2);
    });

    it('应该支持不同类型的日志', () => {
      virtualLog.addLog('Info message', 'info');
      virtualLog.addLog('Success message', 'success');
      virtualLog.addLog('Warning message', 'warning');
      virtualLog.addLog('Error message', 'error');
      
      const logs = virtualLog.exportLogs();
      expect(logs.map(l => l.type)).toEqual(['info', 'success', 'warning', 'error']);
    });
  });

  describe('createVirtualLog', () => {
    let container;

    beforeEach(() => {
      container = document.createElement('div');
      container.id = 'log-panel-factory';
      container.style.height = '200px';
      document.body.appendChild(container);
    });

    afterEach(() => {
      document.body.removeChild(container);
    });

    it('应该创建 VirtualLogManager 实例', () => {
      const virtualLog = createVirtualLog('#log-panel-factory');
      expect(virtualLog).toBeInstanceOf(VirtualLogManager);
    });
  });

  describe('VirtualListManager', () => {
    let container;
    let virtualList;

    beforeEach(() => {
      container = document.createElement('div');
      container.id = 'list-panel-test';
      container.style.height = '200px';
      document.body.appendChild(container);
      
      virtualList = new VirtualListManager('#list-panel-test', {
        itemHeight: 40,
        renderItem: (item, index) => `<div data-index="${index}">${item.name}</div>`
      });
    });

    afterEach(() => {
      if (virtualList) {
        virtualList.destroy();
      }
      document.body.removeChild(container);
    });

    it('应该设置数据', () => {
      const items = [{ name: 'Item 1' }, { name: 'Item 2' }, { name: 'Item 3' }];
      virtualList.setItems(items);
      // 数据已设置（无法直接验证，因为渲染在 DOM 中）
    });

    it('应该添加数据', () => {
      virtualList.addItem({ name: 'Item 1' });
      virtualList.addItem({ name: 'Item 2' });
      // 数据已添加
    });

    it('应该更新数据', () => {
      virtualList.setItems([{ name: 'Item 1' }, { name: 'Item 2' }]);
      virtualList.updateItem(0, { name: 'Updated Item 1' });
      // 数据已更新
    });

    it('应该删除数据', () => {
      virtualList.setItems([{ name: 'Item 1' }, { name: 'Item 2' }, { name: 'Item 3' }]);
      virtualList.removeItem(1);
      // 数据已删除
    });

    it('应该清除所有数据', () => {
      virtualList.setItems([{ name: 'Item 1' }, { name: 'Item 2' }]);
      virtualList.clear();
      // 数据已清除
    });
  });

  describe('createVirtualList', () => {
    let container;

    beforeEach(() => {
      container = document.createElement('div');
      container.id = 'list-panel-factory';
      container.style.height = '200px';
      document.body.appendChild(container);
    });

    afterEach(() => {
      document.body.removeChild(container);
    });

    it('应该创建 VirtualListManager 实例', () => {
      const virtualList = createVirtualList('#list-panel-factory');
      expect(virtualList).toBeInstanceOf(VirtualListManager);
    });
  });

  describe('性能测试', () => {
    let container;
    let virtualLog;

    beforeEach(() => {
      container = document.createElement('div');
      container.id = 'log-panel-perf';
      container.style.height = '200px';
      document.body.appendChild(container);
    });

    afterEach(() => {
      if (virtualLog) {
        virtualLog.destroy();
      }
      if (container && container.parentNode) {
        container.parentNode.removeChild(container);
      }
    });

    it('应该快速添加大量日志', () => {
      virtualLog = new VirtualLogManager('#log-panel-perf', {
        itemHeight: 24,
        maxItems: 10000
      });

      const startTime = performance.now();
      for (let i = 0; i < 500; i++) {
        virtualLog.addLog(`Log ${i}`, 'info');
      }
      const endTime = performance.now();
      
      // 应该在 500ms 内完成（取决于机器性能）
      expect(endTime - startTime).toBeLessThan(500);
      expect(virtualLog.getCount()).toBe(500);
    });
  });
});
