# P0 功能实现方案（定位 1：简易型拉曼光谱边缘客户端）

## 📋 功能清单

| 功能模块 | 功能 | 后端文件 | 前端文件 | 预计时间 |
|----------|------|----------|----------|----------|
| **采集参数控制** | 积分时间调节 | backend/bridge.py | frontend/app.js | 2 小时 |
| | 累加平均次数 | backend/bridge.py | frontend/app.js | 2 小时 |
| **数据处理** | 平滑滤波 | backend/inference.py | frontend/algorithms.js | 2 小时 |
| | 基线校正 | backend/inference.py | frontend/algorithms.js | 4 小时 |
| **峰值分析** | 峰面积计算 | backend/inference.py | frontend/app.js | 2 小时 |
| **物质识别** | 谱库匹配 | backend/inference.py | frontend/app.js | 8 小时 |
| | 相似度计算 | backend/inference.py | - | 2 小时 |
| **数据管理** | 导入历史数据 | backend/bridge.py | frontend/app.js | 2 小时 |
| **谱库文件** | 标准谱库（10 种） | backend/library/ | - | 4 小时 |
| **合计** | | | | **28 小时** |

---

## 一、采集参数控制

### 1.1 积分时间调节

**后端实现**（`backend/bridge.py`）：

```python
class BridgeObject(QObject):
    # ... 现有代码 ...
    
    def __init__(self, state_manager, driver):
        # ... 现有初始化 ...
        self._integration_time = 100  # 默认 100ms
        self._accumulation_count = 1  # 默认 1 次
    
    @Slot(int)
    def setIntegrationTime(self, ms: int):
        """
        设置积分时间（毫秒）
        
        Args:
            ms: 积分时间，范围 10-10000ms
        """
        if ms < 10:
            ms = 10
        elif ms > 10000:
            ms = 10000
        self._integration_time = ms
        log.info(f"[Bridge] 积分时间设置为：{ms}ms")
        
        # 通知 WorkerThread 更新
        if hasattr(self, '_worker_thread'):
            self._worker_thread.integration_time = ms
    
    @Slot(int)
    def setAccumulationCount(self, n: int):
        """
        设置累加平均次数
        
        Args:
            n: 累加次数，范围 1-100
        """
        if n < 1:
            n = 1
        elif n > 100:
            n = 100
        self._accumulation_count = n
        log.info(f"[Bridge] 累加次数设置为：{n}")
        
        # 通知 WorkerThread 更新
        if hasattr(self, '_worker_thread'):
            self._worker_thread.accumulation_count = n
    
    @Slot(result=int)
    def getIntegrationTime(self) -> int:
        """获取当前积分时间"""
        return self._integration_time
    
    @Slot(result=int)
    def getAccumulationCount(self) -> int:
        """获取当前累加次数"""
        return self._accumulation_count
```

**WorkerThread 修改**（`backend/worker_thread.py`）：

```python
class WorkerThread(QThread):
    def __init__(self, driver, sample_rate=10.0):
        # ... 现有初始化 ...
        self._integration_time = 100  # ms
        self._accumulation_count = 1
    
    @property
    def integration_time(self):
        return self._integration_time
    
    @integration_time.setter
    def integration_time(self, ms: int):
        self._integration_time = ms
    
    @property
    def accumulation_count(self):
        return self._accumulation_count
    
    @accumulation_count.setter
    def accumulation_count(self, n: int):
        self._accumulation_count = n
    
    def run(self):
        # ... 现有代码 ...
        while True:
            # ... 等待采集信号 ...
            
            # 累加平均
            spectra = []
            for _ in range(self._accumulation_count):
                spectrum = self.driver.read_spectrum(integration_time=self._integration_time)
                spectra.append(spectrum)
                if self._accumulation_count > 1:
                    time.sleep(self._integration_time / 1000.0)
            
            # 取平均
            if len(spectra) > 1:
                spectrum = np.mean(spectra, axis=0)
            else:
                spectrum = spectra[0]
            
            # 发送光谱数据
            self.spectrumReady.emit(spectrum.tolist() if isinstance(spectrum, np.ndarray) else spectrum)
```

