# P0 功能实现报告 - 后端部分

**实现日期**: 2026-03-23  
**实现工程师**: P11 级全栈工程师  
**实现阶段**: 后端实现完成

---

## 📊 实现进度

| 功能 | 后端 | 前端 UI | 测试 | 完成度 |
|------|------|--------|------|--------|
| 波长校准 | ✅ 完成 | ⏳ 待实现 | ⏳ 待编写 | 40% |
| 强度校准 | ✅ 完成 | ⏳ 待实现 | ⏳ 待编写 | 40% |
| 自动曝光 | ✅ 完成 | ⏳ 待实现 | ⏳ 待编写 | 40% |

---

## ✅ 已完成的实现

### 1. 波长校准模块

**文件**: `backend/algorithms/wavelength_calibration.py`

**核心类**:
- `WavelengthCalibrator` - 波长校准器
- `WavelengthCalibrationResult` - 校准结果数据类

**主要方法**:
```python
def calibrate(
    reference_peaks: List[float],
    expected_positions: Optional[List[float]] = None,
    tolerance: Optional[float] = None
) -> ApiResponse

def find_peak_position(
    spectrum: np.ndarray,
    wavenumbers: np.ndarray,
    expected_position: float,
    search_range: float = 20.0
) -> Optional[float]

def apply_correction(wavenumbers: np.ndarray) -> np.ndarray
def get_status() -> ApiResponse
```

**特性**:
- ✅ 支持单点/多点校准
- ✅ 使用硅片 520 cm⁻¹ 作为默认参考
- ✅ 容忍度验证（默认 5 cm⁻¹）
- ✅ 拟合优度（R²）计算
- ✅ 统一的 ApiResponse 返回格式
- ✅ 日志格式规范

---

### 2. 强度校准模块

**文件**: `backend/algorithms/intensity_calibration.py`

**核心类**:
- `IntensityCalibrator` - 强度校准器
- `IntensityCalibrationResult` - 校准结果数据类

**主要方法**:
```python
def calibrate(
    reference_spectrum: np.ndarray,
    theoretical_spectrum: np.ndarray,
    wavenumbers: np.ndarray
) -> ApiResponse

def apply_correction(spectrum: np.ndarray) -> ApiResponse
def get_status() -> ApiResponse
def load_correction_curve(...) -> ApiResponse
```

**特性**:
- ✅ 使用标准光源谱图计算校正曲线
- ✅ 维度验证
- ✅ 数据有效性检查
- ✅ 校正曲线归一化
- ✅ 统一的 ApiResponse 返回格式
- ✅ 日志格式规范

---

### 3. 自动曝光模块

**文件**: `backend/algorithms/auto_exposure.py`

**核心类**:
- `AutoExposure` - 自动曝光控制器

**主要方法**:
```python
def execute(
    acquire_spectrum: Callable[[int], np.ndarray],
    current_integration_time: int,
    max_iterations: Optional[int] = None
) -> ApiResponse

def set_target_intensity(intensity: float) -> ApiResponse
def get_status() -> ApiResponse
```

**特性**:
- ✅ 二分查找算法
- ✅ 最大迭代次数可配置（默认 3 次）
- ✅ 目标强度范围验证（0.5-0.8）
- ✅ 收敛条件（目标强度 ±10%）
- ✅ 详细的迭代日志
- ✅ 统一的 ApiResponse 返回格式

---

### 4. 状态管理

**文件**: `backend/state_manager.py`

**新增类**:
- `CalibrationState` - 校准状态数据类
- `CalibrationStateManager` - 校准状态管理器

**特性**:
- ✅ 波长校准状态管理
- ✅ 强度校准状态管理
- ✅ 自动曝光启用状态管理
- ✅ 校正值/校正曲线存储

---

### 5. 后端接口

**文件**: `main.py` (BridgeObject 类)

**新增接口方法**:

#### 波长校准接口
```python
@Slot(str, result=str)
def calibrateWavelength(reference_peaks_json: str) -> str

@Slot(result=str)
def getWavelengthCorrection() -> str

@Slot(result=str)
def isWavelengthCalibrated() -> str
```

#### 强度校准接口
```python
@Slot(str, str, result=str)
def calibrateIntensity(reference_spectrum_json: str, theoretical_spectrum_json: str) -> str

@Slot(result=str)
def getIntensityCorrection() -> str
```

#### 自动曝光接口
```python
@Slot(float, int, result=str)
def autoExposure(target_intensity: float = 0.7, max_iterations: int = 3) -> str

@Slot(bool)
def setAutoExposureEnabled(enabled: bool)

@Slot(result=str)
def isAutoExposureEnabled() -> str
```

