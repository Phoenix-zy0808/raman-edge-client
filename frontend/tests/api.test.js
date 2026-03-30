/**
 * API 封装模块测试
 * @module test/api.test
 *
 * 测试范围:
 * - BackendApi 基本功能
 * - 校准功能测试
 * - 缓存功能测试
 * - 错误处理测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BackendApi, api } from '@/api.js';
import { SWRConfig } from '@/cache.js';

describe('BackendApi', () => {
    let testApi;

    beforeEach(() => {
        testApi = new BackendApi();
    });

    describe('基本功能', () => {
        it('应该能够创建实例', () => {
            expect(testApi).toBeInstanceOf(BackendApi);
        });

        it('应该能够初始化', () => {
            testApi.init();
            expect(testApi.isInitialized()).toBe(true);
        });

        it('单例 api 应该存在', () => {
            expect(api).toBeDefined();
            expect(api).toBeInstanceOf(BackendApi);
        });
    });

    describe('校准功能', () => {
        it('应该导出 calibrateWavelength 方法', () => {
            expect(testApi.calibrateWavelength).toBeDefined();
            expect(typeof testApi.calibrateWavelength).toBe('function');
        });

        it('应该导出 calibrateIntensity 方法', () => {
            expect(testApi.calibrateIntensity).toBeDefined();
            expect(typeof testApi.calibrateIntensity).toBe('function');
        });

        it('应该导出 getCalibrationStatus 方法', () => {
            expect(testApi.getCalibrationStatus).toBeDefined();
            expect(typeof testApi.getCalibrationStatus).toBe('function');
        });
    });

    describe('缓存配置', () => {
        it('应该有校准状态缓存配置', () => {
            expect(SWRConfig.calibrationStatus).toBeDefined();
            expect(SWRConfig.calibrationStatus.ttl).toBeGreaterThan(0);
        });

        it('应该有波长数据缓存配置', () => {
            expect(SWRConfig.wavelengths).toBeDefined();
            expect(SWRConfig.wavelengths.ttl).toBeGreaterThan(0);
        });
    });

    describe('设备控制方法', () => {
        it('应该导出 connect 方法', () => {
            expect(testApi.connect).toBeDefined();
            expect(typeof testApi.connect).toBe('function');
        });

        it('应该导出 disconnect 方法', () => {
            expect(testApi.disconnect).toBeDefined();
            expect(typeof testApi.disconnect).toBe('function');
        });

        it('应该导出 startAcquisition 方法', () => {
            expect(testApi.startAcquisition).toBeDefined();
            expect(typeof testApi.startAcquisition).toBe('function');
        });

        it('应该导出 stopAcquisition 方法', () => {
            expect(testApi.stopAcquisition).toBeDefined();
            expect(typeof testApi.stopAcquisition).toBe('function');
        });
    });

    describe('参数设置方法', () => {
        it('应该导出 setIntegrationTime 方法', () => {
            expect(testApi.setIntegrationTime).toBeDefined();
            expect(typeof testApi.setIntegrationTime).toBe('function');
        });

        it('应该导出 setAccumulationCount 方法', () => {
            expect(testApi.setAccumulationCount).toBeDefined();
            expect(typeof testApi.setAccumulationCount).toBe('function');
        });

        it('应该导出 setSmoothingWindow 方法', () => {
            expect(testApi.setSmoothingWindow).toBeDefined();
            expect(typeof testApi.setSmoothingWindow).toBe('function');
        });

        it('应该导出 setNoiseLevel 方法', () => {
            expect(testApi.setNoiseLevel).toBeDefined();
            expect(typeof testApi.setNoiseLevel).toBe('function');
        });
    });

    describe('状态获取方法', () => {
        it('应该导出 getStatus 方法', () => {
            expect(testApi.getStatus).toBeDefined();
            expect(typeof testApi.getStatus).toBe('function');
        });

        it('应该导出 getIntegrationTime 方法', () => {
            expect(testApi.getIntegrationTime).toBeDefined();
            expect(typeof testApi.getIntegrationTime).toBe('function');
        });

        it('应该导出 getAccumulationCount 方法', () => {
            expect(testApi.getAccumulationCount).toBeDefined();
            expect(typeof testApi.getAccumulationCount).toBe('function');
        });
    });

    describe('自动曝光方法', () => {
        it('应该导出 autoExposure 方法', () => {
            expect(testApi.autoExposure).toBeDefined();
            expect(typeof testApi.autoExposure).toBe('function');
        });

        it('应该导出 setAutoExposureEnabled 方法', () => {
            expect(testApi.setAutoExposureEnabled).toBeDefined();
            expect(typeof testApi.setAutoExposureEnabled).toBe('function');
        });
    });
});