**前端实现**（`frontend/index.html`）：

```html
<!-- 在控制面板中添加 -->
<div class="control-group">
    <label>积分时间 (ms): <span id="integration-time-value">100</span></label>
    <input type="number" id="integration-time" min="10" max="10000" 
           value="100" step="10" onchange="updateIntegrationTime(this.value)">
</div>

<div class="control-group">
    <label>累加次数：<span id="accumulation-count-value">1</span></label>
    <input type="number" id="accumulation-count" min="1" max="100" 
           value="1" onchange="updateAccumulationCount(this.value)">
</div>
```

**前端 JS**（`frontend/app.js`）：

```javascript
function updateIntegrationTime(value) {
    document.getElementById('integration-time-value').textContent = value;
    if (pythonBackend) {
        pythonBackend.setIntegrationTime(parseInt(value));
        addLog(`积分时间设置为：${value}ms`, 'info');
    }
}

function updateAccumulationCount(value) {
    document.getElementById('accumulation-count-value').textContent = value;
    if (pythonBackend) {
        pythonBackend.setAccumulationCount(parseInt(value));
        addLog(`累加次数设置为：${value}`, 'info');
    }
}
```

---

### 1.2 累加平均次数

见上方代码（与积分时间一起实现）。

---

## 二、数据处理

### 2.1 平滑滤波

**后端实现**（`backend/inference.py`）：

```python
from scipy.signal import savgol_filter

class LocalInference:
    # ... 现有代码 ...
    
    def smooth(self, spectrum: np.ndarray, window_size: int = 5, polyorder: int = 2) -> np.ndarray:
        """
        Savitzky-Golay 平滑滤波
        
        Args:
            spectrum: 输入光谱
            window_size: 窗口大小（必须为奇数，3-15）
            polyorder: 多项式阶数（默认 2）
        
        Returns:
            平滑后的光谱
        """
        if window_size % 2 == 0:
            window_size += 1  # 确保为奇数
        if window_size < 3:
            window_size = 3
        if window_size > 15:
            window_size = 15
        
        # 确保窗口大小不超过数据长度
        if window_size > len(spectrum):
            window_size = len(spectrum) if len(spectrum) % 2 == 1 else len(spectrum) - 1
        
        smoothed = savgol_filter(spectrum, window_size, polyorder, mode='mirror')
        log.info(f"[Inference] 平滑滤波完成：window={window_size}, polyorder={polyorder}")
        return smoothed
```

**前端实现**（`frontend/algorithms.js`）：

```javascript
/**
 * Savitzky-Golay 平滑滤波（JavaScript 实现）
 * @param {number[]} spectrum - 输入光谱
 * @param {number} windowSize - 窗口大小（奇数，3-15）
 * @param {number} polyOrder - 多项式阶数（默认 2）
 * @returns {number[]} 平滑后的光谱
 */
function savgolFilter(spectrum, windowSize = 5, polyOrder = 2) {
    const n = spectrum.length;
    if (windowSize % 2 === 0) windowSize++;
    if (windowSize < 3) windowSize = 3;
    if (windowSize > n) windowSize = n % 2 === 1 ? n : n - 1;
    
    const halfWindow = Math.floor(windowSize / 2);
    const smoothed = new Array(n);
    
    // 计算卷积系数（简化版，实际应该用最小二乘法计算）
    // 这里使用移动平均作为近似
    for (let i = 0; i < n; i++) {
        let sum = 0;
        let count = 0;
        for (let j = -halfWindow; j <= halfWindow; j++) {
            const idx = i + j;
            if (idx >= 0 && idx < n) {
                sum += spectrum[idx];
                count++;
            }
        }
        smoothed[i] = sum / count;
    }
    
    return smoothed;
}
```

---

### 2.2 基线校正

**后端实现**（`backend/inference.py`）：

