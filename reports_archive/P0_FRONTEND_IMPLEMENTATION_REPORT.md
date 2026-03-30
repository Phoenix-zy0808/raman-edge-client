# P0 功能实现报告 - 前端部分

**实现日期**: 2026-03-23  
**实现工程师**: P11 级全栈工程师  
**实现阶段**: 前端 UI 完成

---

## 📊 实现进度

| 功能 | 后端 | 前端 UI | 测试 | 完成度 |
|------|------|--------|------|--------|
| 波长校准 | ✅ 完成 | ✅ 完成 | ⏳ 待编写 | 70% |
| 强度校准 | ✅ 完成 | ✅ 完成 | ⏳ 待编写 | 70% |
| 自动曝光 | ✅ 完成 | ✅ 完成 | ⏳ 待编写 | 70% |

---

## ✅ 已完成的前端实现

### 1. HTML 结构更新

**文件**: `frontend/index.html`

**新增元素**:

#### 状态栏校准状态指示器
```html
<!-- 波长校准状态 -->
<div class="status-item">
    <div class="status-indicator disconnected" id="wavelength-calibration-status"></div>
    <span>波长校准：<span id="wavelength-calibration-text">未校准</span></span>
</div>

<!-- 强度校准状态 -->
<div class="status-item">
    <div class="status-indicator disconnected" id="intensity-calibration-status"></div>
    <span>强度校准：<span id="intensity-calibration-text">未校准</span></span>
</div>
```

#### 自动曝光控制
```html
<!-- 自动曝光开关 -->
<div class="control-group">
    <label>自动曝光:</label>
    <label class="switch">
        <input type="checkbox" id="auto-exposure-toggle" onchange="toggleAutoExposure()">
        <span class="slider"></span>
    </label>
    <span id="auto-exposure-status">关</span>
</div>

<!-- 目标强度滑块 -->
<div class="control-group" id="auto-exposure-target-group">
    <label>目标强度：<span id="auto-exposure-target-value">0.70</span></label>
    <input type="range" id="auto-exposure-target" min="0.5" max="0.8" step="0.05" value="0.7">
    <button onclick="runAutoExposure()">▶️ 执行自动曝光</button>
</div>
```

#### 校准按钮
```html
<button onclick="calibrateWavelengthUI()">🔬 波长校准</button>
<button onclick="calibrateIntensityUI()">💡 强度校准</button>
```

---

### 2. CSS 样式更新

**文件**: `frontend/styles.css`

**新增样式**:

#### 开关控件
```css
.switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
}

.slider {
    background-color: #333;
    border-radius: 24px;
}

input:checked + .slider {
    background-color: #00d9ff;
}

input:checked + .slider:before {
    transform: translateX(26px);
    background-color: #fff;
}
```

#### 校准状态指示器
```css
#wavelength-calibration-status.connected,
#intensity-calibration-status.connected {
    background-color: #00ff88;
    box-shadow: 0 0 10px #00ff88;
}
```

---

### 3. Bridge 模块更新

**文件**: `frontend/js/bridge.js`

**新增方法**:

```javascript
// 波长校准
export function calibrateWavelength(referencePeaks)
export function getWavelengthCorrection()
export function isWavelengthCalibrated()

// 强度校准
export function calibrateIntensity(referenceSpectrum, theoreticalSpectrum)
export function getIntensityCorrection()

// 自动曝光
export function autoExposure(targetIntensity, maxIterations)
export function setAutoExposureEnabled(enabled)
export function isAutoExposureEnabled()

// 综合状态
export function getCalibrationStatus()
```

---

### 4. Main 模块更新

**文件**: `frontend/js/main.js`

**新增全局函数**:

#### 波长校准 UI 处理
```javascript
window.calibrateWavelengthUI = async function() {
    const result = await window.bridge.calibrateWavelength([520.0]);
    if (result.success) {
        showToast(`波长校准成功：校正值=${result.data.correction.toFixed(3)} cm⁻¹`, 'success');
        updateCalibrationStatus({
            wavelength: { calibrated: true, correction: result.data.correction }
        });
    }
};
```

#### 强度校准 UI 处理
```javascript
window.calibrateIntensityUI = async function() {
    const result = await window.bridge.calibrateIntensity(
        referenceSpectrum, theoreticalSpectrum
    );
    if (result.success) {
        showToast('强度校准成功', 'success');
        updateCalibrationStatus({ intensity: { calibrated: true } });
    }
};
```

#### 自动曝光控制
```javascript
window.toggleAutoExposure = async function() {
    const enabled = checkbox.checked;
    await window.bridge.setAutoExposureEnabled(enabled);
    // 更新 UI 状态
};

window.runAutoExposure = async function() {
    const result = await window.bridge.autoExposure(targetIntensity, 3);
    if (result.success) {
        showToast(`自动曝光成功：积分时间=${result.data.final_integration_time}ms`, 'success');
    }
};
```

