/**
 * 演示数据加载器
 * @module demo-loader
 * 
 * 负责加载和显示演示数据
 */

import { generateMockSpectrum, getPresetSpectrum, generateDemoDataset } from './mock-data.js';
import { updateSpectrum } from './chart.js';
import { addLog, showToast } from './utils.js';
import { events, EventTypes } from './event-bus.js';

let currentDemoMaterial = 'mixed';
let demoDataCache = null;

/**
 * 初始化演示数据加载器
 */
export function initDemoLoader() {
    console.log('[DemoLoader] 初始化演示数据加载器');
    
    // 生成演示数据集缓存
    demoDataCache = generateDemoDataset();
    
    // 设置演示数据按钮事件
    setupDemoButton();
    
    addLog('[DemoLoader] 演示数据加载器已初始化');
}

/**
 * 设置演示数据按钮事件
 */
function setupDemoButton() {
    const btnLoadDemo = document.getElementById('btn-load-demo');
    if (!btnLoadDemo) {
        console.warn('[DemoLoader] 演示数据按钮不存在');
        return;
    }
    
    btnLoadDemo.addEventListener('click', () => {
        loadRandomDemoData();
    });
    
    // 右键点击选择物质
    btnLoadDemo.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showMaterialSelector();
    });
    
    addLog('[DemoLoader] 演示数据按钮已设置（左键随机加载，右键选择物质）');
}

/**
 * 加载随机演示数据
 */
export function loadRandomDemoData() {
    const materials = ['quartz', 'diamond', 'graphite', 'calcite', 'corundum', 'silicon', 'mixed'];
    const randomMaterial = materials[Math.floor(Math.random() * materials.length)];
    loadDemoMaterial(randomMaterial);
}

/**
 * 加载指定物质的演示数据
 * @param {string} material - 物质名称
 */
export function loadDemoMaterial(material) {
    console.log('[DemoLoader] 加载演示数据:', material);

    try {
        const preset = getPresetSpectrum(material);
        const { wavenumbers, intensities } = preset;

        console.log(`[DemoLoader] 数据已生成：${wavenumbers.length} 点`);

        // 更新图表（正确的参数顺序：intensities, wavenumbers）
        updateSpectrum(intensities, wavenumbers);

        // 更新状态
        currentDemoMaterial = material;

        // 发送事件
        events.emit(EventTypes.SPECTRUM_UPDATED, {
            wavenumbers,
            intensities,
            isMock: true,
            material
        });

        // 显示提示
        showToast(`已加载 ${preset.name} 演示数据`, 'success');
        addLog(`[DemoLoader] 已加载演示数据：${preset.name}`, 'success');

        // 自动启用采集按钮
        enableAcquisitionButton();

    } catch (error) {
        console.error('[DemoLoader] 加载演示数据失败:', error);
        addLog(`[DemoLoader] 加载失败：${error.message}`, 'error');
        showToast(`加载失败：${error.message}`, 'error');
    }
}

/**
 * 显示物质选择器
 */
function showMaterialSelector() {
    const materials = [
        { value: 'quartz', label: '石英 (Quartz)' },
        { value: 'diamond', label: '金刚石 (Diamond)' },
        { value: 'graphite', label: '石墨 (Graphite)' },
        { value: 'calcite', label: '方解石 (Calcite)' },
        { value: 'corundum', label: '刚玉 (Corundum)' },
        { value: 'silicon', label: '硅 (Silicon)' },
        { value: 'mixed', label: '混合矿物' }
    ];
    
    // 创建选择器 UI
    const selector = document.createElement('div');
    selector.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #1a1a2e;
        border: 2px solid #00d9ff;
        border-radius: 12px;
        padding: 20px;
        z-index: 10000;
        min-width: 300px;
        box-shadow: 0 8px 32px rgba(0, 217, 255, 0.2);
    `;
    
    let html = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
            <h3 style="color:#00d9ff;margin:0;">📊 选择演示物质</h3>
            <button onclick="this.closest('div').remove()" style="background:transparent;border:none;color:#aaa;font-size:20px;cursor:pointer;">×</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
    `;
    
    materials.forEach(m => {
        html += `
            <button onclick="window.__loadDemo__('${m.value}')" 
                    style="padding:10px 15px;background:#2a2a3e;color:#fff;border:1px solid #333;border-radius:6px;cursor:pointer;text-align:left;">
                ${m.label}
            </button>
        `;
    });
    
    html += `
        </div>
        <div style="margin-top:15px;text-align:center;color:#888;font-size:12px;">
            点击物质名称加载演示数据
        </div>
    `;
    
    selector.innerHTML = html;
    document.body.appendChild(selector);
    
    // 点击外部关闭
    selector.addEventListener('click', (e) => {
        if (e.target === selector) {
            selector.remove();
        }
    });
    
    // 暴露加载函数到全局
    window.__loadDemo__ = (material) => {
        loadDemoMaterial(material);
        selector.remove();
    };
}

/**
 * 启用采集按钮
 */
function enableAcquisitionButton() {
    const btnStart = document.getElementById('btn-start');
    const btnExport = document.getElementById('btn-export');
    const btnExportBatch = document.getElementById('btn-export-batch');
    
    if (btnStart) {
        btnStart.disabled = false;
        btnStart.textContent = '开始采集';
    }
    
    if (btnExport) {
        btnExport.disabled = false;
    }
    
    if (btnExportBatch) {
        btnExportBatch.disabled = false;
    }
    
    addLog('[DemoLoader] 采集和导出功能已启用');
}

/**
 * 获取当前演示数据
 * @returns {Object} 演示数据
 */
export function getCurrentDemoData() {
    return demoDataCache?.find(d => d.material === currentDemoMaterial);
}

/**
 * 获取所有演示数据
 * @returns {Array} 演示数据集
 */
export function getAllDemoData() {
    return demoDataCache || [];
}

export default {
    initDemoLoader,
    loadRandomDemoData,
    loadDemoMaterial,
    getCurrentDemoData,
    getAllDemoData
};