```python
import numpy as np

class LocalInference:
    # ... 现有代码 ...
    
    def baseline_correction(self, spectrum: np.ndarray, method: str = 'poly', 
                           order: int = 3, max_iter: int = 100) -> tuple:
        """
        基线校正
        
        Args:
            spectrum: 输入光谱
            method: 'poly' (多项式拟合) 或 'airpls' (自适应迭代)
            order: 多项式阶数（仅 poly 方法）
            max_iter: 最大迭代次数（仅 airpls 方法）
        
        Returns:
            (corrected_spectrum, baseline) 校正后光谱和基线
        """
        x = np.arange(len(spectrum))
        
        if method == 'poly':
            # 多项式拟合
            coeffs = np.polyfit(x, spectrum, order)
            baseline = np.polyval(coeffs, x)
            corrected = spectrum - baseline
            
        elif method == 'airpls':
            # airPLS 算法（自适应迭代重加权惩罚最小二乘）
            baseline = self._airpls(spectrum, max_iter)
            corrected = spectrum - baseline
            
        else:
            log.warning(f"[Inference] 未知基线校正方法：{method}，使用多项式拟合")
            coeffs = np.polyfit(x, spectrum, order)
            baseline = np.polyval(coeffs, x)
            corrected = spectrum - baseline
        
        # 确保校正值非负
        corrected = np.maximum(corrected, 0)
        
        log.info(f"[Inference] 基线校正完成：method={method}")
        return corrected, baseline
    
    def _airpls(self, spectrum: np.ndarray, max_iter: int = 100, lam: float = 1e5) -> np.ndarray:
        """
        airPLS 基线校正算法
        
        Args:
            spectrum: 输入光谱
            max_iter: 最大迭代次数
            lam: 平滑参数
        
        Returns:
            baseline: 基线
        """
        n = len(spectrum)
        baseline = np.zeros(n)
        
        # 简化版 airpls（完整版需要稀疏矩阵优化）
        for iteration in range(max_iter):
            diff = spectrum - baseline
            
            # 计算权重
            weights = np.ones(n)
            weights[diff < 0] = np.exp(diff[diff < 0] / np.std(spectrum))
            
            # 加权平滑
            # 这里使用简化的高斯平滑
            from scipy.ndimage import gaussian_filter1d
            baseline = gaussian_filter1d(spectrum * weights, sigma=50)
            baseline = baseline / (gaussian_filter1d(weights, sigma=50) + 1e-10)
            
            # 收敛判断
            if np.max(np.abs(diff)) < 1e-6:
                break
        
        log.info(f"[Inference] airPLS 迭代次数：{iteration + 1}")
        return baseline
```

**前端实现**（`frontend/algorithms.js`）：

```javascript
/**
 * 多项式拟合基线校正
 * @param {number[]} spectrum - 输入光谱
 * @param {number} order - 多项式阶数（默认 3）
 * @returns {{corrected: number[], baseline: number[]}} 校正后光谱和基线
 */
function polynomialBaseline(spectrum, order = 3) {
    const n = spectrum.length;
    const x = Array.from({length: n}, (_, i) => i);
    
    // 多项式拟合（简化版，使用最小二乘）
    const coeffs = polyfit(x, spectrum, order);
    const baseline = polynomial(coeffs, x);
    const corrected = spectrum.map((v, i) => Math.max(0, v - baseline[i]));
    
    return { corrected, baseline };
}

/**
 * 多项式拟合（最小二乘法）
 */
function polyfit(x, y, order) {
    // 简化实现，实际应该用矩阵运算
    // 这里使用线性回归作为示例
    const n = x.length;
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return [intercept, slope];  // 只返回线性系数
}

/**
 * 计算多项式值
 */
function polynomial(coeffs, x) {
    return x.map(xi => {
        let y = 0;
        for (let i = coeffs.length - 1; i >= 0; i--) {
            y = y * xi + coeffs[i];
        }
        return y;
    });
}

/**
 * airPLS 基线校正（简化版）
 * @param {number[]} spectrum - 输入光谱
 * @param {number} maxIter - 最大迭代次数
 * @returns {number[]} 基线
 */
function airplsBaseline(spectrum, maxIter = 100) {
    const n = spectrum.length;
    let baseline = new Array(n).fill(0);
    
    // 简化版：使用移动平均模拟基线
    const windowSize = Math.floor(n / 10);
    for (let iter = 0; iter < maxIter; iter++) {
        // 计算差值
        const diff = spectrum.map((v, i) => v - baseline[i]);
        
        // 计算权重（负值权重小）
        const weights = diff.map(d => d < 0 ? Math.exp(d / 100) : 1);
        
        // 加权移动平均
        baseline = movingAverage(spectrum.map((v, i) => v * weights[i]), windowSize);
        const weightSum = movingAverage(weights, windowSize);
        baseline = baseline.map((v, i) => v / (weightSum[i] + 1e-10));
        
        // 收敛判断
        const maxDiff = Math.max(...diff.map(Math.abs));
        if (maxDiff < 1e-6) break;
    }
    
    return baseline;
}

/**
 * 移动平均
 */
function movingAverage(data, windowSize) {
    const n = data.length;
    const result = new Array(n);
    const halfWindow = Math.floor(windowSize / 2);
    
    for (let i = 0; i < n; i++) {
        let sum = 0;
        let count = 0;
        for (let j = -halfWindow; j <= halfWindow; j++) {
            const idx = i + j;
            if (idx >= 0 && idx < n) {
                sum += data[idx];
                count++;
            }
        }
        result[i] = sum / count;
    }
    
    return result;
}
```

