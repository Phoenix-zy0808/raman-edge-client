/**
 * 模拟数据生成器
 * @module mock-data
 * 
 * 生成模拟拉曼光谱数据，用于演示和测试
 */

/**
 * 生成模拟拉曼光谱数据
 * @param {number} numPoints - 数据点数
 * @param {number[]} wavenumberRange - 波数范围 [min, max]
 * @param {Object[]} peaks - 特征峰配置 [{position, intensity, fwhm}, ...]
 * @returns {Object} { wavenumbers, intensities }
 */
export function generateMockSpectrum(
    numPoints = 1024,
    wavenumberRange = [200, 3200],
    peaks = null
) {
    // 生成波数数组
    const wavenumbers = [];
    const step = (wavenumberRange[1] - wavenumberRange[0]) / (numPoints - 1);
    for (let i = 0; i < numPoints; i++) {
        wavenumbers.push(wavenumberRange[0] + i * step);
    }

    // 生成基线（荧光背景）
    const baseline = generateFluorescenceBackground(wavenumbers);

    // 生成拉曼特征峰
    const ramanPeaks = generateRamanPeaks(wavenumbers, peaks);

    // 添加噪声
    const noise = generateNoise(numPoints, 0.02);

    // 合成光谱
    const intensities = wavenumbers.map((_, i) => {
        return Math.max(0, baseline[i] + ramanPeaks[i] + noise[i]);
    });

    return { wavenumbers, intensities };
}

/**
 * 生成荧光背景基线
 */
function generateFluorescenceBackground(wavenumbers) {
    const x = wavenumbers;
    const xNorm = x.map(v => (v - x[0]) / (x[x.length - 1] - x[0]));
    
    return xNorm.map(t => {
        // 指数衰减背景
        const expComponent = 0.3 * Math.exp(-3 * t);
        // 多项式背景
        const polyComponent = 0.05 * Math.pow(1 - t, 2);
        // 常数基底
        const base = 0.1;
        return expComponent + polyComponent + base;
    });
}

/**
 * 生成拉曼特征峰
 */
function generateRamanPeaks(wavenumbers, peaks = null) {
    // 默认特征峰（矿物/宝石）
    const defaultPeaks = [
        { position: 464, intensity: 0.8, fwhm: 30 },   // 石英
        { position: 1082, intensity: 0.6, fwhm: 25 },  // 石英
        { position: 1332, intensity: 0.9, fwhm: 20 },  // 金刚石
        { position: 1580, intensity: 0.7, fwhm: 35 },  // 石墨 G 峰
        { position: 2700, intensity: 0.4, fwhm: 40 },  // 石墨 2D 峰
    ];

    const selectedPeaks = peaks || defaultPeaks;

    return wavenumbers.map((wn, i) => {
        let intensity = 0;
        selectedPeaks.forEach(peak => {
            // 高斯峰
            const sigma = peak.fwhm / (2 * Math.sqrt(2 * Math.log(2)));
            const gaussian = peak.intensity * Math.exp(-Math.pow(wn - peak.position, 2) / (2 * sigma * sigma));
            intensity += gaussian;
        });
        return intensity;
    });
}

/**
 * 生成高斯噪声
 */
function generateNoise(numPoints, stdDev) {
    const noise = [];
    for (let i = 0; i < numPoints; i++) {
        // Box-Muller 变换生成正态分布随机数
        const u1 = Math.random();
        const u2 = Math.random();
        const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        noise.push(z0 * stdDev);
    }
    return noise;
}

/**
 * 获取预设物质的光谱数据
 */