#### 综合状态
```python
@Slot(result=str)
def getCalibrationStatus() -> str
```

---

## 📁 修改的文件清单

| 文件 | 修改内容 | 行数变化 |
|------|----------|----------|
| `backend/algorithms/wavelength_calibration.py` | 新建波长校准模块 | +280 行 |
| `backend/algorithms/intensity_calibration.py` | 新建强度校准模块 | +320 行 |
| `backend/algorithms/auto_exposure.py` | 新建自动曝光模块 | +260 行 |
| `backend/algorithms/__init__.py` | 导出新模块 | +15 行 |
| `backend/state_manager.py` | 添加校准状态管理 | +80 行 |
| `main.py` | 添加 P0 功能接口 | +220 行 |
| `backend/error_handler.py` | 添加日志格式类 | +100 行 |

**总计**: +1275 行

---

## 🔧 使用示例

### 波长校准

```python
from backend.algorithms import WavelengthCalibrator

calibrator = WavelengthCalibrator()

# 单点校准（使用默认硅片 520 cm⁻¹）
result = calibrator.calibrate(reference_peaks=[520.5])
print(result.to_dict())
# {'success': True, 'correction': -0.5, 'r_squared': 1.0, ...}

# 多点校准
result = calibrator.calibrate(
    reference_peaks=[520.5, 1332.2],
    expected_positions=[520.0, 1332.0]
)

# 应用校正
wavenumbers = np.array([...])
corrected = calibrator.apply_correction(wavenumbers)
```

### 强度校准

```python
from backend.algorithms import IntensityCalibrator

calibrator = IntensityCalibrator()

# 执行校准
result = calibrator.calibrate(
    reference_spectrum=measured_spectrum,
    theoretical_spectrum=standard_spectrum,
    wavenumbers=wavenumbers
)

# 应用校正
result = calibrator.apply_correction(spectrum)
```

### 自动曝光

```python
from backend.algorithms import AutoExposure

auto_exp = AutoExposure(target_intensity=0.7)

# 执行自动曝光
result = auto_exp.execute(
    acquire_spectrum=driver.acquire,  # 采集函数
    current_integration_time=100,
    max_iterations=3
)

if result.success:
    print(f"最终积分时间：{result.data['final_integration_time']}ms")
else:
    print(f"超时：{result.message}")
```

---

## 🎯 下一步工作

### 前端 UI 实现

1. **波长校准 UI**
   - 添加"波长校准"按钮
   - 显示校准状态指示器
   - 显示校正值和校准时间

2. **强度校准 UI**
   - 添加"强度校准"按钮
   - 文件选择器（导入标准光源谱图）
   - 显示校正曲线图表

3. **自动曝光 UI**
   - 添加"自动曝光"开关
   - 目标强度滑块
   - 显示"调节中..."动画

### 单元测试

```python
# test_wavelength_calibration.py
def test_wavelength_calibration_success()
def test_wavelength_calibration_invalid_input()
def test_wavelength_calibration_large_error()

# test_intensity_calibration.py
def test_intensity_calibration_success()
def test_intensity_calibration_invalid_spectrum()
def test_intensity_calibration_dimension_mismatch()

# test_auto_exposure.py
def test_auto_exposure_success()
def test_auto_exposure_invalid_target()
def test_auto_exposure_timeout()
```

---

## 📝 技术要点

### 1. 统一返回格式

所有方法都返回 `ApiResponse` 对象：

```python
@dataclass
class ApiResponse:
    success: bool
    error_code: Optional[int]
    message: str
    data: Optional[Dict[str, Any]]
    timestamp: float
```

### 2. 日志格式规范

使用统一的日志格式类：

```python
log.info(CalibrationLog.wavelength_calibration_success(correction))
log.error(CalibrationLog.wavelength_calibration_failed(error_msg, code))
log.debug(AutoExposureLog.exposure_adjustment(current, new, intensity))
```

### 3. 错误码分组

```python
# 校准相关错误 (250-279)
CALIBRATION_FAILED = 250
CALIBRATION_TIMEOUT = 251
REFERENCE_PEAK_NOT_FOUND = 252
CALIBRATION_DATA_INVALID = 253

WAVELENGTH_CALIBRATION_ERROR = 255
INTENSITY_CALIBRATION_ERROR = 260
AUTO_EXPOSURE_TIMEOUT = 265
```

---

*报告生成时间：2026-03-23*  
*下一阶段：前端 UI 实现 + 单元测试*