---

## 三、峰值分析

### 3.1 峰面积计算

**后端实现**（`backend/inference.py`）：

```python
from scipy.signal import find_peaks

class LocalInference:
    # ... 现有代码 ...
    
    def calculate_peak_area(self, spectrum: np.ndarray, wavelength: np.ndarray, 
                           peak_pos: float, window: float = 50) -> dict:
        """
        计算峰面积
        
        Args:
            spectrum: 光谱强度
            wavelength: 波长/拉曼位移
            peak_pos: 峰位置（cm⁻¹）
            window: 积分窗口（cm⁻¹）
        
        Returns:
            dict: {
                'position': 峰位,
                'height': 峰高,
                'area': 峰面积,
                'fwhm': 半高宽
            }
        """
        # 找到峰位置附近的索引范围
        mask = (wavelength >= peak_pos - window) & (wavelength <= peak_pos + window)
        peak_wavelength = wavelength[mask]
        peak_spectrum = spectrum[mask]
        
        if len(peak_spectrum) < 3:
            log.warning(f"[Inference] 峰区域数据不足：{peak_pos}")
            return None
        
        # 找到峰高
        peak_idx = np.argmax(peak_spectrum)
        peak_height = peak_spectrum[peak_idx]
        actual_position = peak_wavelength[peak_idx]
        
        # 基线校正（局部）
        baseline = np.linspace(peak_spectrum[0], peak_spectrum[-1], len(peak_spectrum))
        corrected_spectrum = peak_spectrum - baseline
        
        # 计算峰面积（梯形积分）
        area = np.trapz(corrected_spectrum, peak_wavelength)
        
        # 计算半高宽
        half_height = peak_height / 2
        left_idx = np.where(corrected_spectrum[:peak_idx] <= half_height)[0]
        right_idx = np.where(corrected_spectrum[peak_idx:] <= half_height)[0]
        
        if len(left_idx) > 0 and len(right_idx) > 0:
            left_pos = peak_wavelength[left_idx[-1]]
            right_pos = peak_wavelength[peak_idx + right_idx[0]]
            fwhm = right_pos - left_pos
        else:
            fwhm = 0
        
        result = {
            'position': float(actual_position),
            'height': float(peak_height),
            'area': float(area),
            'fwhm': float(fwhm)
        }
        
        log.info(f"[Inference] 峰面积计算完成：pos={actual_position:.1f}, area={area:.2f}")
        return result
```

**前端实现**（`frontend/app.js`）：