export function getPresetSpectrum(materialName) {
    const presets = {
        'quartz': {
            name: '石英 (Quartz)',
            peaks: [
                { position: 464, intensity: 0.8, fwhm: 30 },
                { position: 1082, intensity: 0.6, fwhm: 25 },
                { position: 355, intensity: 0.3, fwhm: 20 },
                { position: 800, intensity: 0.2, fwhm: 25 },
            ]
        },
        'diamond': {
            name: '金刚石 (Diamond)',
            peaks: [
                { position: 1332, intensity: 1.0, fwhm: 15 },
                { position: 1140, intensity: 0.1, fwhm: 30 },
                { position: 1500, intensity: 0.1, fwhm: 30 },
            ]
        },
        'graphite': {
            name: '石墨 (Graphite)',
            peaks: [
                { position: 1580, intensity: 0.9, fwhm: 35 },  // G 峰
                { position: 2700, intensity: 0.6, fwhm: 40 },  // 2D 峰
                { position: 1350, intensity: 0.3, fwhm: 30 },  // D 峰
            ]
        },
        'calcite': {
            name: '方解石 (Calcite)',
            peaks: [
                { position: 1086, intensity: 1.0, fwhm: 25 },
                { position: 712, intensity: 0.4, fwhm: 20 },
                { position: 281, intensity: 0.3, fwhm: 15 },
            ]
        },
        'corundum': {
            name: '刚玉 (Corundum)',
            peaks: [
                { position: 418, intensity: 0.7, fwhm: 25 },
                { position: 578, intensity: 0.6, fwhm: 25 },
                { position: 751, intensity: 0.5, fwhm: 20 },
            ]
        },
        'silicon': {
            name: '硅 (Silicon)',
            peaks: [
                { position: 520, intensity: 1.0, fwhm: 15 },
                { position: 950, intensity: 0.2, fwhm: 20 },
                { position: 300, intensity: 0.1, fwhm: 20 },
            ]
        },
        'mixed': {
            name: '混合矿物',
            peaks: [
                { position: 464, intensity: 0.6, fwhm: 30 },   // 石英
                { position: 1082, intensity: 0.4, fwhm: 25 },  // 石英
                { position: 1332, intensity: 0.8, fwhm: 20 },  // 金刚石
                { position: 1580, intensity: 0.5, fwhm: 35 },  // 石墨
                { position: 1086, intensity: 0.5, fwhm: 25 },  // 方解石
            ]
        }
    };

    const preset = presets[materialName] || presets['mixed'];
    return generateMockSpectrum(1024, [200, 3200], preset.peaks);
}

/**
 * 添加随机变异（用于演示数据增强）
 */
export function addVariation(spectrum, options = {}) {
    const { wavenumbers, intensities } = spectrum;
    const {
        noiseLevel = 0.02,
        shiftRange = 5,
        intensityRange = [0.9, 1.1]
    } = options;

    // 添加噪声
    const noise = generateNoise(intensities.length, noiseLevel);
    
    // 强度缩放
    const scale = intensityRange[0] + Math.random() * (intensityRange[1] - intensityRange[0]);
    
    // 波数平移
    const shift = (Math.random() - 0.5) * 2 * shiftRange;

    const variedIntensities = intensities.map((v, i) => {
        return Math.max(0, (v + noise[i]) * scale);
    });

    const variedWavenumbers = wavenumbers.map(v => v + shift);

    return { wavenumbers: variedWavenumbers, intensities: variedIntensities };
}

/**
 * 批量生成演示数据集
 */
export function generateDemoDataset() {
    const materials = ['quartz', 'diamond', 'graphite', 'calcite', 'corundum', 'silicon', 'mixed'];
    const dataset = [];

    materials.forEach(material => {
        // 每个物质生成 5 个变体
        for (let i = 0; i < 5; i++) {
            const base = getPresetSpectrum(material);
            const varied = addVariation(base, {
                noiseLevel: 0.01 + Math.random() * 0.02,
                intensityRange: [0.95, 1.05]
            });
            dataset.push({
                material,
                name: getPresetSpectrum(material).name,
                ...varied,
                isMock: true
            });
        }
    });

    return dataset;
}

export default {
    generateMockSpectrum,
    getPresetSpectrum,
    addVariation,
    generateDemoDataset
};
