# P0 功能详细开发方案

> **产品定位**：简易型拉曼光谱边缘客户端（教学/演示/快速检测）
> **开发周期**：4 天（28 小时）
> **目标评分**：82 分 → 85 分

---

## 📋 目录

1. [项目现状锐评](#一项目现状锐评)
2. [P0 功能开发顺序](#二 p0 功能开发顺序)
3. [第 1 天：采集参数控制](#三第 1 天采集参数控制)
4. [第 2 天：数据处理](#四第 2 天数据处理)
5. [第 3 天：峰值分析与物质识别](#五第 3 天峰值分析与物质识别)
6. [第 4 天：数据管理与集成测试](#六第 4 天数据管理与集成测试)
7. [测试计划](#七测试计划)
8. [风险与缓解](#八风险与缓解)

---

## 一、项目现状锐评

### ✅ 优势（82 分的基础）

| 模块 | 评分 | 亮点 |
|------|------|------|
| **前端** | 85 分 | Toast、加载动画、FPS、峰值标注、主题切换、响应式、快捷键——**功能比很多商业软件还好** |
| **测试** | 82 分 | 23 项测试 100% 通过——**测试覆盖率比 90% 的 Python 项目都高** |
| **通信层** | 82 分 | QWebChannel 端到端通了——**比手写 HTTP WebSocket 稳定** |
| **工作线程** | 88 分 | 原子操作 + QWaitCondition——**性能优化到位** |
| **代码规范** | 87 分 | 日志系统、异常处理、线程安全——**生产级代码** |
| **打包验证** | 82 分 | Qt 资源系统、exe 启动测试——**能打包发布** |

### ❌ 劣势（P0 缺失的 28 分）

| 问题 | 影响 | 严重性 |
|------|------|--------|
| **无积分时间调节** | 无法适应不同样品（液体/固体/粉末） | 🔴 严重 |
| **无累加平均** | 信噪比低，弱峰检测不到 | 🔴 严重 |
| **无平滑滤波** | 噪声大，谱图难看 | 🟡 中等 |
| **无基线校正** | 荧光背景无法消除，定量不准 | 🔴 严重 |
| **无峰面积计算** | 只能定性，不能定量 | 🟡 中等 |
| **无谱库匹配** | 无法识别物质——**这是拉曼光谱仪的核心功能！** | 🔴 致命 |
| **无标准谱库** | 有匹配算法也没用 | 🔴 致命 |

### 💀 P11 锐评

> **你现在的项目就像一个"漂亮的空壳"**：
> - 前端 UI 很漂亮（Toast、加载动画、主题切换）
> - 测试很完善（23 项测试 100% 通过）
> - 代码很规范（日志、异常、线程安全）
> - **但是！连最基本的物质识别都做不了！**

**这就像买了一辆特斯拉**：
- 中控大屏 17 英寸（= 你的前端 UI）
- 自动驾驶系统（= 你的 QWebChannel）
- 真皮座椅加热通风（= 你的 Toast、加载动画）
- **但是！没有电机和电池！（= 没有 P0 核心功能）**

**所以现在的 82 分是"外观分"，不是"功能分"！**

---

## 二、P0 功能开发顺序

### 优先级排序（按依赖关系）

```
第 1 天：采集参数控制
  ├─ 积分时间调节（BridgeObject → WorkerThread → MockDriver）
  └─ 累加平均次数（同上）

第 2 天：数据处理
  ├─ 平滑滤波（inference.py → scipy.signal.savgol_filter）
  └─ 基线校正（inference.py → 多项式拟合 + airPLS）

第 3 天：峰值分析与物质识别
  ├─ 峰面积计算（inference.py → scipy.signal.find_peaks + np.trapz）
  ├─ 相似度计算（inference.py → 余弦相似度 + 相关系数）
  ├─ 谱库匹配（inference.py → 加载谱库 + 插值对齐 + 排序）
  └─ 标准谱库（backend/library/*.json - 10 种物质）

第 4 天：数据管理与集成测试
  ├─ 导入历史数据（BridgeObject → CSV/JSON 解析）
  ├─ 前端 UI 集成（index.html → 新增 P0 控件）
  └─ 端到端测试（test_p0_features.py → 8 项测试）
```

### 依赖关系图

```
积分时间调节 ──┬─→ 平滑滤波 ──→ 峰面积计算 ──→ 谱库匹配
累加平均次数 ──┘              │
                              ↓
                        基线校正 ──→ 相似度计算
                                        ↓
                                    标准谱库（并行开发）
```

---

## 三、第 1 天：采集参数控制

### 3.1 积分时间调节（2 小时）

#### 后端修改（1 小时）

**文件**：`main.py`（BridgeObject 类）

**修改位置**：在 `BridgeObject.__init__()` 中添加：

```python
# 在 __init__ 方法中，添加以下代码（约第 120 行）
self._integration_time = 100  # 默认 100ms
self._accumulation_count = 1  # 默认 1 次
```

**添加方法**（在 `exportData()` 方法后面）：

```python
@Slot(int)
def setIntegrationTime(self, ms: int):
    """
    设置积分时间（毫秒）
    
    Args:
        ms: 积分时间，范围 10-10000ms
    """
    if ms < 10:
        ms = 10
        log.warning("[Bridge] 积分时间过小，已设置为 10ms")
    elif ms > 10000:
        ms = 10000
        log.warning("[Bridge] 积分时间过大，已设置为 10000ms")
    
    self._integration_time = ms
    log.info(f"[Bridge] 积分时间设置为：{ms}ms")
    
    # 通知 WorkerThread 更新（如果有引用）
    if hasattr(self, '_worker_thread'):
        self._worker_thread.integration_time = ms

@Slot(result=int)
def getIntegrationTime(self) -> int:
    """获取当前积分时间"""
    return self._integration_time
```

**文件**：`main.py`（WorkerThread 类）

**修改位置**：在 `WorkerThread.__init__()` 中添加：

```python
# 在 __init__ 方法中，添加（约第 360 行）
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
```

**修改采集循环**（在 `run()` 方法中，约第 420 行）：

```python
# 找到原来的采集代码（while 循环内）
# 原代码可能是：
# spectrum = self.driver.read_spectrum()

# 修改为：
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
```

**文件**：`backend/driver/mock_driver.py`

**修改**：在 `read_spectrum()` 方法中添加积分时间参数：

```python
def read_spectrum(self, integration_time: int = 100) -> np.ndarray:
    """
    读取光谱数据
    
    Args:
        integration_time: 积分时间（毫秒），影响信号强度
    """
    # 检查设备状态
    if not self.is_connected:
        raise RuntimeError("Device not connected")
    
    # 模拟积分时间对信号的影响（积分时间越长，信号越强）
    intensity_factor = integration_time / 100.0  # 相对于 100ms 的倍数
    
    # ... 原有模拟代码 ...
    # 在生成光谱时乘以 intensity_factor
```

#### 前端修改（1 小时）

**文件**：`frontend/index.html`

**修改位置**：在控制面板中，噪声滑块前面（约第 50 行）：

```html
<!-- 在"噪声水平"前面添加 -->
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

**文件**：`frontend/app.js`

**添加函数**（在 `updateNoise()` 函数前面，约第 270 行）：

```javascript
function updateIntegrationTime(value) {
    const ms = parseInt(value);
    document.getElementById('integration-time-value').textContent = ms;
    if (pythonBackend) {
        pythonBackend.setIntegrationTime(ms);
        addLog(`积分时间设置为：${ms}ms`, 'info');
    }
}

function updateAccumulationCount(value) {
    const n = parseInt(value);
    document.getElementById('accumulation-count-value').textContent = n;
    if (pythonBackend) {
        pythonBackend.setAccumulationCount(n);
        addLog(`累加次数设置为：${n}`, 'info');
    }
}
```

---

### 3.2 累加平均次数（2 小时）

**与积分时间调节一起实现**，代码已在上面给出。

---

## 四、第 2 天：数据处理

### 4.1 平滑滤波（2 小时）

#### 后端实现（1 小时）

**文件**：`backend/inference.py`

**添加方法**（在 `MockInference` 类中，约第 200 行）：

```python
from scipy.signal import savgol_filter

class LocalInference:
    # ... 现有代码 ...
    
    def smooth(self, spectrum: np.ndarray, window_size: int = 5, 
               polyorder: int = 2, method: str = 'sg') -> np.ndarray:
        """
        Savitzky-Golay 平滑滤波
        
        Args:
            spectrum: 输入光谱
            window_size: 窗口大小（必须为奇数，3-15）
            polyorder: 多项式阶数（默认 2）
            method: 滤波方法（'sg'=Savitzky-Golay, 'ma'=移动平均）
        
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
        
        if method == 'sg':
            smoothed = savgol_filter(spectrum, window_size, polyorder, mode='mirror')
        elif method == 'ma':
            # 简化版移动平均
            kernel = np.ones(window_size) / window_size
            smoothed = np.convolve(spectrum, kernel, mode='same')
        else:
            log.warning(f"[Inference] 未知滤波方法：{method}，使用 Savitzky-Golay")
            smoothed = savgol_filter(spectrum, window_size, polyorder, mode='mirror')
        
        log.info(f"[Inference] 平滑滤波完成：method={method}, window={window_size}")
        return smoothed
```

**添加前端调用接口**（在 `BridgeObject` 类中）：

```python
@Slot(list, int, result=list)
def smoothSpectrum(self, spectrum: list, window_size: int = 5) -> list:
    """
    平滑光谱
    
    Args:
        spectrum: 光谱数据（列表）
        window_size: 窗口大小（3-15）
    
    Returns:
        平滑后的光谱（列表）
    """
    if self._inference is None:
        log.error("[Bridge] 推理模块未初始化")
        return spectrum
    
    spectrum_np = np.array(spectrum)
    smoothed = self._inference.smooth(spectrum_np, window_size)
    return smoothed.tolist()
```

#### 前端实现（1 小时）

**文件**：`frontend/index.html`

**添加控件**（在噪声滑块后面）：

```html
<div class="control-group">
    <label>平滑滤波：<span id="smooth-status">关</span></label>
    <button class="btn btn-primary" id="btn-smooth" onclick="toggleSmooth()">
        开启
    </button>
    <input type="range" id="smooth-window" min="3" max="15" step="2" 
           value="5" onchange="updateSmoothWindow(this.value)" disabled>
    <label>窗口大小：<span id="smooth-window-value">5</span></label>
</div>
```

**文件**：`frontend/app.js`

**添加全局变量**（约第 20 行）：

```javascript
let smoothEnabled = false;
let smoothWindow = 5;
```

**添加函数**（在 `updateNoise()` 后面）：

```javascript
function toggleSmooth() {
    smoothEnabled = !smoothEnabled;
    const btn = document.getElementById('btn-smooth');
    const slider = document.getElementById('smooth-window');
    const status = document.getElementById('smooth-status');
    
    btn.textContent = smoothEnabled ? '关闭' : '开启';
    status.textContent = smoothEnabled ? '开' : '关';
    slider.disabled = !smoothEnabled;
    
    addLog(`平滑滤波已${smoothEnabled ? '开启' : '关闭'}`, 'info');
    
    // 如果已开启，重新处理当前光谱
    if (smoothEnabled && spectrumData.length > 0) {
        applySmoothToCurrentSpectrum();
    }
}

function updateSmoothWindow(value) {
    smoothWindow = parseInt(value);
    document.getElementById('smooth-window-value').textContent = value;
    addLog(`平滑窗口设置为：${value}`, 'info');
    
    // 重新处理当前光谱
    if (smoothEnabled) {
        applySmoothToCurrentSpectrum();
    }
}

function applySmoothToCurrentSpectrum() {
    if (!pythonBackend || spectrumData.length === 0) return;
    
    const smoothed = pythonBackend.smoothSpectrum(spectrumData, smoothWindow);
    updateSpectrum(smoothed);
    addLog('光谱平滑处理完成', 'success');
}
```

---

### 4.2 基线校正（4 小时）

#### 后端实现（2.5 小时）

**文件**：`backend/inference.py`

**添加方法**（在 `smooth()` 方法后面）：

```python
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
    
    def _airpls(self, spectrum: np.ndarray, max_iter: int = 100, 
                lam: float = 1e5) -> np.ndarray:
        """
        airPLS 基线校正算法（自适应迭代重加权惩罚最小二乘）
        
        Args:
            spectrum: 输入光谱
            max_iter: 最大迭代次数
            lam: 平滑参数
        
        Returns:
            baseline: 基线
        """
        n = len(spectrum)
        baseline = np.zeros(n)
        
        try:
            from scipy.sparse import spdiags
            from scipy.linalg import cho_factor, cho_solve
            
            # 简化版 airpls（完整版需要稀疏矩阵优化）
            for iteration in range(max_iter):
                diff = spectrum - baseline
                
                # 计算权重
                weights = np.ones(n)
                negative_mask = diff < 0
                weights[negative_mask] = np.exp(diff[negative_mask] / np.std(spectrum))
                
                # 加权平滑（使用高斯滤波近似）
                from scipy.ndimage import gaussian_filter1d
                numerator = gaussian_filter1d(spectrum * weights, sigma=50)
                denominator = gaussian_filter1d(weights, sigma=50) + 1e-10
                baseline = numerator / denominator
                
                # 收敛判断
                if np.max(np.abs(diff)) < 1e-6:
                    log.info(f"[Inference] airPLS 收敛于第 {iteration + 1} 次迭代")
                    break
            
            log.info(f"[Inference] airPLS 完成，迭代次数：{iteration + 1}")
            
        except Exception as e:
            log.error(f"[Inference] airPLS 计算失败：{e}，回退到多项式拟合")
            x = np.arange(n)
            coeffs = np.polyfit(x, spectrum, 3)
            baseline = np.polyval(coeffs, x)
        
        return baseline
```

**添加前端调用接口**（在 `BridgeObject` 类中）：

```python
@Slot(list, str, int, result=str)
def baselineCorrection(self, spectrum: list, method: str = 'poly', 
                       order: int = 3) -> str:
    """
    基线校正
    
    Args:
        spectrum: 光谱数据（列表）
        method: 方法（'poly' 或 'airpls'）
        order: 多项式阶数
    
    Returns:
        JSON 字符串：{"corrected": [...], "baseline": [...]}
    """
    import json
    
    if self._inference is None:
        log.error("[Bridge] 推理模块未初始化")
        return json.dumps({'error': 'Inference module not initialized'})
    
    spectrum_np = np.array(spectrum)
    corrected, baseline = self._inference.baseline_correction(spectrum_np, method, order)
    
    result = {
        'corrected': corrected.tolist(),
        'baseline': baseline.tolist()
    }
    
    return json.dumps(result)
```

#### 前端实现（1.5 小时）

**文件**：`frontend/index.html`

**添加控件**（在平滑滤波后面）：

```html
<div class="control-group">
    <label>基线校正：<span id="baseline-status">关</span></label>
    <button class="btn btn-primary" id="btn-baseline" onclick="toggleBaseline()">
        开启
    </button>
    <select id="baseline-method" onchange="updateBaselineMethod(this.value)" disabled>
        <option value="poly">多项式拟合</option>
        <option value="airpls">airPLS</option>
    </select>
    <input type="number" id="baseline-order" min="1" max="10" value="3" 
           onchange="updateBaselineOrder(this.value)" disabled>
    <label>多项式阶数</label>
</div>
```

**文件**：`frontend/app.js`

**添加全局变量**：

```javascript
let baselineEnabled = false;
let baselineMethod = 'poly';
let baselineOrder = 3;
let originalSpectrum = [];  // 保存原始光谱
```

**添加函数**（在 `toggleSmooth()` 后面）：

```javascript
function toggleBaseline() {
    baselineEnabled = !baselineEnabled;
    const btn = document.getElementById('btn-baseline');
    const methodSelect = document.getElementById('baseline-method');
    const orderInput = document.getElementById('baseline-order');
    const status = document.getElementById('baseline-status');
    
    btn.textContent = baselineEnabled ? '关闭' : '开启';
    status.textContent = baselineEnabled ? '开' : '关';
    methodSelect.disabled = !baselineEnabled;
    orderInput.disabled = !baselineEnabled;
    
    if (baselineEnabled) {
        // 保存原始光谱
        originalSpectrum = [...spectrumData];
        applyBaselineToCurrentSpectrum();
    } else {
        // 恢复原始光谱
        if (originalSpectrum.length > 0) {
            updateSpectrum(originalSpectrum);
        }
    }
    
    addLog(`基线校正已${baselineEnabled ? '开启' : '关闭'}`, 'info');
}

function updateBaselineMethod(value) {
    baselineMethod = value;
    addLog(`基线校正方法：${value}`, 'info');
    if (baselineEnabled) {
        applyBaselineToCurrentSpectrum();
    }
}

function updateBaselineOrder(value) {
    baselineOrder = parseInt(value);
    addLog(`基线校正阶数：${value}`, 'info');
    if (baselineEnabled) {
        applyBaselineToCurrentSpectrum();
    }
}

function applyBaselineToCurrentSpectrum() {
    if (!pythonBackend || spectrumData.length === 0) return;
    
    const resultJson = pythonBackend.baselineCorrection(spectrumData, baselineMethod, baselineOrder);
    const result = JSON.parse(resultJson);
    
    if (result.error) {
        showToast(`基线校正失败：${result.error}`, 'error');
        return;
    }
    
    // 显示校正后光谱
    updateSpectrum(result.corrected);
    addLog('基线校正完成', 'success');
    
    // 可选：显示基线
    // showBaseline(result.baseline);
}
```

---

## 五、第 3 天：峰值分析与物质识别

### 5.1 峰面积计算（2 小时）

#### 后端实现（1 小时）

**文件**：`backend/inference.py`

**添加方法**（在 `baseline_correction()` 后面）：

```python
from scipy.signal import find_peaks

class LocalInference:
    # ... 现有代码 ...
    
    def calculate_peak_area(self, spectrum: np.ndarray, wavelength: np.ndarray,
                           peak_pos: float, window: float = 50) -> Optional[Dict]:
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
            } 或 None（如果未找到峰）
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
        
        # 基线校正（局部线性基线）
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

**添加前端调用接口**（在 `BridgeObject` 类中）：

```python
@Slot(list, list, float, float, result=str)
def calculatePeakArea(self, spectrum: list, wavelength: list, 
                      peak_pos: float, window: float = 50) -> str:
    """
    计算峰面积
    
    Args:
        spectrum: 光谱数据（列表）
        wavelength: 波长数据（列表）
        peak_pos: 峰位置
        window: 积分窗口
    
    Returns:
        JSON 字符串：峰面积结果
    """
    import json
    
    if self._inference is None:
        return json.dumps({'error': 'Inference module not initialized'})
    
    spectrum_np = np.array(spectrum)
    wavelength_np = np.array(wavelength)
    
    result = self._inference.calculate_peak_area(spectrum_np, wavelength_np, peak_pos, window)
    
    if result is None:
        return json.dumps({'error': 'Peak not found'})
    
    return json.dumps(result)
```

#### 前端实现（1 小时）

**文件**：`frontend/app.js`

**修改**：在 `initChart()` 函数中，添加点击事件（在 `chart.on('rendered', ...)` 后面）：

```javascript
// 点击光谱显示峰信息
chart.on('click', function(params) {
    if (params.componentType === 'series' && params.seriesName === '光谱') {
        const wavelength = params.value[0];
        const intensity = params.value[1];
        
        // 计算峰面积
        calculateAndShowPeakInfo(wavelength, intensity);
    }
});

function calculateAndShowPeakInfo(peakPos, peakHeight) {
    if (!pythonBackend) return;
    
    const window = 50;  // cm⁻¹
    const resultJson = pythonBackend.calculatePeakArea(
        spectrumData, wavelengthData, peakPos, window
    );
    const result = JSON.parse(resultJson);
    
    if (result.error) {
        showToast(`未找到峰：${result.error}`, 'warning');
        return;
    }
    
    const message = `峰信息：
        峰位：${result.position.toFixed(1)} cm⁻¹
        峰高：${result.height.toFixed(4)}
        面积：${result.area.toFixed(2)}
        半高宽：${result.fwhm.toFixed(1)} cm⁻¹`;
    
    showToast(message, 'info', 5000);
    addLog(`峰值分析：${result.position.toFixed(1)} cm⁻¹, 面积=${result.area.toFixed(2)}`, 'info');
}
```

---

### 5.2 相似度计算（1 小时）

#### 后端实现

**文件**：`backend/inference.py`

**添加方法**（在 `calculate_peak_area()` 后面）：

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
        return float(np.clip(similarity, 0.0, 1.0))
    
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
        return float(np.clip(corr_matrix[0, 1], -1.0, 1.0))
```

---

### 5.3 谱库匹配（3 小时）

#### 后端实现（2 小时）

**文件**：`backend/inference.py`

**添加谱库加载**（在 `__init__` 方法中）：

```python
class LocalInference:
    def __init__(self, config_path: str = None):
        # ... 现有初始化 ...
        self._library = []
        self._load_library()
    
    def _load_library(self):
        """加载标准谱库"""
        library_path = Path(__file__).parent / 'library'
        if not library_path.exists():
            log.warning(f"[Inference] 谱库目录不存在：{library_path}")
            library_path.mkdir(parents=True, exist_ok=True)
            return
        
        json_files = list(library_path.glob('*.json'))
        if len(json_files) == 0:
            log.warning(f"[Inference] 谱库目录为空：{library_path}")
            return
        
        for json_file in json_files:
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._library.append({
                        'name': data.get('name', 'Unknown'),
                        'cas': data.get('cas', ''),
                        'description': data.get('description', ''),
                        'spectrum': np.array(data.get('spectrum', [])),
                        'wavelength': np.array(data.get('wavelength', []))
                    })
                    log.info(f"[Inference] 加载谱图：{data.get('name')}")
            except Exception as e:
                log.error(f"[Inference] 加载谱图失败：{json_file}, {e}")
        
        log.info(f"[Inference] 共加载 {len(self._library)} 个标准谱图")
```

**添加谱库匹配方法**（在 `correlation()` 后面）：

```python
class LocalInference:
    # ... 现有代码 ...
    
    def match_library(self, spectrum: np.ndarray, wavelength: np.ndarray,
                     top_k: int = 3) -> List[Dict]:
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
                    'correlation': 相关系数,
                    'rank': 排名
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
            ref_interp = self._interpolate_spectrum(ref['spectrum'], ref['wavelength'], wavelength)
            
            # 计算相似度
            similarity = self.cosine_similarity(spectrum, ref_interp)
            correlation = self.correlation(spectrum, ref_interp)
            
            results.append({
                'name': ref['name'],
                'cas': ref.get('cas', ''),
                'description': ref.get('description', ''),
                'similarity': similarity,
                'correlation': correlation
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 添加排名
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
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

**添加前端调用接口**（在 `BridgeObject` 类中）：

```python
@Slot(list, list, int, result=str)
def matchLibrary(self, spectrum: list, wavelength: list, top_k: int = 3) -> str:
    """
    谱库匹配
    
    Args:
        spectrum: 待测光谱
        wavelength: 波长
        top_k: 返回前 K 个
    
    Returns:
        JSON 字符串：匹配结果列表
    """
    import json
    
    if self._inference is None:
        return json.dumps({'error': 'Inference module not initialized'})
    
    spectrum_np = np.array(spectrum)
    wavelength_np = np.array(wavelength)
    
    results = self._inference.match_library(spectrum_np, wavelength_np, top_k)
    
    return json.dumps(results)
```

#### 前端实现（1 小时）

**文件**：`frontend/index.html`

**添加谱库匹配面板**（在控制面板后面，日志面板前面）：

```html
<!-- 在控制面板后面添加 -->
<div class="library-panel" id="library-panel" style="display: none;">
    <h3>谱库匹配结果</h3>
    <div id="match-results"></div>
    <button class="btn btn-primary" onclick="closeLibraryPanel()">关闭</button>
</div>
```

**文件**：`frontend/styles.css`

**添加样式**（在日志面板样式后面）：

```css
/* 谱库匹配面板 */
.library-panel {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 15px;
    margin: 0 20px 20px;
    border: 1px solid var(--border-color);
    max-height: 300px;
    overflow-y: auto;
}

.library-panel h3 {
    color: var(--accent-color);
    margin-bottom: 15px;
}

.match-item {
    background: var(--bg-tertiary);
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 4px;
    border-left: 4px solid var(--accent-color);
}

.match-item .rank {
    font-weight: bold;
    color: var(--accent-color);
}

.match-item .name {
    font-size: 1.1em;
    margin: 5px 0;
}

.match-item .similarity {
    color: #00ff88;
}
```

**文件**：`frontend/app.js`

**添加函数**（在文件末尾）：

```javascript
function showLibraryMatch() {
    if (!pythonBackend || spectrumData.length === 0) {
        showToast('无光谱数据', 'warning');
        return;
    }
    
    const resultJson = pythonBackend.matchLibrary(spectrumData, wavelengthData, 3);
    const results = JSON.parse(resultJson);
    
    if (results.error) {
        showToast(`匹配失败：${results.error}`, 'error');
        return;
    }
    
    if (results.length === 0) {
        showToast('谱库为空', 'warning');
        return;
    }
    
    // 显示匹配面板
    const panel = document.getElementById('library-panel');
    const resultsDiv = document.getElementById('match-results');
    
    resultsDiv.innerHTML = results.map(r => `
        <div class="match-item">
            <div class="rank">第${r.rank}名</div>
            <div class="name">${r.name}</div>
            <div>CAS: ${r.cas || 'N/A'}</div>
            <div class="similarity">相似度：${(r.similarity * 100).toFixed(1)}%</div>
            <div>相关系数：${(r.correlation * 100).toFixed(1)}%</div>
        </div>
    `).join('');
    
    panel.style.display = 'block';
    addLog(`谱库匹配完成，Top 1: ${results[0].name}`, 'success');
}

function closeLibraryPanel() {
    document.getElementById('library-panel').style.display = 'none';
}
```

**添加按钮**（在 `frontend/index.html` 控制面板中）：

```html
<button class="btn btn-primary" onclick="showLibraryMatch()">
    谱库匹配
</button>
```

---

### 5.4 标准谱库（2 小时）

**创建目录**：`backend/library/`

**创建谱图文件**（10 种物质）：

**文件**：`backend/library/silicon.json`

```json
{
    "name": "硅 (Silicon)",
    "cas": "7440-21-3",
    "description": "单晶硅标准物质，特征峰 520 cm⁻¹",
    "wavelength": [200, 210, 220, ..., 3200],
    "spectrum": [0.01, 0.01, 0.01, ..., 0.01]
}
```

**注意**：谱图数据需要从公开数据库获取或实测。可以使用以下资源：
- RRUFF 项目：http://rruff.info/
- RShiftBase
- NIST Chemistry WebBook

**简化方案**：先用模拟数据（高斯峰）：

```python
# 生成模拟谱图的脚本
import numpy as np
import json

def generate_mock_spectrum(peaks, wavelength_range=(200, 3200), num_points=1024):
    """
    生成模拟谱图
    
    Args:
        peaks: [(position, intensity, width), ...]
        wavelength_range: (min, max)
        num_points: 点数
    """
    wavelength = np.linspace(wavelength_range[0], wavelength_range[1], num_points)
    spectrum = np.ones(num_points) * 0.01  # 基线
    
    for pos, intensity, width in peaks:
        spectrum += intensity * np.exp(-(wavelength - pos)**2 / (2 * width**2))
    
    return {
        'wavelength': wavelength.tolist(),
        'spectrum': spectrum.tolist()
    }

# 硅（520 cm⁻¹）
silicon = generate_mock_spectrum([(520, 1.0, 15)])
with open('backend/library/silicon.json', 'w') as f:
    json.dump({
        'name': '硅 (Silicon)',
        'cas': '7440-21-3',
        'description': '单晶硅标准物质，特征峰 520 cm⁻¹'
    }, f)
    f.write(',')
    f.write(json.dumps(silicon))

# ... 其他 9 种物质
```

---

## 六、第 4 天：数据管理与集成测试

### 6.1 导入历史数据（2 小时）

#### 后端实现（1 小时）

**文件**：`main.py`（BridgeObject 类）

**添加方法**（在 `exportData()` 后面）：

```python
@Slot(str, result=str)
def loadData(self, file_path: str) -> str:
    """
    导入历史数据
    
    Args:
        file_path: 文件路径（CSV 或 JSON）
    
    Returns:
        JSON 字符串：{"wavelength": [...], "spectrum": [...]} 或错误信息
    """
    import csv
    import json
    
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
            return json.dumps({'error': '不支持的文件格式，支持 CSV 和 JSON'})
        
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

#### 前端实现（1 小时）

**文件**：`frontend/index.html`

**添加按钮**（在控制面板中）：

```html
<button class="btn btn-primary" onclick="importData()">
    导入数据
</button>
```

**文件**：`frontend/app.js`

**添加函数**：

```javascript
function importData() {
    if (!pythonBackend) {
        showToast('后端未连接', 'error');
        return;
    }
    
    // 创建文件输入
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.json';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // 注意：QWebChannel 不支持直接文件传输
        // 需要后端提供文件选择对话框
        // 简化方案：显示文件路径，让用户手动输入
        
        const filePath = file.path || file.name;
        showToast(`请选择文件：${filePath}`, 'info');
        
        // 实际使用时，需要后端调用 QFileDialog
        // 这里简化处理
    };
    
    input.click();
}
```

---

### 6.2 前后端联调（2 小时）

**测试清单**：

1. 积分时间调节 - 改变积分时间，观察信号强度变化
2. 累加平均 - 改变累加次数，观察噪声变化
3. 平滑滤波 - 开启平滑，观察谱图平滑度
4. 基线校正 - 开启基线校正，观察基线消除效果
5. 峰面积计算 - 点击光谱，查看峰信息
6. 谱库匹配 - 点击匹配，查看匹配结果
7. 导入数据 - 导入 CSV/JSON，查看是否正确加载

---

## 七、测试计划

### 7.1 单元测试（`test_p0_features.py`）

```python
"""
P0 功能单元测试
"""
import pytest
import numpy as np
from main import BridgeObject, WorkerThread
from backend.state_manager import StateManager
from backend.driver import MockDriver
from backend.inference import LocalInference


def test_integration_time():
    """测试积分时间调节"""
    driver = MockDriver()
    state_manager = StateManager()
    bridge = BridgeObject(state_manager, driver)
    
    # 设置积分时间
    bridge.setIntegrationTime(500)
    assert bridge.getIntegrationTime() == 500
    
    # 边界测试
    bridge.setIntegrationTime(5)  # 小于 10
    assert bridge.getIntegrationTime() == 10
    
    bridge.setIntegrationTime(20000)  # 大于 10000
    assert bridge.getIntegrationTime() == 10000


def test_accumulation_count():
    """测试累加平均次数"""
    driver = MockDriver()
    state_manager = StateManager()
    bridge = BridgeObject(state_manager, driver)
    
    bridge.setAccumulationCount(10)
    # 需要添加 getAccumulationCount 方法


def test_smooth():
    """测试平滑滤波"""
    inference = LocalInference()
    
    # 创建带噪声的光谱
    spectrum = np.sin(np.linspace(0, 10, 1024)) + np.random.randn(1024) * 0.1
    
    # 平滑
    smoothed = inference.smooth(spectrum, window_size=5)
    
    # 验证平滑后噪声降低
    assert np.std(smoothed) < np.std(spectrum)
    assert len(smoothed) == len(spectrum)


def test_baseline_correction():
    """测试基线校正"""
    inference = LocalInference()
    
    # 创建带基线的光谱
    x = np.linspace(0, 10, 1024)
    baseline = 0.1 * x + 5
    spectrum = np.sin(x) + baseline
    
    # 基线校正
    corrected, bl = inference.baseline_correction(spectrum, method='poly', order=1)
    
    # 验证基线被消除
    assert np.mean(corrected) < np.mean(spectrum)
    assert len(corrected) == len(spectrum)


def test_peak_area():
    """测试峰面积计算"""
    inference = LocalInference()
    
    # 创建模拟峰
    wavelength = np.linspace(200, 3200, 1024)
    spectrum = np.exp(-(wavelength - 520)**2 / (2 * 30**2))
    
    # 计算峰面积
    result = inference.calculate_peak_area(spectrum, wavelength, 520, window=50)
    
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
    
    # 确保谱库不为空
    if len(inference._library) == 0:
        pytest.skip("谱库为空")
    
    # 使用谱库中的谱图作为测试
    ref = inference._library[0]
    results = inference.match_library(ref['spectrum'], ref['wavelength'])
    
    assert len(results) > 0
    assert results[0]['similarity'] > 0.9  # 自身匹配应该很高


def test_load_data():
    """测试导入数据"""
    import tempfile
    import json
    
    driver = MockDriver()
    state_manager = StateManager()
    bridge = BridgeObject(state_manager, driver)
    
    # 创建测试 JSON 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'wavelength': [200, 300, 400],
            'spectrum': [0.1, 0.2, 0.3]
        }, f)
        temp_path = f.name
    
    result = bridge.loadData(temp_path)
    data = json.loads(result)
    
    assert 'wavelength' in data
    assert 'spectrum' in data
    assert len(data['wavelength']) == 3
```

---

## 八、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **谱库数据获取困难** | 中 | 高 | 先用模拟数据，后续补充真实谱图 |
| **airPLS 算法收敛慢** | 高 | 中 | 限制最大迭代次数，提供多项式拟合备选 |
| **前端文件导入受限** | 高 | 中 | 后端提供 QFileDialog，或简化为路径输入 |
| **积分时间影响采集速度** | 中 | 中 | 提示用户合理设置积分时间 |
| **累加平均降低帧率** | 高 | 低 | 显示实际帧率，让用户权衡 |

---

## 九、总结

### 开发时间线

| 日期 | 任务 | 小时 | 完成标志 |
|------|------|------|----------|
| **第 1 天** | 积分时间 + 累加平均 | 4 | BridgeObject 方法完成，前端 UI 完成 |
| **第 2 天** | 平滑滤波 + 基线校正 | 6 | inference.py 方法完成，前端 UI 完成 |
| **第 3 天** | 峰面积 + 谱库匹配 + 谱库 | 8 | 匹配功能完成，10 种谱图完成 |
| **第 4 天** | 导入数据 + 联调测试 | 8 | 8 项单元测试通过 |
| **合计** | | **26 小时** | |

### 预期成果

- ✅ 积分时间 10-10000ms 可调
- ✅ 累加平均 1-100 次可调
- ✅ Savitzky-Golay 平滑滤波
- ✅ 多项式拟合 + airPLS 基线校正
- ✅ 峰面积、峰高、半高宽计算
- ✅ 余弦相似度 + 相关系数
- ✅ 谱库匹配（Top 3）
- ✅ 10 种标准物质谱图
- ✅ CSV/JSON 数据导入
- ✅ 8 项单元测试通过

### 评分变化

| 模块 | 当前 | 完成后 | 变化 |
|------|------|--------|------|
| 工作线程 | 88 | 90 | +2（累加平均） |
| 前端 | 85 | 88 | +3（P0 UI） |
| 测试 | 82 | 85 | +3（P0 测试） |
| 算法推理 | 72 | 82 | +10（平滑、基线、峰值、匹配） |
| **总体** | **82** | **85** | **+3** |

---

*文档版本：1.0*
*创建日期：2026-03-20*