```javascript
// 添加峰值点击事件
function initChart() {
    // ... 现有初始化代码 ...
    
    // 点击显示峰值信息
    chart.on('click', function(params) {
        if (params.componentType === 'series') {
            const wavelength = params.value[0];
            const intensity = params.value[1];
            
            // 计算峰面积（简化版）
            const peakInfo = calculateLocalPeakArea(wavelength, intensity);
            
            // 显示峰值信息
            showPeakInfo(peakInfo);
        }
    });
}

function calculateLocalPeakArea(peakPos, peakHeight) {
    const window = 50;  // cm⁻¹
    
    // 找到窗口范围内的数据
    const startIndex = wavelengthData.findIndex(w => w >= peakPos - window);
    const endIndex = wavelengthData.findIndex(w => w >= peakPos + window);
    
    if (startIndex === -1 || endIndex === -1) {
        return null;
    }
    
    const localWavelength = wavelengthData.slice(startIndex, endIndex);
    const localSpectrum = spectrumData.slice(startIndex, endIndex);
    
    // 基线校正
    const baselineStart = localSpectrum[0];
    const baselineEnd = localSpectrum[localSpectrum.length - 1];
    const baseline = Array.from({length: localSpectrum.length}, 
        (_, i) => baselineStart + (baselineEnd - baselineStart) * i / (localSpectrum.length - 1));
    
    const corrected = localSpectrum.map((v, i) => Math.max(0, v - baseline[i]));
    
    // 梯形积分
    let area = 0;
    for (let i = 1; i < corrected.length; i++) {
        area += (corrected[i] + corrected[i-1]) * (localWavelength[i] - localWavelength[i-1]) / 2;
    }
    
    // 半高宽
    const halfHeight = peakHeight / 2;
    let leftPos = peakPos;
    let rightPos = peakPos;
    
    for (let i = wavelengthData.findIndex(w => w >= peakPos); i >= startIndex; i--) {
        if (spectrumData[i] <= halfHeight) {
            leftPos = wavelengthData[i];
            break;
        }
    }
    
    for (let i = wavelengthData.findIndex(w => w >= peakPos); i <= endIndex; i++) {
        if (spectrumData[i] <= halfHeight) {
            rightPos = wavelengthData[i];
            break;
        }
    }
    
    const fwhm = rightPos - leftPos;
    
    return {
        position: peakPos.toFixed(1),
        height: peakHeight.toFixed(4),
        area: area.toFixed(2),
        fwhm: fwhm.toFixed(1)
    };
}

function showPeakInfo(peakInfo) {
    if (!peakInfo) return;
    
    const message = `峰信息：
        峰位：${peakInfo.position} cm⁻¹
        峰高：${peakInfo.height}
        面积：${peakInfo.area}
        半高宽：${peakInfo.fwhm} cm⁻¹`;
    
    showToast(message, 'info', 5000);
    addLog(`峰值分析：${peakInfo.position} cm⁻¹, 面积=${peakInfo.area}`, 'info');
}
```

---

## 四、物质识别

### 4.1 相似度计算

**后端实现**（`backend/inference.py`）：

```python
class LocalInference:
    # ... 现有代码 ...
    
    def cosine_similarity(self, s1: np.ndarray, s2: np.ndarray) -> float:
        """
        余弦相似度
        
        Args:
            s1: 光谱 1
            s2: 光谱 2
        
        Returns:
            相似度（0-1）
        """
        dot_product = np.dot(s1, s2)
        norm1 = np.linalg.norm(s1)
        norm2 = np.linalg.norm(s2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def correlation(self, s1: np.ndarray, s2: np.ndarray) -> float:
        """
        皮尔逊相关系数
        
        Args:
            s1: 光谱 1
            s2: 光谱 2
        
        Returns:
            相关系数（-1 到 1）
        """
        if len(s1) != len(s2):
            raise ValueError("光谱长度必须相同")
        
        corr_matrix = np.corrcoef(s1, s2)
        return float(corr_matrix[0, 1])
```

### 4.2 谱库匹配

**后端实现**（`backend/inference.py`）：