---

### 5. UI 模块更新

**文件**: `frontend/js/ui.js`

**新增函数**:

```javascript
/**
 * 更新校准状态 UI
 * @param {Object} status - 校准状态对象
 */
export function updateCalibrationStatus(status) {
    // 更新波长校准状态
    if (status && status.wavelength) {
        wlStatusIndicator.className = status.wavelength.calibrated ? 'connected' : 'disconnected';
        wlStatusText.textContent = status.wavelength.calibrated 
            ? `已校准 (${status.wavelength.correction?.toFixed(3)} cm⁻¹)`
            : '未校准';
    }
    
    // 更新强度校准状态
    if (status && status.intensity) {
        intStatusIndicator.className = status.intensity.calibrated ? 'connected' : 'disconnected';
        intStatusText.textContent = status.intensity.calibrated ? '已校准' : '未校准';
    }
}
```

---

## 📁 修改的文件清单

| 文件 | 修改内容 | 行数变化 |
|------|----------|----------|
| `frontend/index.html` | 添加校准按钮、自动曝光开关、状态指示器 | +40 行 |
| `frontend/styles.css` | 开关控件、校准状态样式 | +95 行 |
| `frontend/js/bridge.js` | 添加 10 个 P0 功能桥接方法 | +125 行 |
| `frontend/js/main.js` | 添加 P0 功能全局函数 | +140 行 |
| `frontend/js/ui.js` | 添加校准状态更新函数 | +40 行 |

**总计**: +440 行

---

## 🎨 UI 效果

### 状态栏
```
┌─────────────────────────────────────────────────────────────┐
│ ● 设备：已连接  ● 采集：停止  ● 波长校准：未校准  ● 强度校准：未校准  FPS: 60 │
└─────────────────────────────────────────────────────────────┘
```

校准后：
```
┌─────────────────────────────────────────────────────────────┐
│ ● 设备：已连接  ● 采集：停止  ● 波长校准：已校准 (-0.5 cm⁻¹)  ● 强度校准：已校准  FPS: 60 │
└─────────────────────────────────────────────────────────────┘
```

### 控制面板
```
┌─────────────────────────────────────┐
│ 自动曝光：[●] 开                    │
│ ─────────────────────────────────   │
│ 目标强度：0.70                      │
│ [━━━━━━━━━●━━━━━━━━━] 0.5-0.8       │
│ [▶️ 执行自动曝光]                   │
│                                     │
│ [🔬 波长校准] [💡 强度校准]         │
│                                     │
│ 积分时间 (ms): 100 [____]           │
└─────────────────────────────────────┘
```

---

## 🔧 使用流程

### 波长校准
1. 点击"🔬 波长校准"按钮
2. 系统自动使用硅片 520 cm⁻¹ 作为参考
3. 校准成功后，状态栏显示"已校准 (校正值 cm⁻¹)"

### 强度校准
1. 采集一条光谱数据
2. 点击"💡 强度校准"按钮
3. 系统使用当前光谱和模拟理论值进行校准
4. 校准成功后，状态栏显示"已校准"

### 自动曝光
1. 点击自动曝光开关，启用自动曝光
2. 调节目标强度滑块（0.5-0.8）
3. 点击"▶️ 执行自动曝光"
4. 系统自动调节积分时间，显示最终结果

---

## 📝 技术要点

### 1. 开关控件样式
使用 CSS `:checked` 伪实现开关效果：
```css
input:checked + .slider {
    background-color: #00d9ff;
}
```

### 2. 状态指示器
复用现有状态指示器样式，通过 `connected`/`disconnected` 类切换：
```javascript
element.className = `status-indicator ${calibrated ? 'connected' : 'disconnected'}`;
```

### 3. 异步函数处理
所有后端调用都是同步的（Qt 桥接），但使用 async/await 保持代码一致性：
```javascript
window.calibrateWavelengthUI = async function() {
    const result = await window.bridge.calibrateWavelength([520.0]);
    // 处理结果
};
```

---

## 🎯 下一步工作

### 单元测试
```python
# test_p0_frontend.py
def test_wavelength_calibration_ui()
def test_intensity_calibration_ui()
def test_auto_exposure_ui()
```

### 改进建议

1. **强度校准文件导入**
   - 当前使用模拟数据
   - 应添加文件选择器导入标准光源谱图

2. **自动曝光实时反馈**
   - 添加迭代进度显示
   - 显示当前强度和积分时间

3. **校准状态持久化**
   - 刷新页面后保留校准状态
   - 使用 localStorage 或后端存储

---

*报告生成时间：2026-03-23*  
*下一阶段：P0 功能单元测试*