```python
import json
from pathlib import Path

class LocalInference:
    # ... 现有代码 ...
    
    def __init__(self, config_path: str = None):
        # ... 现有初始化 ...
        self._library = []
        self._load_library()
    
    def _load_library(self):
        """加载标准谱库"""
        library_path = Path(__file__).parent / 'library'
        if not library_path.exists():
            log.warning(f"[Inference] 谱库目录不存在：{library_path}")
            return
        
        for json_file in library_path.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._library.append({
                        'name': data.get('name', 'Unknown'),
                        'cas': data.get('cas', ''),
                        'spectrum': np.array(data.get('spectrum', [])),
                        'wavelength': np.array(data.get('wavelength', []))
                    })
                    log.info(f"[Inference] 加载谱图：{data.get('name')}")
            except Exception as e:
                log.error(f"[Inference] 加载谱图失败：{json_file}, {e}")
        
        log.info(f"[Inference] 共加载 {len(self._library)} 个标准谱图")
    
    def match_library(self, spectrum: np.ndarray, wavelength: np.ndarray, 
                     top_k: int = 3) -> list:
        """
        谱库匹配
        
        Args:
            spectrum: 待测光谱
            wavelength: 波长
            top_k: 返回前 K 个匹配结果
        
        Returns:
            list: [
                {
                    'name': '物质名',
                    'cas': 'CAS 号',
                    'similarity': 相似度,
                    'correlation': 相关系数
                },
                ...
            ]
        """
        if len(self._library) == 0:
            log.warning("[Inference] 谱库为空")
            return []
        
        results = []
        
        for ref in self._library:
            # 插值对齐波长
            ref_interp = self._interpolate_spectrum(ref.spectrum, ref.wavelength, wavelength)
            
            # 计算相似度
            similarity = self.cosine_similarity(spectrum, ref_interp)
            correlation = self.correlation(spectrum, ref_interp)
            
            results.append({
                'name': ref['name'],
                'cas': ref.get('cas', ''),
                'similarity': similarity,
                'correlation': correlation
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        log.info(f"[Inference] 谱库匹配完成，Top 1: {results[0]['name']} ({results[0]['similarity']:.4f})")
        return results[:top_k]
    
    def _interpolate_spectrum(self, spectrum: np.ndarray, wavelength: np.ndarray, 
                             target_wavelength: np.ndarray) -> np.ndarray:
        """
        插值光谱到目标波长
        
        Args:
            spectrum: 原始光谱
            wavelength: 原始波长
            target_wavelength: 目标波长
        
        Returns:
            插值后的光谱
        """
        from scipy.interpolate import interp1d
        
        # 创建插值函数
        f = interp1d(wavelength, spectrum, kind='linear', fill_value='extrapolate')
        return f(target_wavelength)
```

**谱库文件格式**（`backend/library/silicon.json`）：

```json
{
    "name": "硅 (Silicon)",
    "cas": "7440-21-3",
    "description": "单晶硅标准物质，特征峰 520 cm⁻¹",
    "wavelength": [200, 250, 300, ..., 3200],
    "spectrum": [0.01, 0.02, 0.01, ..., 0.01]
}
```

---

## 五、数据管理

### 5.1 导入历史数据

**后端实现**（`backend/bridge.py`）：

```python
import csv
import json

class BridgeObject(QObject):
    # ... 现有代码 ...
    
    @Slot(str, result=str)
    def loadData(self, file_path: str) -> str:
        """
        导入历史数据
        
        Args:
            file_path: 文件路径（CSV 或 JSON）
        
        Returns:
            JSON 字符串：{"wavelength": [...], "spectrum": [...]} 或错误信息
        """
        try:
            if file_path.endswith('.csv'):
                wavelength = []
                spectrum = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # 跳过表头
                    for row in reader:
                        wavelength.append(float(row[0]))
                        spectrum.append(float(row[1]))
            
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    wavelength = data.get('wavelength', [])
                    spectrum = data.get('spectrum', [])
            
            else:
                return json.dumps({'error': '不支持的文件格式'})
            
            # 数据验证
            if len(wavelength) != len(spectrum):
                return json.dumps({'error': '波长和光谱长度不匹配'})
            
            if len(wavelength) == 0:
                return json.dumps({'error': '数据为空'})
            
            result = {
                'wavelength': wavelength,
                'spectrum': spectrum
            }
            
            log.info(f"[Bridge] 导入数据成功：{file_path}")
            return json.dumps(result)
        
        except Exception as e:
            log.error(f"[Bridge] 导入数据失败：{e}")
            return json.dumps({'error': str(e)})
```

**前端实现**（`frontend/app.js`）：

```javascript
function importData() {
    if (!pythonBackend) {
        showToast('后端未连接', 'error');
        return;
    }
    
    // 创建文件选择对话框
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.json';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // 读取文件并发送到后端
        const reader = new FileReader();
        reader.onload = function(e) {
            // 这里需要后端支持文件选择对话框
            // 简化版：直接显示文件路径
            const filePath = file.path || file.name;
            const result = pythonBackend.loadData(filePath);
            
            try {
                const data = JSON.parse(result);
                if (data.error) {
                    showToast(`导入失败：${data.error}`, 'error');
                } else {
                    // 更新图表
                    wavelengthData = data.wavelength;
                    spectrumData = data.spectrum;
                    updateSpectrum(spectrumData);
                    showToast('数据导入成功', 'success');
                    addLog(`导入数据：${file.name}`, 'success');
                }
            } catch (err) {
                showToast(`解析失败：${err}`, 'error');
            }
        };
        reader.readAsText(file);
    };
    
    input.click();
}
```

---

## 六、标准谱库

### 6.1 谱库文件清单

创建 `backend/library/` 目录，包含以下文件：

1. **silicon.json** - 硅（520 cm⁻¹）
2. **diamond.json** - 金刚石（1332 cm⁻¹）
3. **graphite.json** - 石墨（1580, 2700 cm⁻¹）
4. **benzene.json** - 苯（992, 3060 cm⁻¹）
5. **ethanol.json** - 乙醇（880, 1050, 1450 cm⁻¹）
6. **acetone.json** - 丙酮（787, 1715, 2920 cm⁻¹）
7. **water.json** - 水（1640, 3400 cm⁻¹）
8. **quartz.json** - 石英（464, 696 cm⁻¹）
9. **calcite.json** - 方解石（1086 cm⁻¹）
10. **sulfur.json** - 硫（150, 220, 470 cm⁻¹）

### 6.2 谱图数据获取

1. **公开数据库**：
   - RShiftBase（拉曼位移数据库）
   - RRUFF 项目（矿物拉曼光谱）
   - NIST Chemistry WebBook

2. **实测数据**：
   - 使用标准物质实测
   - 仪器厂商提供

---

## 七、测试计划

### 7.1 单元测试

```python
# test_p0_features.py

def test_integration_time():
    """测试积分时间调节"""
    bridge = BridgeObject(state_manager, driver)
    bridge.setIntegrationTime(500)
    assert bridge.getIntegrationTime() == 500

def test_accumulation_count():
    """测试累加平均次数"""
    bridge = BridgeObject(state_manager, driver)
    bridge.setAccumulationCount(10)
    assert bridge.getAccumulationCount() == 10

def test_smooth():
    """测试平滑滤波"""
    inference = LocalInference()
    spectrum = np.random.randn(1024)
    smoothed = inference.smooth(spectrum, window_size=5)
    assert len(smoothed) == len(spectrum)
    assert np.std(smoothed) < np.std(spectrum)

def test_baseline_correction():
    """测试基线校正"""
    inference = LocalInference()
    spectrum = np.random.randn(1024) + 100  # 添加基线
    corrected, baseline = inference.baseline_correction(spectrum, method='poly')
    assert len(corrected) == len(spectrum)
    assert np.mean(corrected) < np.mean(spectrum)

def test_peak_area():
    """测试峰面积计算"""
    inference = LocalInference()
    # 创建模拟峰
    wavelength = np.linspace(200, 3200, 1024)
    spectrum = np.exp(-(wavelength - 520)**2 / (2 * 30**2))
    result = inference.calculate_peak_area(spectrum, wavelength, 520)
    assert result is not None
    assert result['position'] > 500 and result['position'] < 540
    assert result['area'] > 0

def test_cosine_similarity():
    """测试余弦相似度"""
    inference = LocalInference()
    s1 = np.array([1, 2, 3, 4, 5])
    s2 = np.array([1, 2, 3, 4, 5])
    s3 = np.array([5, 4, 3, 2, 1])
    assert inference.cosine_similarity(s1, s2) == 1.0
    assert inference.cosine_similarity(s1, s3) < 1.0

def test_match_library():
    """测试谱库匹配"""
    inference = LocalInference()
    # 使用谱库中的谱图作为测试
    if len(inference._library) > 0:
        ref = inference._library[0]
        results = inference.match_library(ref.spectrum, ref.wavelength)
        assert len(results) > 0
        assert results[0]['similarity'] > 0.9

def test_load_data():
    """测试导入数据"""
    bridge = BridgeObject(state_manager, driver)
    # 创建测试文件
    import tempfile
    import json
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'wavelength': [200, 300, 400], 'spectrum': [0.1, 0.2, 0.3]}, f)
        temp_path = f.name
    
    result = bridge.loadData(temp_path)
    data = json.loads(result)
    assert 'wavelength' in data
    assert 'spectrum' in data
    assert len(data['wavelength']) == 3
```

### 7.2 集成测试

```python
def test_p0_end_to_end():
    """P0 功能端到端测试"""
    # 1. 设置积分时间
    # 2. 设置累加次数
    # 3. 开始采集
    # 4. 平滑滤波
    # 5. 基线校正
    # 6. 峰面积计算
    # 7. 谱库匹配
    # 验证所有步骤正常
```

---

## 八、时间计划

| 日期 | 任务 | 预计时间 | 完成标志 |
|------|------|----------|----------|
| **第 1 天** | 积分时间调节 | 2 小时 | BridgeObject 添加方法，前端 UI 完成 |
| | 累加平均次数 | 2 小时 | BridgeObject 添加方法，前端 UI 完成 |
| **第 2 天** | 平滑滤波 | 2 小时 | inference.py 添加方法，测试通过 |
| | 基线校正 | 4 小时 | inference.py 添加方法，测试通过 |
| **第 3 天** | 峰面积计算 | 2 小时 | inference.py 添加方法，测试通过 |
| | 相似度计算 | 2 小时 | inference.py 添加方法，测试通过 |
| **第 4 天** | 谱库匹配 | 4 小时 | inference.py 添加方法，测试通过 |
| | 标准谱库（10 种） | 4 小时 | backend/library/ 目录创建完成 |
| **第 5 天** | 导入历史数据 | 2 小时 | BridgeObject 添加方法，测试通过 |
| | 前后端联调 | 2 小时 | 所有 P0 功能端到端测试通过 |
| **合计** | | **28 小时** | |

---

## 九、验收标准

### 9.1 功能验收

| 功能 | 验收标准 | 测试方法 |
|------|----------|----------|
| 积分时间调节 | 10-10000ms 可调，采集时间随之变化 | 手动测试 + 日志验证 |
| 累加平均次数 | 1-100 可调，信噪比提高 | 手动测试 + 对比光谱 |
| 平滑滤波 | 噪声降低，特征峰保持 | 对比平滑前后光谱 |
| 基线校正 | 荧光背景消除 | 对比校正前后光谱 |
| 峰面积计算 | 峰位、峰高、面积、半高宽准确 | 与标准值对比 |
| 谱库匹配 | Top 1 匹配正确率>90% | 使用已知物质测试 |
| 导入历史数据 | CSV/JSON 格式正常加载 | 手动测试 |

### 9.2 代码验收

- [ ] 所有函数有 docstring
- [ ] 关键代码有注释
- [ ] 异常处理完善
- [ ] 日志记录完整
- [ ] 单元测试通过
- [ ] 代码审查通过

---

*文档版本：1.0*
*创建日期：2026-03-20*
*最后更新：2026-03-20*
